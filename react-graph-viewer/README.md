# React Graph Viewer

Interactive visualization for Python code analysis graphs using React Flow.

## Features

- **Multiple Graph Types**: Switch between Combined, Call, and Declaration graphs
- **Interactive Layout**: Drag nodes, zoom, pan, and reorganize the graph
- **Automatic Layout**: Vertical and horizontal layout algorithms using Dagre
- **Node Types**: Different visual styles for classes, methods, functions, properties, and imports
- **File Grouping**: Color-coded nodes based on source file
- **Mini Map**: Overview of the entire graph
- **Controls**: Zoom controls and fit-to-view functionality

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

## Graph Data

The app reads JSON graph data from the `/public/artifacts/` directory:
- `combined_graph.json` - Complete graph with all relationships
- `call_graph.json` - Function/method call relationships only
- `declaration_graph.json` - Class-method/property structural relationships only

## Node Types

- **Classes**: Blue rounded rectangles with bold borders
- **Methods**: Blue rounded rectangles  
- **Functions**: Colored based on file (red for main.py, yellow for utils.py)
- **Properties**: Pink diamond shapes
- **Imports**: Yellow rotated squares (45°)

## Controls

- **Graph Type Selector**: Choose between Combined, Call, and Declaration graphs
- **Layout Buttons**: Switch between vertical (TB) and horizontal (LR) layouts
- **Zoom/Pan**: Use mouse wheel and drag to navigate
- **Node Dragging**: Drag nodes to reposition them