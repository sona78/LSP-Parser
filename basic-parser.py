import asyncio
import json
import os
import sys
import signal
from multilspy import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from files import GRAPH_JSON_FILE

class TimeoutError(Exception):
    """Custom timeout exception for Windows compatibility."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")

async def build_code_graph_with_multilspy():
    """Build code graph using multilspy with comprehensive error handling."""
    print("Building code graph with multilspy...")
    
    # Configure multilspy
    config = MultilspyConfig(code_language="python")
    repository_root_path = os.path.abspath("test-project")
    config.root_uri = f"file:///{repository_root_path.replace(os.sep, '/')}"
    config.language_id = "python"
    config.trace_lsp_communication = False

    # Create logger
    logger = MultilspyLogger()

    print(f"Repository root path: {repository_root_path}")
    print("Creating language server...")
    
    # Create the language server
    lsp = LanguageServer.create(config, logger, repository_root_path)
    print(f"Language server created: {type(lsp).__name__}")

    graph = {"nodes": [], "edges": []}
    all_functions = []
    
    print("Starting language server...")
    async with lsp.start_server():
        print("Language server started successfully!")
        
        # Find all Python files in the workspace
        python_files = []
        for root, dirs, files in os.walk(repository_root_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    python_files.append(os.path.join(root, file))
        
        print(f"Found Python files: {[os.path.relpath(f, repository_root_path) for f in python_files]}")

        # === STEP A: GET ALL FUNCTIONS (NODES) ===
        print("\nFinding all functions using multilspy...")
        
        for file_path in python_files:
            relative_path = os.path.relpath(file_path, repository_root_path)
            print(f"Processing file: {relative_path}")
            
            # Open the file in the language server
            with lsp.open_file(relative_path):
                # Get document symbols with timeout
                symbols_result = await lsp.request_document_symbols(relative_path)

                (symbols, tree_repr) = symbols_result
                
                if not symbols:
                    print(f"  No symbols found in {relative_path}")
                    continue
                
                print(f"  Found {len(symbols)} symbols")
                
                for sym in symbols:
                    # Check for functions (kind 12 is Function)
                    print(f"sym {sym}")
                    if sym['kind'] == 12:
                        func_info = {
                            "name": sym['name'],
                            "kind": "FUNCTION",
                            "file_path": file_path,
                            "line": sym['range']['start']['line'] + 1,
                            "file": os.path.basename(file_path),
                            "range": sym
                        }
                        all_functions.append(func_info)
                        
                        node_id = f"{sym['name']}::{os.path.basename(file_path)}"
                        graph["nodes"].append({
                            "id": node_id,
                            "name": sym['name'],
                            "kind": "FUNCTION",
                            "file": os.path.basename(file_path),
                            "line": sym['range']['start']['line'] + 1,
                        })                        

        print(f"\nFound {len(graph['nodes'])} functions (nodes).")

        # === STEP B: FIND FUNCTION CALLS (EDGES) ===
        print("\nFinding function calls using multilspy...")

        # For each function, find references to it
        for i, func in enumerate(all_functions):
            relative_path = os.path.relpath(func["file_path"], repository_root_path)
            print(f"[{i+1}/{len(all_functions)}] Finding references for {func['name']} in {relative_path}")
            
            # Find references with timeout - use selectionRange for better accuracy
            line = func["range"]["selectionRange"]["start"]["line"]
            char = func["range"]["selectionRange"]["start"]["character"]
            print(f"Looking for references at {relative_path}:{line}:{char}")
            
            try:
                refs_result = await lsp.request_references(relative_path, line, char)
            except Exception as e:
                print(f"    Error getting references: {e}")
                continue
            
            if not refs_result:
                print(f"    No references found")
                continue
            
            print(f"    Found {len(refs_result)} references")
            
            for ref in refs_result:
                # Build absolute path for reference
                print(f"ref: {ref}")
                ref_path = os.path.normpath(os.path.join(repository_root_path, ref["relativePath"]))
                ref_line = ref["range"]["start"]["line"]
                
                # Find which function contains this reference
                caller_func = None
                for f in all_functions:
                    if os.path.normpath(f["file_path"]) == ref_path:
                        start_line = f["range"]["range"]["start"]["line"]
                        end_line = f["range"]["range"]["end"]["line"]
                        if start_line <= ref_line <= end_line:
                            caller_func = f
                            break
                
                # Add edge if we found a valid caller that's different from the callee
                if caller_func and caller_func["name"] != func["name"]:
                    caller_id = f"{caller_func['name']}::{caller_func['file']}"
                    callee_id = f"{func['name']}::{func['file']}"
                    edge = {"from": caller_id, "to": callee_id}
                    
                    if edge not in graph["edges"]:
                        graph["edges"].append(edge)
                        print(f"      Edge: {caller_func['name']} -> {func['name']}")

        print(f"\nFound {len(graph['edges'])} function calls (edges).")
        
        # Print and save results
        print("\n--- GRAPH FOUNDATION (JSON) ---")
        print(json.dumps(graph, indent=2))

        with open(GRAPH_JSON_FILE, 'w') as f:
            json.dump(graph, f, indent=2)
        print(f"\nGraph data saved to {GRAPH_JSON_FILE}")
        
        return graph

async def main():
    """Main entry point with platform-specific timeout handling."""
    print("Starting multilspy-based code graph builder...")
    
    # Set up timeout handling
    if os.name == 'posix':  # Unix/Linux/Mac
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(180)  # 3 minute timeout
    
    if os.name == 'posix':
        # Unix/Linux/Mac with signal-based timeout
        result = await build_code_graph_with_multilspy()
        signal.alarm(0)  # Cancel timeout
        return result
    else:
        # Windows with asyncio timeout
        return await asyncio.wait_for(
            build_code_graph_with_multilspy(),
            timeout=30.0  # Shorter timeout for Windows due to hanging issues
        )

if __name__ == "__main__":
    result = asyncio.run(main())
    if result:
        print("Successfully completed code graph generation using multilspy!")
    else:
        print("Code graph generation failed - consider using AST-based approach as fallback")
        sys.exit(1)