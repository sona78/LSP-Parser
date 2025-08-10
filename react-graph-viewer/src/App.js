import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
} from 'reactflow';
import dagre from 'dagre';

import 'reactflow/dist/style.css';

const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  
  // Separate group nodes from regular nodes
  const groupNodes = nodes.filter(node => node.type === 'group');
  const regularNodes = nodes.filter(node => node.type !== 'group');
  
  // Layout group nodes with very generous spacing to accommodate large groups
  if (groupNodes.length === 1) {
    // Single group - center it
    groupNodes[0].position = { x: 50, y: 50 };
  } else if (groupNodes.length <= 3) {
    // Arrange horizontally for 2-3 groups with very generous spacing
    let xOffset = 50;
    groupNodes.forEach((node, index) => {
      node.position = {
        x: xOffset,
        y: 50,
      };
      // Use actual width plus generous gap
      xOffset += (node.style.width || 800) + 300; // 300px gap between groups
    });
  } else {
    // Grid layout for more groups with very generous spacing
    const cols = Math.ceil(Math.sqrt(groupNodes.length));
    let yOffsets = [50]; // Start first row at y=50
    let maxHeightInRow = [];
    
    groupNodes.forEach((node, index) => {
      const col = index % cols;
      const row = Math.floor(index / cols);
      
      // Ensure we have y-offset for this row
      if (!yOffsets[row]) {
        yOffsets[row] = yOffsets[row - 1] + (maxHeightInRow[row - 1] || 500) + 200;
      }
      
      node.position = {
        x: col * 1200 + 50, // Extra generous horizontal spacing
        y: yOffsets[row],
      };
      
      // Track max height in this row for next row calculation
      const nodeHeight = node.style.height || 500;
      maxHeightInRow[row] = Math.max(maxHeightInRow[row] || 0, nodeHeight);
    });
  }
  
  // Layout regular nodes within their groups
  const nodesByGroup = {};
  regularNodes.forEach(node => {
    const groupId = node.parentNode;
    if (!nodesByGroup[groupId]) {
      nodesByGroup[groupId] = [];
    }
    nodesByGroup[groupId].push(node);
  });
  
  Object.keys(nodesByGroup).forEach(groupId => {
    const groupNode = groupNodes.find(n => n.id === groupId);
    if (!groupNode) return;
    
    const nodesInGroup = nodesByGroup[groupId];
    
    // Create a mini layout for nodes within this group
    const miniGraph = new dagre.graphlib.Graph();
    miniGraph.setDefaultEdgeLabel(() => ({}));
    miniGraph.setGraph({ rankdir: direction, nodesep: 30, ranksep: 50 });
    
    nodesInGroup.forEach((node) => {
      miniGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
    });
    
    // Add edges between nodes in this group
    edges.forEach((edge) => {
      const sourceInGroup = nodesInGroup.find(n => n.id === edge.source);
      const targetInGroup = nodesInGroup.find(n => n.id === edge.target);
      if (sourceInGroup && targetInGroup) {
        miniGraph.setEdge(edge.source, edge.target);
      }
    });
    
    dagre.layout(miniGraph);
    
    // Position nodes relative to their group using a grid layout
    const nodeCount = nodesInGroup.length;
    const cols = Math.ceil(Math.sqrt(nodeCount));
    
    nodesInGroup.forEach((node, index) => {
      const nodeWithPosition = miniGraph.node(node.id);
      if (nodeWithPosition && miniGraph.nodes().length > 1) {
        // Use dagre layout if there are connections between nodes
        node.position = {
          x: nodeWithPosition.x - nodeWidth / 2 + 20,
          y: nodeWithPosition.y - nodeHeight / 2 + 70, // More space for title
        };
      } else {
        // Grid layout with very generous spacing matching group sizing
        const col = index % cols;
        const row = Math.floor(index / cols);
        const horizontalSpacing = 80; // Match the group calculation - extra horizontal space
        const verticalSpacing = 50;   // Match the group calculation
        const horizontalGroupPadding = 150; // Match the group calculation - extra horizontal padding
        const titleHeight = 100;      // Match the group calculation
        
        node.position = {
          x: horizontalGroupPadding + col * (nodeWidth + horizontalSpacing),
          y: titleHeight + row * (nodeHeight + verticalSpacing),
        };
      }
      
      node.targetPosition = isHorizontal ? 'left' : 'top';
      node.sourcePosition = isHorizontal ? 'right' : 'bottom';
    });
  });

  return { nodes, edges };
};

