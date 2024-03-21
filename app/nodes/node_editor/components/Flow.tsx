"use client";
// import { useCallback } from 'react';
import {
  Node,
  // useNodesState,
  // useEdgesState,
  // addEdge,
  Connection,
  Edge,
  ConnectionLineType,
  MiniMap,
  Controls,
  // Background,
} from 'reactflow';
// import 'reactflow/dist/style.css';
import ContextMenuWrapper from './context-menu-wrapper';
import React, { useCallback } from 'react';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  useStoreApi,
} from 'reactflow';
import { initialEdges, initialNodes } from './nodes-and-edges';
import customNode2 from './custom-node-2';


import 'reactflow/dist/style.css';

// import CustomNode from './CustomNode';
// import ElkNode from './api-node';

// const initialNodes: Node[] = [
//   {
//     id: '1',
//     type: 'input',
//     data: { label: 'Node 1' },
//     position: { x: 250, y: 5 },
//   },
//   {
//     id: '2',
//     data: { label: 'Node 2' },
//     position: { x: 100, y: 100 },
//   },
//   {
//     id: '3',
//     data: { label: 'Node 3' },
//     position: { x: 400, y: 100 },
//   },
//   {
//     id: '4',
//     data: { label: 'Node 4' },
//     position: { x: 400, y: 200 },
//     type: 'elk',
//     // className: styles.customNode,
//   },
// ];

// const initialEdges: Edge[] = [
//   { id: 'e1-2', source: '1', target: '2' },
//   { id: 'e1-3', source: '1', target: '3' },
// ];

const nodeTypes = {
  customOne: customNode2
};

// const defaultEdgeOptions = {
//   animated: true,
//   type: 'smoothstep',
// };

const minimapStyle = {
  height: 120,
};

// export default function Flow() {
//   const [nodes, , onNodesChange] = useNodesState(initialNodes);
//   const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
//   const onConnect = useCallback(
//     (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
//     [setEdges]
//   );

//   return (
//     <div className="flex-grow text-xs">
//       <ContextMenuWrapper>
//         <ReactFlow
//           nodes={nodes}
//           onNodesChange={onNodesChange}
//           edges={edges}
//           onEdgesChange={onEdgesChange}
//           onConnect={onConnect}
//           nodeTypes={nodeTypes}
//           defaultEdgeOptions={defaultEdgeOptions}
//           connectionLineType={ConnectionLineType.SmoothStep}
//           fitView
//           minZoom={0.002}
//           className='z-0'
//         >
//           <MiniMap style={minimapStyle} zoomable pannable />
//           <Controls />
//           <Background color="#aaa" gap={16} />
//         </ReactFlow>
//       </ContextMenuWrapper>
//     </div>
//   );
// }


// import './style.css';

// import { initialEdges, initialNodes } from './nodes-and-edges';


const MIN_DISTANCE = 150;

const Flow = () => {
  const store = useStoreApi();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params : Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  const getClosestEdge = useCallback((node : Node) => {
    const { nodeInternals } = store.getState();
    const storeNodes = Array.from(nodeInternals.values());

    const closestNode : {node : null | Node} = storeNodes.reduce(
      (res, n : Node) => {
        if (n.id !== node.id && n.positionAbsolute && node.positionAbsolute) {
          const dx = n.positionAbsolute.x - node.positionAbsolute.x;
          const dy = n.positionAbsolute.y - node.positionAbsolute.y;
          const d = Math.sqrt(dx * dx + dy * dy);

          if (d < res.distance && d < MIN_DISTANCE) {
            res.distance = d;
            res.node = n;
          }
        }

        return res;
      },
      {
        distance: Number.MAX_VALUE,
        node: null as Node | null,
      },
    );

    if (!closestNode.node) {
      return null;
    }

    if (closestNode.node.positionAbsolute === undefined || node.positionAbsolute === undefined) return;

    const closeNodeIsSource = 
      closestNode.node.positionAbsolute.x < node.positionAbsolute.x;

    return {
      id: closeNodeIsSource
        ? `${closestNode.node.id}-${node.id}`
        : `${node.id}-${closestNode.node.id}`,
      source: closeNodeIsSource ? closestNode.node.id : node.id,
      target: closeNodeIsSource ? node.id : closestNode.node.id,
    };
  }, []);

  const onNodeDrag = useCallback(
    (_ : React.MouseEvent<Element, MouseEvent>, node : Node) => {
      const closeEdge = getClosestEdge(node);

      setEdges((es) => {
        const nextEdges = es.filter((e) => e.className !== 'temp');

        if (
          closeEdge &&
          !nextEdges.find(
            (ne) =>
              ne.source === closeEdge.source && ne.target === closeEdge.target,
          )
        ) {
          // closeEdge.className = 'temp';
          nextEdges.push(closeEdge);
        }

        return nextEdges;
      });
    },
    [getClosestEdge, setEdges],
  );

  const onNodeDragStop = useCallback(
    (_ : React.MouseEvent<Element, MouseEvent>, node : Node) => {
      const closeEdge = getClosestEdge(node);

      setEdges((es) => {
        const nextEdges = es.filter((e) => e.className !== 'temp');

        if (
          closeEdge &&
          !nextEdges.find(
            (ne) =>
              ne.source === closeEdge.source && ne.target === closeEdge.target,
          )
        ) {
          nextEdges.push(closeEdge);
        }

        return nextEdges;
      });
    },
    [getClosestEdge],
  );

  return (
    <div className="flex-grow text-xs">
      <ContextMenuWrapper>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeDrag={onNodeDrag}
          onNodeDragStop={onNodeDragStop}
          onConnect={onConnect}
          fitView
        >
          <MiniMap style={minimapStyle} zoomable pannable />
          <Controls />
          <Background color="#aaa" gap={16} />
          {/* <Background variant={BackgroundVariant.Cross} gap={50} /> */}
        </ReactFlow>
      </ContextMenuWrapper>
    </div>
  );
};

export default () => (
  <ReactFlowProvider>
    <Flow />
  </ReactFlowProvider>
);
