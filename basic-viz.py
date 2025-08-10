#!/usr/bin/env python3
"""
Graph Visualization Tool
Creates visual representations of the code graph using multiple methods.
"""

import json
import os
from files import GRAPH_JSON_FILE, GRAPH_DOT_FILE, GRAPH_IMAGE_FILE, GRAPH_PNG_FILE, GRAPH_SVG_FILE, GRAPH_PDF_FILE, GRAPH_MATPLOTLIB_PNG_FILE, CALL_GRAPH_JSON_FILE, DECLARATION_GRAPH_JSON_FILE
import graphviz
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def load_graph_data(filename=GRAPH_JSON_FILE):
    """Load graph data from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run basic-parser.py first to generate the graph data.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error reading {filename}: {e}")
        return None


def create_visualization(graph_data, output_format='png', engine='dot'):
    """
    Create a visual representation of the code graph.
    
    Args:
        graph_data: Dictionary containing nodes and edges
        output_format: Output format (png, pdf, svg, etc.)
        engine: Graphviz layout engine (dot, neato, fdp, sfdp, circo, twopi)
    """
    if not graph_data:
        return None

    # Create a new directed graph
    dot = graphviz.Digraph(comment='Code Call Graph', engine=engine)
    dot.attr(rankdir='TB')  # Top to bottom layout
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
    dot.attr('edge', color='darkblue', arrowhead='vee')

    # Group nodes by file for better visualization
    file_groups = {}
    for node in graph_data['nodes']:
        file_name = node['file']
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(node)

    # Color scheme for different files
    file_colors = {
        'main.py': 'lightcoral',
        'operations.py': 'lightgreen', 
        'utils.py': 'lightyellow',
        '__init__.py': 'lightgray'
    }

    # Add nodes grouped by file
    for file_name, nodes in file_groups.items():
        with dot.subgraph(name=f'cluster_{file_name}') as cluster:
            cluster.attr(label=file_name, style='filled', fillcolor='lightsteelblue')

            color = file_colors.get(file_name, 'lightblue')

            for node in nodes:
                node_label = f"{node['name']}\\nLine: {node.get('line', 'N/A')}"
                
                # Different representation for classes, methods, properties, and functions
                if node.get('kind') == 'CLASS':
                    # Classes: rectangle with double border and different color
                    cluster.node(node['id'], node_label, 
                               shape='box', style='rounded,filled,bold', 
                               fillcolor='lightcyan', penwidth='2')
                elif node.get('kind') == 'PROPERTY':
                    # Properties: diamond shape with distinct color
                    cluster.node(node['id'], node_label, 
                               shape='diamond', style='filled', 
                               fillcolor='lightpink')
                elif node.get('kind') == 'IMPORT':
                    # Imports: hexagon shape with distinct color
                    cluster.node(node['id'], node_label, 
                               shape='hexagon', style='filled', 
                               fillcolor='lightgoldenrodyellow')
                elif node.get('kind') == 'METHOD':
                    # Methods: rounded box with distinct color
                    cluster.node(node['id'], node_label, 
                               shape='box', style='rounded,filled', 
                               fillcolor='lightsteelblue')
                else:
                    # Functions: default rounded box
                    cluster.node(node['id'], node_label, fillcolor=color)

    # Add edges (function calls)
    for edge in graph_data['edges']:
        dot.edge(edge['from'], edge['to'])

    return dot


def create_text_visualization(graph_data):
    """Create a text-based visualization of the graph."""
    if not graph_data:
        return None

    print("\n" + "="*60)
    print("TEXT-BASED CODE CALL GRAPH VISUALIZATION")
    print("="*60)

    # Group nodes by file
    file_groups = {}
    for node in graph_data['nodes']:
        file_name = node['file']
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(node)

    # Display nodes by file
    print("\nCODE ELEMENTS BY FILE:")
    print("-" * 30)
    for file_name, nodes in file_groups.items():
        print(f"\n[FILE] {file_name}:")
        
        # Group by type within each file
        classes = [n for n in nodes if n.get('kind') == 'CLASS']
        functions = [n for n in nodes if n.get('kind') == 'FUNCTION']
        methods = [n for n in nodes if n.get('kind') == 'METHOD']
        properties = [n for n in nodes if n.get('kind') == 'PROPERTY']
        imports = [n for n in nodes if n.get('kind') == 'IMPORT']
        # Files are represented as containers (clusters), not as individual nodes
        
        if classes:
            print(f"   Classes:")
            for node in classes:
                print(f"     |-- [CLASS] {node['name']} (line {node.get('line', 'N/A')})")
        
        if methods:
            print(f"   Methods:")
            for node in methods:
                print(f"     |-- [METHOD] {node['name']} (line {node.get('line', 'N/A')})")
        
        if properties:
            print(f"   Properties:")
            for node in properties:
                print(f"     |-- [PROPERTY] {node['name']} (line {node.get('line', 'N/A')})")
        
        if imports:
            print(f"   Imports:")
            for node in imports:
                print(f"     |-- [IMPORT] {node['name']} (line {node.get('line', 'N/A')})")
        
        if functions:
            print(f"   Functions:")
            for node in functions:
                print(f"     |-- [FUNC] {node['name']} (line {node.get('line', 'N/A')})")

    # Display call relationships
    print(f"\nFUNCTION CALL RELATIONSHIPS ({len(graph_data['edges'])} total):")
    print("-" * 40)

    # Group edges by caller
    caller_groups = {}
    for edge in graph_data['edges']:
        caller = edge['from']
        if caller not in caller_groups:
            caller_groups[caller] = []
        caller_groups[caller].append(edge['to'])

    for caller, callees in caller_groups.items():
        caller_name = caller.split('::')[0]
        caller_file = caller.split('::')[1]
        print(f"\n[CALLER] {caller_name} ({caller_file}) calls:")
        for callee in callees:
            callee_name = callee.split('::')[0]
            callee_file = callee.split('::')[1]
            print(f"   |---> {callee_name} ({callee_file})")

    # Create a simple ASCII diagram
    print(f"\nASCII CALL FLOW DIAGRAM:")
    print("-" * 30)

    # Find entry point (functions that are called but don't call others)
    all_callers = set(edge['from'] for edge in graph_data['edges'])
    all_callees = set(edge['to'] for edge in graph_data['edges'])
    entry_points = all_callers - all_callees

    if entry_points:
        for entry in entry_points:
            entry_name = entry.split('::')[0]
            print(f"\n[{entry_name}] (Entry Point)")
            _print_call_tree(entry, graph_data['edges'], visited=set(), indent=1)
    else:
        print("\nNo clear entry point found. Showing all call relationships:")
        for caller, callees in caller_groups.items():
            caller_name = caller.split('::')[0]
            print(f"\n[{caller_name}]")
            for callee in callees:
                callee_name = callee.split('::')[0]
                print(f"  |---> [{callee_name}]")

    print("\n" + "="*60)
    return True


def _print_call_tree(node, edges, visited, indent=0, max_depth=5):
    """Recursively print call tree to avoid infinite loops."""
    if indent > max_depth or node in visited:
        if node in visited:
            print("  " * indent + "|---> [...] (circular reference)")
        return

    visited.add(node)

    # Find all functions this node calls
    callees = [edge['to'] for edge in edges if edge['from'] == node]

    for callee in callees:
        callee_name = callee.split('::')[0]
        print("  " * indent + f"|---> [{callee_name}]")
        _print_call_tree(callee, edges, visited.copy(), indent + 1, max_depth)


def create_dot_file(graph_data, filename=GRAPH_DOT_FILE):
    """Create a simple DOT file that can be used with any Graphviz installation."""
    if not graph_data:
        return False

    # Group nodes by file for better visualization
    file_groups = {}
    for node in graph_data['nodes']:
        file_name = node['file']
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(node)

    # Color scheme for different files
    file_colors = {
        'main.py': 'lightcoral',
        'operations.py': 'lightgreen', 
        'utils.py': 'lightyellow',
        '__init__.py': 'lightgray'
    }

    with open(filename, 'w') as f:
        f.write('digraph CodeCallGraph {\n')
        f.write('    rankdir=TB;\n')
        f.write('    node [shape=box, style="rounded,filled"];\n')
        f.write('    edge [color=darkblue, arrowhead=vee];\n\n')

        # Add subgraphs for each file
        for file_name, nodes in file_groups.items():
            cluster_name = file_name.replace('.', '_').replace('-', '_')
            f.write(f'    subgraph cluster_{cluster_name} {{\n')
            f.write(f'        label="{file_name}";\n')
            f.write('        style=filled;\n')
            f.write('        fillcolor=lightsteelblue;\n')

            color = file_colors.get(file_name, 'lightblue')

            for node in nodes:
                node_id = node['id'].replace('::', '_').replace('.', '_').replace('-', '_')
                node_label = f"{node['name']}\\nLine: {node.get('line', 'N/A')}"
                
                # Different representation for classes, methods, properties, and functions
                if node.get('kind') == 'CLASS':
                    f.write(f'        "{node_id}" [label="{node_label}", fillcolor=lightcyan, style="rounded,filled,bold", penwidth=2];\n')
                elif node.get('kind') == 'PROPERTY':
                    f.write(f'        "{node_id}" [label="{node_label}", shape=diamond, style=filled, fillcolor=lightpink];\n')
                elif node.get('kind') == 'IMPORT':
                    f.write(f'        "{node_id}" [label="{node_label}", shape=hexagon, style=filled, fillcolor=lightgoldenrodyellow];\n')
                elif node.get('kind') == 'METHOD':
                    f.write(f'        "{node_id}" [label="{node_label}", fillcolor=lightsteelblue, style="rounded,filled"];\n')
                else:
                    f.write(f'        "{node_id}" [label="{node_label}", fillcolor={color}];\n')

            f.write('    }\n\n')

        # Add edges
        f.write('    // Function call relationships\n')
        for edge in graph_data['edges']:
            from_id = edge['from'].replace('::', '_').replace('.', '_').replace('-', '_')
            to_id = edge['to'].replace('::', '_').replace('.', '_').replace('-', '_')
            f.write(f'    "{from_id}" -> "{to_id}";\n')

        f.write('}\n')

    return True


def save_and_display(dot, filename=GRAPH_IMAGE_FILE, output_format='png', view=False):
    """Save the graph and optionally display it."""
    if not dot:
        return False

    try:
        # Render and save the graph
        output_file = dot.render(filename, format=output_format, cleanup=True)
        print(f"Graph visualization saved as: {output_file}")

        # Optionally open the file
        if view:
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_file)
                elif os.name == 'posix':  # macOS and Linux
                    os.system(f'open "{output_file}"' if os.uname().sysname == 'Darwin' else f'xdg-open "{output_file}"')
            except Exception as e:
                print(f"Could not open file automatically: {e}")
                print(f"Please open {output_file} manually.")

        return True
    except Exception as e:
        print(f"Error creating visualization: {e}")
        return False


def main():
    """Main function to create and save the graph visualization."""
    print("Loading graph data...")
    
    # Load all three graphs
    combined_graph = load_graph_data(GRAPH_JSON_FILE)
    call_graph = load_graph_data(CALL_GRAPH_JSON_FILE) 
    declaration_graph = load_graph_data(DECLARATION_GRAPH_JSON_FILE)
    
    graphs = []
    if combined_graph:
        graphs.append(("Combined", combined_graph))
    if call_graph:
        graphs.append(("Call", call_graph))  
    if declaration_graph:
        graphs.append(("Declaration", declaration_graph))
    
    if not graphs:
        print("No graph data found. Run basic-parser.py first.")
        return
    
    for graph_name, graph_data in graphs:
        print(f"\n=== Processing {graph_name} Graph ===")
        print(f"Loaded {graph_name.lower()} graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")

        # Process each graph type
        print(f"\n1. Creating text-based visualization for {graph_name} graph...")
        create_text_visualization(graph_data)

        print(f"\n2. Creating Graphviz visualization for {graph_name} graph...")
        try:
            dot = create_visualization(graph_data)

            if dot:
                # Use graph-specific file names
                base_name = f"./artifacts/{graph_name.lower()}_graph"
                success = save_and_display(dot, base_name, 'png', view=False)

                if success:
                    print(f"Graphviz {graph_name} visualization created successfully!")
                else:
                    print(f"Failed to create Graphviz {graph_name} visualization.")
            else:
                print(f"Failed to create Graphviz {graph_name} graph object.")
        except Exception as e:
            print(f"Error with Graphviz {graph_name} visualization: {e}")

        print(f"\n3. Creating DOT file for {graph_name} graph...")
        try:
            dot_file = f"./artifacts/{graph_name.lower()}_graph.dot"
            create_dot_file(graph_data, dot_file)
            print(f"{graph_name} DOT file saved as: {dot_file}")
        except Exception as e:
            print(f"Error creating {graph_name} DOT file: {e}")

    print(f"\nVisualization complete! Generated visualizations for {len(graphs)} graph types.")


if __name__ == "__main__":
    main()