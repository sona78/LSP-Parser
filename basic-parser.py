import asyncio
import json
import os
import pathlib
import tempfile
import logging
from multilspy import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger

# Optional: Configure logging to see LSP messages
# logging.basicConfig(level=logging.INFO)
# multilspy_config.trace_lsp_communication = True

def find_containing_function(
    location: dict, functions: list
) -> dict | None:
    """Find which function a given location (e.g., a reference) is inside."""
    for func_symbol in functions:
        # Check if the file URIs match
        if func_symbol["file_path"] != location.file_path:
            continue

        # Check if the reference's line is within the function's start and end lines
        ref_line = location.range.start.line
        func_start_line = func_symbol["range"]["start"]["line"]
        func_end_line = func_symbol["range"]["end"]["line"]

        if func_start_line <= ref_line <= func_end_line:
            return func_symbol
    return None


def main():
    """
    Creates a simple code graph by parsing Python files directly.
    """
    print("Creating code graph using direct file parsing...")
    
    # Build the factual graph foundation
    graph = {"nodes": [], "edges": []}
    
    # === STEP A: GET ALL FUNCTIONS (NODES) ===
    print("Finding all functions in the workspace...")
    import glob
    import ast
    import re
    
    python_files = glob.glob("test-project/*.py")
    print(f"Found Python files: {python_files}")
    
    all_functions = []
    
    # Parse each Python file to find functions
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "kind": "FUNCTION",
                        "file_path": file_path,
                        "line": node.lineno,
                        "file": os.path.basename(file_path)
                    }
                    all_functions.append(func_info)
                    
                    node_id = f"{node.name}::{os.path.basename(file_path)}"
                    graph["nodes"].append({
                        "id": node_id,
                        "name": node.name,
                        "kind": "FUNCTION",
                        "file": os.path.basename(file_path),
                        "line": node.lineno,
                    })
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            # Fallback to simple regex parsing
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith('def '):
                            func_name = re.match(r'def\s+(\w+)', line.strip())
                            if func_name:
                                func_name = func_name.group(1)
                                func_info = {
                                    "name": func_name,
                                    "kind": "FUNCTION", 
                                    "file_path": file_path,
                                    "line": i,
                                    "file": os.path.basename(file_path)
                                }
                                all_functions.append(func_info)
                                
                                node_id = f"{func_name}::{os.path.basename(file_path)}"
                                graph["nodes"].append({
                                    "id": node_id,
                                    "name": func_name,
                                    "kind": "FUNCTION",
                                    "file": os.path.basename(file_path),
                                    "line": i,
                                })
            except Exception as e2:
                print(f"Error with fallback parsing for {file_path}: {e2}")
    
    print(f"Found {len(graph['nodes'])} functions (nodes).")
    
    # === STEP B: FIND FUNCTION CALLS (EDGES) ===
    print("\nFinding function calls to build call graph (edges)...")
    
    # Simple approach: look for function calls in each file
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find which functions are defined in this file
            file_functions = [f for f in all_functions if f['file_path'] == file_path]
            
            # Look for calls to other functions
            for target_func in all_functions:
                # Simple regex to find function calls
                call_pattern = rf'\b{target_func["name"]}\s*\('
                if re.search(call_pattern, content):
                    # This file calls the target function
                    # Now determine which function in this file makes the call
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if re.search(call_pattern, line):
                            # Find which function this line belongs to
                            caller_func = None
                            for func in file_functions:
                                # Simple heuristic: if the call is after the function definition
                                if func['line'] <= line_num:
                                    caller_func = func
                            
                            if caller_func and caller_func['name'] != target_func['name']:
                                caller_id = f"{caller_func['name']}::{caller_func['file']}"
                                callee_id = f"{target_func['name']}::{target_func['file']}"
                                edge = {"from": caller_id, "to": callee_id}
                                
                                # Avoid duplicate edges
                                if edge not in graph["edges"]:
                                    graph["edges"].append(edge)
                            
        except Exception as e:
            print(f"Error analyzing calls in {file_path}: {e}")
    
    print(f"Found {len(graph['edges'])} function calls (edges).")
    
    # Print the final graph
    print("\n---  GRAPH FOUNDATION (JSON) ---")
    print(json.dumps(graph, indent=2))
    
    # Save the graph to a JSON file for visualization
    with open('./artifacts/graph_data.json', 'w') as f:
        json.dump(graph, f, indent=2)
    print("\nGraph data saved to graph_data.json")


if __name__ == "__main__":
    main()