const getNodeStyle = (kind, file) => {
  const baseStyle = {
    background: '#fff',
    border: '1px solid #ddd',
    borderRadius: '3px',
    fontSize: '12px',
    padding: '10px',
    textAlign: 'center',
    minWidth: '150px',
  };

  const fileColors = {
    'main.py': '#ffcccb',        // Light red
    'operations.py': '#add8e6',  // Light blue  
    'utils.py': '#ffffe0',       // Light yellow
  };

  switch (kind) {
    case 'CLASS':
      return {
        ...baseStyle,
        background: fileColors[file] || '#lightcyan',
        border: '2px solid #0066cc',
        fontWeight: 'bold',
      };
    case 'METHOD':
      return {
        ...baseStyle,
        background: fileColors[file] || '#lightsteelblue',
        border: '1px solid #4682b4',
      };
    case 'FUNCTION':
      return {
        ...baseStyle,
        background: fileColors[file] || (file === 'utils.py' ? '#ffffe0' : '#ffcccb'),
        border: '1px solid #666',
      };
    case 'PROPERTY':
      return {
        ...baseStyle,
        background: '#lightpink',
        border: '1px solid #ff69b4',
        borderRadius: '50%',
        width: '120px',
        height: '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      };
    case 'IMPORT':
      return {
        ...baseStyle,
        background: '#lightgoldenrodyellow',
        border: '1px solid #daa520',
        borderRadius: '8px',
        clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)',
        width: '100px',
        height: '100px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      };
    default:
      return baseStyle;
  }
};

const transformGraphToReactFlow = (graph) => {
  // Group nodes by file
  const nodesByFile = {};
  graph.nodes.forEach(node => {
    if (!nodesByFile[node.file]) {
      nodesByFile[node.file] = [];
    }
    nodesByFile[node.file].push(node);
  });

  // Create regular nodes
  const nodes = graph.nodes.map((node) => ({
    id: node.id,
    data: {
      label: (
        <div>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
            {node.name}
          </div>
          <div style={{ fontSize: '10px', color: '#666' }}>
            Line {node.line}
          </div>
          <div style={{ fontSize: '9px', color: '#999' }}>
            [{node.kind}]
          </div>
        </div>
      ),
    },
    position: { x: 0, y: 0 }, // Will be set by layout algorithm
    style: getNodeStyle(node.kind, node.file),
    parentNode: `group-${node.file}`, // Assign to file group
    extent: 'parent',
  }));

  // Create group nodes for each file (subflows)
  const fileColors = {
    'main.py': '#ffeeee',        // Light red background
    'operations.py': '#eef5ff',  // Light blue background
    'utils.py': '#fffff0',       // Light yellow background
  };

  const groupNodes = Object.keys(nodesByFile).map(file => {
    const nodesInFile = nodesByFile[file];
    // Calculate size based on number of nodes in the file
    const nodeCount = nodesInFile.length;
    const cols = Math.ceil(Math.sqrt(nodeCount));
    const rows = Math.ceil(nodeCount / cols);
    
    // Calculate very generous sizing based on actual node content
    const horizontalSpacing = 80; // Extra generous horizontal spacing between nodes
    const verticalSpacing = 50;   // Generous vertical spacing between nodes
    const horizontalGroupPadding = 150; // Extra generous horizontal padding
    const verticalGroupPadding = 100;   // Generous vertical padding
    const titleHeight = 100;      // Generous space for title
    
    // Calculate content area needed for the grid of nodes
    const contentWidth = cols * nodeWidth + (cols - 1) * horizontalSpacing;
    const contentHeight = rows * nodeHeight + (rows - 1) * verticalSpacing;
    
    // Add very generous padding to get total group dimensions
    const totalWidth = contentWidth + (horizontalGroupPadding * 2);
    const totalHeight = contentHeight + titleHeight + verticalGroupPadding;
    
    return {
      id: `group-${file}`,
      data: {
        label: (
          <div style={{ 
            fontWeight: 'bold', 
            color: '#333',
            fontSize: '16px',
            padding: '12px',
            textAlign: 'center',
            borderBottom: '1px solid #ddd',
            marginBottom: '10px'
          }}>
            📁 {file} ({nodeCount} nodes)
          </div>
        )
      },
      position: { x: 0, y: 0 },
      style: {
        backgroundColor: fileColors[file] || '#f9f9f9',
        border: '2px solid #999',
        borderRadius: '12px',
        padding: '0',
        width: Math.max(800, totalWidth),   // Minimum 800px width, extra generous horizontally
        height: Math.max(500, totalHeight), // Minimum 500px height, very generous
        opacity: 0.7, // More transparent to show edges better
      },
      type: 'group',
      selectable: false,
      draggable: true,
    };
  });

  // Combine regular nodes and group nodes
  const allNodes = [...groupNodes, ...nodes];

  const edges = graph.edges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.from,
    target: edge.to,
    type: 'smoothstep',
    style: {
      strokeWidth: 3,
      stroke: '#2563eb',
      opacity: 0.9,
      zIndex: 10,
    },
    markerEnd: {
      type: 'arrowclosed',
      width: 24,
      height: 24,
      color: '#2563eb',
    },
    zIndex: 10,
  }));

  return { nodes: allNodes, edges };
};

