import asyncio
import json
import os
import sys
import signal
from multilspy import LanguageServer
from multilspy.multilspy_config import MultilspyConfig
from multilspy.multilspy_logger import MultilspyLogger
from files import GRAPH_JSON_FILE, CALL_GRAPH_JSON_FILE, DECLARATION_GRAPH_JSON_FILE

# Store the original working directory for LSP server
original_working_directory = os.getcwd()
repository_root_path = os.path.abspath("test-project")

class TimeoutError(Exception):
    """Custom timeout exception for Windows compatibility."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")

def find_python_files(root_path):
    """Find all Python files in the given repository root."""
    python_files = []
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                python_files.append(os.path.join(root, file))
    return python_files

def setup_lsp(root_path):
    """Set up and return a Multilspy LanguageServer instance."""
    config = MultilspyConfig(code_language="python")
    config.root_uri = f"file:///{root_path.replace(os.sep, '/')}"
    config.language_id = "python"
    config.trace_lsp_communication = False

    logger = MultilspyLogger()

    print(f"Repository root path: {root_path}")
    print(f"Original working directory: {original_working_directory}")
    print("Creating language server...")
    
    # Use absolute path to jedi-language-server to avoid PATH issues
    import shutil
    jedi_path = shutil.which("jedi-language-server")
    if jedi_path:
        print(f"Found jedi-language-server at: {jedi_path}")
        # Temporarily monkey-patch the command to use absolute path
        from multilspy.language_servers.jedi_language_server import jedi_server
        original_init = jedi_server.JediServer.__init__
        
        def patched_init(self, config, logger, repository_root_path):
            from multilspy.lsp_protocol_handler.server import ProcessLaunchInfo
            from multilspy.language_server import LanguageServer as BaseLS
            BaseLS.__init__(self, config, logger, repository_root_path, 
                          ProcessLaunchInfo(cmd=jedi_path, cwd=original_working_directory), "python")
        
        jedi_server.JediServer.__init__ = patched_init
        result = LanguageServer.create(config, logger, root_path)
        jedi_server.JediServer.__init__ = original_init  # Restore original
        return result
    else:
        print("Warning: jedi-language-server not found in PATH")
        return LanguageServer.create(config, logger, root_path)

async def get_functions_from_file(lsp, file_path, root_path):
    """Extract all function, method, class, property, and import symbols from a file using multilspy."""
    relative_path = os.path.relpath(file_path, root_path)
    print(f"Processing file: {relative_path}")
    all_functions = []
    nodes = []
    all_classes = []
    all_methods = []
    all_properties = []
    all_imports = []
    method_class_edges = []
    property_class_edges = []
    import_file_edges = []
    with lsp.open_file(relative_path):
        symbols, tree_repr = await lsp.request_document_symbols(relative_path)
        print(f"Tree Repr: {tree_repr}")

        if not symbols:
            print(f"  No symbols found in {relative_path}")
            return all_functions, nodes, all_classes, all_methods, all_properties, all_imports, method_class_edges, property_class_edges, import_file_edges

        print(f"  Found {len(symbols)} symbols")

        def process_symbol(sym, parent_class=None):
            print(f"sym {sym}")
            # Class (kind 5)
            if sym['kind'] == 5:
                class_info = {
                    "name": sym['name'],
                    "kind": "CLASS",
                    "file_path": file_path,
                    "line": sym['range']['start']['line'] + 1,
                    "file": os.path.basename(file_path),
                    "range": sym
                }
                all_classes.append(class_info)
                node_id = f"{sym['name']}::{os.path.basename(file_path)}"
                nodes.append({
                    "id": node_id,
                    "name": sym['name'],
                    "kind": "CLASS",
                    "file": os.path.basename(file_path),
                    "line": sym['range']['start']['line'] + 1,
                })
                # Process children (e.g., methods, properties)
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=sym['name'])
            # Module/Import (kind 2)
            elif sym['kind'] == 2:
                import_info = {
                    "name": sym['name'],
                    "kind": "IMPORT",
                    "file_path": file_path,
                    "line": sym['range']['start']['line'] + 1,
                    "file": os.path.basename(file_path),
                    "range": sym
                }
                all_imports.append(import_info)
                node_id = f"{sym['name']}::{os.path.basename(file_path)}"
                nodes.append({
                    "id": node_id,
                    "name": sym['name'],
                    "kind": "IMPORT",
                    "file": os.path.basename(file_path),
                    "line": sym['range']['start']['line'] + 1,
                })
                # Note: Imports are contained within files (as clusters), not linked as edges
                # Process children if any
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=parent_class)
            # Method (kind 6)
            elif sym['kind'] == 6:
                method_info = {
                    "name": sym['name'],
                    "kind": "METHOD",
                    "file_path": file_path,
                    "line": sym['range']['start']['line'] + 1,
                    "file": os.path.basename(file_path),
                    "range": sym,
                    "parent_class": parent_class
                }
                all_methods.append(method_info)
                node_id = f"{sym['name']}::{os.path.basename(file_path)}"
                nodes.append({
                    "id": node_id,
                    "name": sym['name'],
                    "kind": "METHOD",
                    "file": os.path.basename(file_path),
                    "line": sym['range']['start']['line'] + 1,
                })
                # Link method to its class if parent_class is known
                if parent_class:
                    class_id = f"{parent_class}::{os.path.basename(file_path)}"
                    edge = {"from": class_id, "to": node_id}
                    method_class_edges.append(edge)
                    print(f"      Method-Class Edge: {class_id} -> {node_id}")
                # Process children (e.g., inner functions)
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=parent_class)
            # Property (kind 7)
            elif sym['kind'] == 7:
                property_info = {
                    "name": sym['name'],
                    "kind": "PROPERTY",
                    "file_path": file_path,
                    "line": sym['range']['start']['line'] + 1,
                    "file": os.path.basename(file_path),
                    "range": sym,
                    "parent_class": parent_class
                }
                all_properties.append(property_info)
                node_id = f"{sym['name']}::{os.path.basename(file_path)}"
                nodes.append({
                    "id": node_id,
                    "name": sym['name'],
                    "kind": "PROPERTY",
                    "file": os.path.basename(file_path),
                    "line": sym['range']['start']['line'] + 1,
                })
                # Link property to its class if parent_class is known
                if parent_class:
                    class_id = f"{parent_class}::{os.path.basename(file_path)}"
                    edge = {"from": class_id, "to": node_id}
                    property_class_edges.append(edge)
                    print(f"      Property-Class Edge: {class_id} -> {node_id}")
                # Process children (e.g., inner functions)
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=parent_class)
            # Function (kind 12)
            elif sym['kind'] == 12:
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
                nodes.append({
                    "id": node_id,
                    "name": sym['name'],
                    "kind": "FUNCTION",
                    "file": os.path.basename(file_path),
                    "line": sym['range']['start']['line'] + 1,
                })
                # Process children (e.g., inner functions)
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=parent_class)
            else:
                # Other symbol kinds, process children if any
                if "children" in sym and sym["children"]:
                    for child in sym["children"]:
                        process_symbol(child, parent_class=parent_class)

        for sym in symbols:
            process_symbol(sym)

        # Since LSP doesn't provide nested structure, we need to determine 
        # class-method/property relationships based on source ranges
        for method in all_methods:
            for class_info in all_classes:
                # Check if method is within class range
                if (os.path.normpath(method["file_path"]) == os.path.normpath(class_info["file_path"]) and
                    class_info["range"]["range"]["start"]["line"] <= method["range"]["range"]["start"]["line"] <= 
                    class_info["range"]["range"]["end"]["line"]):
                    # Create class-to-method edge
                    class_id = f"{class_info['name']}::{class_info['file']}"
                    method_id = f"{method['name']}::{method['file']}"
                    edge = {"from": class_id, "to": method_id}
                    if edge not in method_class_edges:
                        method_class_edges.append(edge)
                        print(f"      Method-Class Edge: {class_id} -> {method_id}")
                    break  # Found the containing class, no need to check others

        for prop in all_properties:
            for class_info in all_classes:
                # Check if property is within class range
                if (os.path.normpath(prop["file_path"]) == os.path.normpath(class_info["file_path"]) and
                    class_info["range"]["range"]["start"]["line"] <= prop["range"]["range"]["start"]["line"] <= 
                    class_info["range"]["range"]["end"]["line"]):
                    # Create class-to-property edge
                    class_id = f"{class_info['name']}::{class_info['file']}"
                    prop_id = f"{prop['name']}::{prop['file']}"
                    edge = {"from": class_id, "to": prop_id}
                    if edge not in property_class_edges:
                        property_class_edges.append(edge)
                        print(f"      Property-Class Edge: {class_id} -> {prop_id}")
                    break  # Found the containing class, no need to check others

    return all_functions, nodes, all_classes, all_methods, all_properties, all_imports, method_class_edges, property_class_edges, import_file_edges

def find_caller_function(all_functions, ref_path, ref_line):
    """Find the function in all_functions that contains the reference line."""
    for f in all_functions:
        if os.path.normpath(f["file_path"]) == ref_path:
            start_line = f["range"]["range"]["start"]["line"]
            end_line = f["range"]["range"]["end"]["line"]
            if start_line <= ref_line <= end_line:
                return f
    return None

def find_caller_method(all_methods, ref_path, ref_line):
    """Find the method in all_methods that contains the reference line."""
    for m in all_methods:
        if os.path.normpath(m["file_path"]) == ref_path:
            start_line = m["range"]["range"]["start"]["line"]
            end_line = m["range"]["range"]["end"]["line"]
            if start_line <= ref_line <= end_line:
                return m
    return None

def find_caller_property(all_properties, ref_path, ref_line):
    """Find the property in all_properties that contains the reference line."""
    for p in all_properties:
        if os.path.normpath(p["file_path"]) == ref_path:
            start_line = p["range"]["range"]["start"]["line"]
            end_line = p["range"]["range"]["end"]["line"]
            if start_line <= ref_line <= end_line:
                return p
    return None

def find_caller_class(all_classes, ref_path, ref_line):
    """Find the class in all_classes that contains the reference line."""
    for c in all_classes:
        if os.path.normpath(c["file_path"]) == ref_path:
            start_line = c["range"]["range"]["start"]["line"]
            end_line = c["range"]["range"]["end"]["line"]
            if start_line <= ref_line <= end_line:
                return c
    return None

async def find_function_edges(lsp, all_functions, all_classes, all_methods, all_properties, all_imports, root_path):
    """Find all function/method/property/import call edges using multilspy."""
    edges = []
    # Combine functions, methods, properties, and imports for callee search
    all_callees = all_functions + all_methods + all_properties + all_imports
    for i, func in enumerate(all_callees):
        relative_path = os.path.relpath(func["file_path"], root_path)
        print(f"[{i+1}/{len(all_callees)}] Finding references for {func['name']} in {relative_path}")

        # For methods/properties/functions, use their range
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
            print(f"ref: {ref}")
            ref_path = os.path.normpath(os.path.join(root_path, ref["relativePath"]))
            ref_line = ref["range"]["start"]["line"]

            caller_func = find_caller_function(all_functions, ref_path, ref_line)
            caller_method = find_caller_method(all_methods, ref_path, ref_line)
            caller_property = find_caller_property(all_properties, ref_path, ref_line)
            caller_class = find_caller_class(all_classes, ref_path, ref_line)

            callee_id = f"{func['name']}::{func['file']}"

            if caller_func and caller_func["name"] != func["name"]:
                caller_id = f"{caller_func['name']}::{caller_func['file']}"
                edge = {"from": caller_id, "to": callee_id}
                if edge not in edges:
                    edges.append(edge)
                    print(f"      Edge: {caller_func['name']} -> {func['name']}")
            elif caller_method and caller_method["name"] != func["name"]:
                caller_id = f"{caller_method['name']}::{caller_method['file']}"
                edge = {"from": caller_id, "to": callee_id}
                if edge not in edges:
                    edges.append(edge)
                    print(f"      Edge: {caller_method['name']} -> {func['name']}")
            elif caller_property and caller_property["name"] != func["name"]:
                caller_id = f"{caller_property['name']}::{caller_property['file']}"
                edge = {"from": caller_id, "to": callee_id}
                if edge not in edges:
                    edges.append(edge)
                    print(f"      Edge: {caller_property['name']} -> {func['name']}")
            # Remove class-to-method/function/property edges as classes don't call directly
    return edges

def save_graph(graph, file_path, graph_type="Graph"):
    """Save the graph as JSON to the specified file."""
    print(f"\n--- {graph_type.upper()} FOUNDATION (JSON) ---")
    print(json.dumps(graph, indent=2))
    with open(file_path, 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"\n{graph_type} data saved to {file_path}")

def reclassify_isolated_classes_as_imports(nodes, call_edges, declaration_edges):
    """Reclassify classes that have no edges (neither call nor declaration) as imports."""
    print("\nReclassifying isolated classes as imports...")
    
    # Get all edge node IDs
    edge_node_ids = set()
    for edge in call_edges + declaration_edges:
        edge_node_ids.add(edge["from"])
        edge_node_ids.add(edge["to"])
    
    # Find classes with no edges and reclassify them as imports
    reclassified_count = 0
    for node in nodes:
        if node["kind"] == "CLASS" and node["id"] not in edge_node_ids:
            print(f"  Reclassifying {node['name']} from CLASS to IMPORT")
            node["kind"] = "IMPORT"
            reclassified_count += 1
    
    print(f"Reclassified {reclassified_count} isolated classes as imports.")
    return nodes

def create_call_graph(nodes, call_edges):
    """Create call graph containing only function/method/property call relationships."""
    return {
        "nodes": nodes,
        "edges": call_edges
    }

def create_declaration_graph(nodes, method_class_edges, property_class_edges, import_file_edges):
    """Create declaration graph showing class-method/property relationships only.
    Files are represented as visual containers (clusters), not as nodes."""
    # Declaration graph contains only structural relationships, not file-level relationships
    return {
        "nodes": nodes,
        "edges": method_class_edges + property_class_edges
    }

async def build_code_graph_with_multilspy():
    """Build code graph using multilspy with comprehensive error handling."""
    print("Building code graph with multilspy...")
    print(f"Repository root path: {repository_root_path}")
    print(f"Original working directory: {original_working_directory}")

    # Ensure we're in the original working directory for LSP server startup
    current_dir = os.getcwd()
    if current_dir != original_working_directory:
        print(f"Changing back to original directory: {original_working_directory}")
        os.chdir(original_working_directory)

    lsp = setup_lsp(repository_root_path)
    print(f"Language server created: {type(lsp).__name__}")

    graph = {"nodes": [], "edges": []}
    all_functions = []
    all_classes = []
    all_methods = []
    all_properties = []
    all_imports = []
    method_class_edges = []
    property_class_edges = []
    import_file_edges = []

    print("Starting language server...")
    async with lsp.start_server():
        print("Language server started successfully!")

        python_files = find_python_files(repository_root_path)
        print(f"Found Python files: {[os.path.relpath(f, repository_root_path) for f in python_files]}")

        # STEP A: Get all functions, methods, classes, properties, and imports (nodes)
        print("\nFinding all functions, methods, classes, properties, and imports using multilspy...")
        for file_path in python_files:
            funcs, nodes, classes, methods, properties, imports, mclass_edges, pclass_edges, ifile_edges = await get_functions_from_file(
                lsp, file_path, repository_root_path
            )
            all_functions.extend(funcs)
            all_classes.extend(classes)
            all_methods.extend(methods)
            all_properties.extend(properties)
            all_imports.extend(imports)
            method_class_edges.extend(mclass_edges)
            property_class_edges.extend(pclass_edges)
            import_file_edges.extend(ifile_edges)
            graph["nodes"].extend(nodes)
        print(f"\nFound {len(graph['nodes'])} nodes (functions, methods, classes, properties, and imports).")

        # STEP B: Find function/method/property/import calls (edges)
        print("\nFinding function, method, property, and import calls using multilspy...")
        call_edges = await find_function_edges(
            lsp, all_functions, all_classes, all_methods, all_properties, all_imports, repository_root_path
        )
        print(f"\nFound {len(call_edges)} call edges and {len(method_class_edges) + len(property_class_edges)} declaration edges.")
        
        # Reclassify isolated classes as imports
        graph["nodes"] = reclassify_isolated_classes_as_imports(
            graph["nodes"], call_edges, method_class_edges + property_class_edges
        )
        
        # Create separate graphs
        call_graph = create_call_graph(graph["nodes"], call_edges)
        declaration_graph = create_declaration_graph(graph["nodes"], method_class_edges, property_class_edges, import_file_edges)
        
        # Save separate graphs
        save_graph(call_graph, CALL_GRAPH_JSON_FILE, "Call Graph")
        save_graph(declaration_graph, DECLARATION_GRAPH_JSON_FILE, "Declaration Graph")
        
        # Keep combined graph for backward compatibility
        graph["edges"] = call_edges + method_class_edges + property_class_edges
        save_graph(graph, GRAPH_JSON_FILE, "Combined Graph")
        
        return {"combined": graph, "call": call_graph, "declaration": declaration_graph}

def run_parser_on_directory(directory_path: str) -> bool:
    """
    Run the parser on a given directory and generate graph artifacts.
    
    Args:
        directory_path: Path to the directory containing Python files
        
    Returns:
        True if parsing succeeded, False otherwise
    """
    global repository_root_path
    
    # Update the repository path
    old_path = repository_root_path
    repository_root_path = os.path.abspath(directory_path)
    
    try:
        print(f"Running parser on directory: {repository_root_path}")
        result = asyncio.run(main())
        return result
    finally:
        # Restore original path
        repository_root_path = old_path

def get_parser_config():
    """Get the current parser configuration."""
    return {
        'repository_root_path': repository_root_path,
        'original_working_directory': original_working_directory
    }

def setup_parser_for_directory(directory_path: str):
    """
    Set up parser configuration for a specific directory.
    
    Args:
        directory_path: Path to the directory to analyze
    """
    global repository_root_path
    repository_root_path = os.path.abspath(directory_path)

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