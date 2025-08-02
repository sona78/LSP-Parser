#!/usr/bin/env python3
"""
Graph Visualization Tool using Matplotlib
Creates a visual representation of the code graph using matplotlib and networkx.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from files import GRAPH_JSON_FILE, GRAPH_MATPLOTLIB_PNG_FILE, GRAPH_MATPLOTLIB_PDF_FILE
try:
    import networkx as nx
except ImportError:
    print("NetworkX not available. Creating a basic matplotlib visualization...")
    nx = None


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


def create_matplotlib_visualization(graph_data):
    """Create visualization using matplotlib without networkx."""
    if not graph_data:
        return None
    
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_title('Code Call Graph', fontsize=16, fontweight='bold')
    
    # Group nodes by file
    file_groups = {}
    for node in graph_data['nodes']:
        file_name = node['file']
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(node)
    
    # Color scheme for different files
    file_colors = {
        'main.py': '#ffcccb',      # light red
        'operations.py': '#90ee90', # light green
        'utils.py': '#ffffe0',     # light yellow
        '__init__.py': '#d3d3d3'   # light gray
    }
    
    # Position nodes in groups
    y_start = 0.9
    y_spacing = 0.8 / len(file_groups)
    node_positions = {}
    
    for i, (file_name, nodes) in enumerate(file_groups.items()):
        y_pos = y_start - i * y_spacing
        x_spacing = 0.8 / max(len(nodes), 1)
        x_start = 0.1
        
        # Draw file group background
        rect = patches.Rectangle((0.05, y_pos - 0.15), 0.9, 0.25, 
                               linewidth=2, edgecolor='black', 
                               facecolor=file_colors.get(file_name, '#lightblue'), 
                               alpha=0.3)
        ax.add_patch(rect)
        
        # Add file name label
        ax.text(0.5, y_pos + 0.05, file_name, fontsize=12, fontweight='bold', 
                ha='center', va='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Position nodes within the group
        for j, node in enumerate(nodes):
            x_pos = x_start + j * x_spacing
            node_positions[node['id']] = (x_pos, y_pos - 0.05)
            
            # Draw node
            circle = patches.Circle((x_pos, y_pos - 0.05), 0.03, 
                                  facecolor=file_colors.get(file_name, '#lightblue'),
                                  edgecolor='black', linewidth=1)
            ax.add_patch(circle)
            
            # Add node label
            ax.text(x_pos, y_pos - 0.12, node['name'], fontsize=8, ha='center', va='top',
                   rotation=45 if len(node['name']) > 8 else 0)
    
    # Draw edges
    for edge in graph_data['edges']:
        from_pos = node_positions.get(edge['from'])
        to_pos = node_positions.get(edge['to'])
        
        if from_pos and to_pos:
            # Draw arrow
            ax.annotate('', xy=to_pos, xytext=from_pos,
                       arrowprops=dict(arrowstyle='->', color='blue', lw=1.5, alpha=0.7))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add legend
    legend_elements = [patches.Patch(color=color, label=file) 
                      for file, color in file_colors.items() 
                      if any(node['file'] == file for node in graph_data['nodes'])]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
    
    plt.tight_layout()
    return fig


def create_networkx_visualization(graph_data):
    """Create visualization using networkx."""
    if not graph_data or not nx:
        return None
    
    # Create directed graph
    G = nx.DiGraph()
    
    # Add nodes with attributes
    for node in graph_data['nodes']:
        G.add_node(node['id'], 
                  name=node['name'], 
                  file=node['file'],
                  kind=node['kind'])
    
    # Add edges
    for edge in graph_data['edges']:
        G.add_edge(edge['from'], edge['to'])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Group nodes by file for layout
    file_groups = {}
    for node in graph_data['nodes']:
        file_name = node['file']
        if file_name not in file_groups:
            file_groups[file_name] = []
        file_groups[file_name].append(node['id'])
    
    # Create custom layout
    pos = {}
    y_positions = {file: i for i, file in enumerate(file_groups.keys())}
    
    for file_name, node_ids in file_groups.items():
        y = y_positions[file_name]
        for i, node_id in enumerate(node_ids):
            x = i - len(node_ids) / 2
            pos[node_id] = (x, y)
    
    # Color scheme
    file_colors = {
        'main.py': '#ffcccb',
        'operations.py': '#90ee90', 
        'utils.py': '#ffffe0',
        '__init__.py': '#d3d3d3'
    }
    
    # Get node colors
    node_colors = []
    for node_id in G.nodes():
        file_name = G.nodes[node_id]['file']
        node_colors.append(file_colors.get(file_name, '#lightblue'))
    
    # Draw the graph
    nx.draw(G, pos, ax=ax,
            node_color=node_colors,
            node_size=2000,
            font_size=8,
            font_weight='bold',
            arrows=True,
            arrowsize=20,
            edge_color='blue',
            alpha=0.7,
            labels={node: G.nodes[node]['name'] for node in G.nodes()})
    
    ax.set_title('Code Call Graph (NetworkX)', fontsize=16, fontweight='bold')
    
    # Add legend
    legend_elements = [patches.Patch(color=color, label=file) 
                      for file, color in file_colors.items() 
                      if any(G.nodes[node]['file'] == file for node in G.nodes())]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    return fig


def main():
    """Main function to create and save the graph visualization."""
    print("Loading graph data...")
    graph_data = load_graph_data()
    
    if not graph_data:
        return
    
    print(f"Loaded graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
    
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        
        # Try NetworkX first, fallback to matplotlib-only
        if nx:
            print("Creating NetworkX visualization...")
            fig = create_networkx_visualization(graph_data)
        else:
            print("Creating matplotlib visualization...")
            fig = create_matplotlib_visualization(graph_data)
        
        if fig:
            # Save the figure
            fig.savefig(GRAPH_MATPLOTLIB_PNG_FILE, dpi=300, bbox_inches='tight')
            print(f"Graph visualization saved as: {GRAPH_MATPLOTLIB_PNG_FILE}")
            
            # Also save as PDF
            fig.savefig(GRAPH_MATPLOTLIB_PDF_FILE, bbox_inches='tight')
            print(f"Graph visualization saved as: {GRAPH_MATPLOTLIB_PDF_FILE}")
            
            plt.close(fig)
            print("Visualization created successfully!")
        else:
            print("Failed to create visualization.")
            
    except ImportError:
        print("Matplotlib not available. Cannot create visualization.")
        print("Please install matplotlib: pip install matplotlib")
    except Exception as e:
        print(f"Error creating visualization: {e}")


if __name__ == "__main__":
    main()