function App() {
  const [graphType, setGraphType] = useState('combined');
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [graphData, setGraphData] = useState({
    combined: null,
    call: null,
    declaration: null,
  });
  const [loading, setLoading] = useState(true);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onLayout = useCallback(
    (direction) => {
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        nodes,
        edges,
        direction
      );

      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [nodes, edges, setNodes, setEdges]
  );

  // Load graph data on component mount
  useEffect(() => {
    const loadGraphData = async () => {
      try {
        const [combinedRes, callRes, declarationRes] = await Promise.all([
          fetch('/artifacts/combined_graph.json'),
          fetch('/artifacts/call_graph.json'),
          fetch('/artifacts/declaration_graph.json')
        ]);

        const [combined, call, declaration] = await Promise.all([
          combinedRes.json(),
          callRes.json(),
          declarationRes.json()
        ]);

        setGraphData({ combined, call, declaration });
      } catch (error) {
        console.error('Failed to load graph data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadGraphData();
  }, []);

  useEffect(() => {
    if (loading || !graphData[graphType]) return;

    const selectedGraph = graphData[graphType];
    const { nodes: transformedNodes, edges: transformedEdges } = 
      transformGraphToReactFlow(selectedGraph);

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      transformedNodes,
      transformedEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [graphType, graphData, loading, setNodes, setEdges]);

  if (loading) {
    return (
      <div className="app">
        <div className="controls">
          <h1>Code Graph Viewer</h1>
          <div>Loading graph data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="controls">
        <h1>Code Graph Viewer</h1>
        <select 
          value={graphType} 
          onChange={(e) => setGraphType(e.target.value)}
        >
          <option value="combined">Combined Graph</option>
          <option value="call">Call Graph</option>
          <option value="declaration">Declaration Graph</option>
        </select>
        <button onClick={() => onLayout('TB')}>Vertical Layout</button>
        <button onClick={() => onLayout('LR')}>Horizontal Layout</button>
      </div>
      
      <div className="graph-container">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          connectionLineType="smoothstep"
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </div>
    </div>
  );
}

export default App;