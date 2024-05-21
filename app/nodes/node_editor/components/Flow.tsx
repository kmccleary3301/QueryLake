"use client";
import React, { useCallback, useMemo, useRef, useState } from 'react';
import ReactFlow, { useNodesState, useEdgesState, addEdge, MiniMap, Controls, Connection, Edge, Background, ReactFlowInstance, ReactFlowProvider } from 'reactflow';

import 'reactflow/dist/base.css';

import CustomNode, { ToolchainNodeReactFlow } from './CustomNode';
import ContextMenuWrapper from './context-menu-wrapper';
import { useNodeContextAction } from "../../context-provider"

// const nodeTypes = {
//   custom: CustomNode,
//   toolchainNode: ToolchainNodeReactFlow
// };

export default function Flow() {
  let id = 0;
  const getId = () => `dndnode_${id++}`;

  const { 
    toolchainNodes,
    setToolchainNodes,
    onNodesChange,
    toolchainEdges,
    setToolchainEdges,
    onEdgesChange
  } = useNodeContextAction();

  // const [nodes, setNodes, onNodesChange] = useNodesState<object>(initNodes);
  // const [edges, setEdges, onEdgesChange] = useEdgesState(initEdges);
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance<any, any> | null>(null);
  const reactFlowWrapper = useRef(null);


  const onConnect = useCallback((params :  Connection | Edge) => setToolchainEdges((eds) => addEdge(params, eds)), []);

  const nodeTypes = useMemo(
    () => ({
      custom: CustomNode,
      toolchainNode: ToolchainNodeReactFlow
    }),
    [],
  );

  return (
    <div className="flex-grow text-xs">
      <ContextMenuWrapper reactFlowInstance={reactFlowInstance} setNodes={setToolchainNodes} getId={getId}>
        <ReactFlowProvider>
          <div className="reactflow-wrapper w-full h-full" ref={reactFlowWrapper}>
            <ReactFlow
              nodes={toolchainNodes}
              edges={toolchainEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              nodeTypes={nodeTypes}
              fitView
              onInit={setReactFlowInstance}
              // className="bg-teal-50"
              className=""
            >
              <MiniMap zoomable pannable/>
              <Controls />
              <Background color="#aaa" gap={16}/>
            </ReactFlow>
          </div>
        </ReactFlowProvider>
      </ContextMenuWrapper>
    </div>
  );
};

// export default Flow;
