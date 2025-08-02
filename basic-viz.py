#!/usr/bin/env python3
"""
Graph Visualization Tool
Creates visual representations of the code graph using multiple methods.
"""

import json
import os
from files import GRAPH_JSON_FILE, GRAPH_DOT_FILE, GRAPH_IMAGE_FILE, GRAPH_PNG_FILE, GRAPH_SVG_FILE, GRAPH_PDF_FILE, GRAPH_MATPLOTLIB_PNG_FILE

# Try to import optional dependencies
try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


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
    print("\nFUNCTIONS BY FILE:")
    print("-" * 30)
    for file_name, nodes in file_groups.items():
        print(f"\n[FILE] {file_name}:")
        for node in nodes:
            print(f"   |-- {node['name']} (line {node.get('line', 'N/A')})")
    
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
    graph_data = load_graph_data()
    
    if not graph_data:
        return
    
    print(f"Loaded graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
    
    # Always create text visualization (no dependencies required)
    print("\n1. Creating text-based visualization...")
    create_text_visualization(graph_data)
    
    # Try Graphviz visualization if available
    if HAS_GRAPHVIZ:
        print("\n2. Creating Graphviz visualization...")
        try:
            dot = create_visualization(graph_data)
            
            if dot:
                # Save as PNG
                success = save_and_display(dot, GRAPH_IMAGE_FILE, 'png', view=False)
                
                if success:
                    print("Graphviz visualization created successfully!")
                    
                    # Also create other formats
                    save_and_display(dot, GRAPH_SVG_FILE.replace('.svg', ''), 'svg', view=False)
                    save_and_display(dot, GRAPH_PDF_FILE.replace('.pdf', ''), 'pdf', view=False)
                    
                    print("Available formats:")
                    print(f"- {GRAPH_PNG_FILE} (main visualization)")
                    print(f"- {GRAPH_SVG_FILE} (scalable vector)")
                    print(f"- {GRAPH_PDF_FILE} (PDF document)")
                else:
                    print("Failed to create Graphviz visualization.")
            else:
                print("Failed to create Graphviz graph object.")
        except Exception as e:
            print(f"Error with Graphviz visualization: {e}")
    else:
        print("\n2. Graphviz not available - skipping Graphviz visualization")
        print("   To install: pip install graphviz")
        print("   Also install Graphviz software from https://graphviz.org/")
    
    # Try matplotlib visualization if available
    if HAS_MATPLOTLIB:
        print("\n3. Creating matplotlib visualization...")
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.set_title('Code Call Graph (Simple Layout)', fontsize=14, fontweight='bold')
            
            # Simple visualization using matplotlib
            # Group nodes by file and create a simple layout
            file_groups = {}
            for node in graph_data['nodes']:
                file_name = node['file']
                if file_name not in file_groups:
                    file_groups[file_name] = []
                file_groups[file_name].append(node)
            
            node_positions = {}
            colors = ['lightcoral', 'lightgreen', 'lightyellow', 'lightgray']
            
            y_start = 0.8
            for i, (file_name, nodes) in enumerate(file_groups.items()):
                y_pos = y_start - i * 0.2
                x_start = 0.1
                x_step = 0.8 / max(len(nodes), 1)
                
                for j, node in enumerate(nodes):
                    x_pos = x_start + j * x_step
                    node_positions[node['id']] = (x_pos, y_pos)
                    
                    # Draw node
                    circle = patches.Circle((x_pos, y_pos), 0.02, 
                                          facecolor=colors[i % len(colors)],
                                          edgecolor='black')
                    ax.add_patch(circle)
                    
                    # Add label
                    ax.text(x_pos, y_pos - 0.05, node['name'], 
                           fontsize=6, ha='center', va='top')
                
                # Add file label
                ax.text(0.05, y_pos, file_name, fontsize=10, fontweight='bold')
            
            # Draw edges
            for edge in graph_data['edges']:
                from_pos = node_positions.get(edge['from'])
                to_pos = node_positions.get(edge['to'])
                
                if from_pos and to_pos:
                    ax.annotate('', xy=to_pos, xytext=from_pos,
                               arrowprops=dict(arrowstyle='->', color='blue', alpha=0.6))
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            plt.tight_layout()
            fig.savefig(GRAPH_MATPLOTLIB_PNG_FILE, dpi=200, bbox_inches='tight')
            plt.close(fig)
            
            print(f"Matplotlib visualization saved as: {GRAPH_MATPLOTLIB_PNG_FILE}")
            
        except Exception as e:
            print(f"Error with matplotlib visualization: {e}")
    else:
        print("\n3. Matplotlib not available - skipping matplotlib visualization")
        print("   To install: pip install matplotlib")
    
    # Always create a simple DOT file that can be used with any Graphviz installation
    print("\n4. Creating DOT file for external Graphviz use...")
    try:
        create_dot_file(graph_data, GRAPH_DOT_FILE)
        print(f"DOT file saved as: {GRAPH_DOT_FILE}")
        print(f"To render with external Graphviz: dot -Tpng {GRAPH_DOT_FILE} -o graph.png")
    except Exception as e:
        print(f"Error creating DOT file: {e}")
    
    print(f"\nVisualization complete! Check the output files and text display above.")


if __name__ == "__main__":
    main()