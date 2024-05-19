// ThemeProvider.tsx
'use client';
import {
  Dispatch,
	PropsWithChildren,
	SetStateAction,
	createContext,
	useContext,
	useRef,
} from 'react';
import { displaySection } from '@/types/toolchain-interface';
import ReactFlow, { useNodesState, useEdgesState, addEdge, MiniMap, Controls, Connection, Edge, Background, ReactFlowInstance, ReactFlowProvider, Node, NodeChange, EdgeChange } from 'reactflow';
import CustomNode from './node_editor/components/CustomNode';

type OnChange<ChangesType> = (changes: ChangesType[]) => void;

const nodeTypes = {
  custom: CustomNode,
};

const initNodes = [
  {
    id: '1',
    type: 'custom',
    data: { name: 'Jane Doe', job: 'CEO', emoji: '😎' },
    position: { x: 0, y: 50 },
  },
  {
    id: '2',
    type: 'custom',
    data: { name: 'Tyler Weary', job: 'Designer', emoji: '🤓' },

    position: { x: -200, y: 200 },
  },
  {
    id: '3',
    type: 'custom',
    data: { name: 'Kristi Price', job: 'Developer', emoji: '🤩' },
    position: { x: 200, y: 200 },
  },
];

const initEdges = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
  },
  {
    id: 'e1-3',
    source: '1',
    target: '3',
  },
];


const NodeContext = createContext<{
	interfaceConfiguration: displaySection;
	setInterfaceConfiguration: (value: displaySection) => void;
	getInterfaceConfiguration: () => displaySection;
  toolchainNodes: Node<object, string | undefined>[];
  setToolchainNodes: Dispatch<SetStateAction<Node<object, string | undefined>[]>>;
  onNodesChange: OnChange<NodeChange>;
  toolchainEdges: Edge<any>[];
  setToolchainEdges: Dispatch<SetStateAction<Edge<any>[]>>;
  onEdgesChange: OnChange<EdgeChange>;

}>({
	interfaceConfiguration: {
		split: "none",
		size: 100,
		align: "center",
		tailwind: "",
		mappings: []
	},
	setInterfaceConfiguration: () => {
		return {
			split: "none",
			size: 100,
			align: "center",
			tailwind: "",
			mappings: []
		}
	},
	getInterfaceConfiguration: () => {
		return {
			split: "none",
			size: 100,
			align: "center",
			tailwind: "",
			mappings: []
		}
	},
  toolchainNodes: [],
  setToolchainNodes: () => [],
  onNodesChange: () => [],
  toolchainEdges: [],
  setToolchainEdges: () => [],
  onEdgesChange: () => [],
});

export const NodeContextProvider = ({
	interfaceConfiguration,
	children,
}: PropsWithChildren<{ 
	interfaceConfiguration : displaySection,
}>) => {

  const [nodes, set_nodes, on_nodes_change] = useNodesState<object>(initNodes);
  const [edges, set_edges, on_edges_change] = useEdgesState(initEdges);

	const interface_configuration = useRef<displaySection>(interfaceConfiguration);
	const set_interface_configuration = (value: displaySection) => {
		interface_configuration.current = value;
	};
	const get_interface_configuration : () => displaySection = () => {
		return interface_configuration.current;
	};

	return (
		<NodeContext.Provider value={{ 
			interfaceConfiguration: interface_configuration.current,
			setInterfaceConfiguration: set_interface_configuration,
			getInterfaceConfiguration: get_interface_configuration,
      toolchainNodes: nodes,
      setToolchainNodes: set_nodes,
      onNodesChange: on_nodes_change,
      toolchainEdges: edges,
      setToolchainEdges: set_edges,
      onEdgesChange: on_edges_change,
		}}>
			{children}
		</NodeContext.Provider>
	);
};

export const useNodeContextAction = () => {
	return useContext(NodeContext);
};