"use client";

import { useContextAction } from '@/app/context-provider';
import {
	ContextMenu,
	ContextMenuCheckboxItem,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuRadioGroup,
	ContextMenuRadioItem,
	ContextMenuSeparator,
	ContextMenuShortcut,
	ContextMenuSub,
	ContextMenuSubContent,
	ContextMenuSubTrigger,
	ContextMenuTrigger,
} from '@/registry/default/ui/context-menu';
// import { ScrollArea } from '@radix-ui/react-scroll-area';
import { ScrollArea } from '@/registry/default/ui/scroll-area';
import { APIFunctionSpec } from '@/types/globalTypes';
import { toolchainNode } from '@/types/toolchains';
import { MouseEvent, MouseEventHandler, useCallback } from 'react';
import { Node, ReactFlowInstance } from 'reactflow';


export default function ContextMenuWrapper({ 
  reactFlowInstance,
  setNodes,
  getId,
	children
}: {
  reactFlowInstance: ReactFlowInstance<any, any> | null;
  setNodes: React.Dispatch<React.SetStateAction<Node<object, string | undefined>[]>>;
  getId: () => string;
	children: React.ReactNode;
}) {

  const { apiFunctionSpecs } = useContextAction();

  const onAddTestItem = useCallback(
    (event : MouseEvent<HTMLDivElement, globalThis.MouseEvent>) => {
      // event.preventDefault();
      if (!reactFlowInstance) {
        console.log("No reactFlowInstance; exiting");
        return;
      }
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: "dndnode_test_"+getId(),
        position: position,
        data: { icon: <div/>, title: 'fullBundle' },
        type: 'turbo',
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlowInstance],
  );

  const onAddAPIFunctionNode = useCallback(
    (event : MouseEvent<HTMLDivElement, globalThis.MouseEvent>, api_func: APIFunctionSpec) => {
      // event.preventDefault();
      if (!reactFlowInstance) {
        console.log("No reactFlowInstance; exiting");
        return;
      }

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });


      const new_node_data : toolchainNode = {
        id: api_func.api_function_id + "_" + getId(),
        api_function: api_func.api_function_id,
        feed_mappings: [],
        input_arguments: api_func.function_args.map((arg) => ({
          key: arg.keyword,
          ...(arg.default_value?{ default_value: arg.default_value }:{}),
          ...(arg.type_hint?{ type_hint: arg.type_hint }:{}),
        }))
      }

      const newNode = {
        id: getId(),
        position: position,
        data: new_node_data,
        type: 'toolchain',
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [reactFlowInstance],
  );


  return (
		<ContextMenu modal={true}>
			<ContextMenuTrigger className="flex z-5 h-full w-full items-center justify-center rounded-md border border-dashed text-sm">
				{children}
			</ContextMenuTrigger>
			<ContextMenuContent className="w-64">
				<ContextMenuItem inset onClick={(event) => {
          onAddTestItem(event);
        }}>
          Add Test Item
				</ContextMenuItem>
				{/* <ContextMenuItem inset disabled>
					Forward
					<ContextMenuShortcut>⌘]</ContextMenuShortcut>
				</ContextMenuItem> */}
				<ContextMenuItem inset>
					Add Empty Node
				</ContextMenuItem>
				<ContextMenuSub>
					<ContextMenuSubTrigger inset>Add API Call</ContextMenuSubTrigger>
					<ContextMenuSubContent className="">
            <ScrollArea className='h-[400px]'>
            {apiFunctionSpecs?.map((spec, index) => (
              <ContextMenuItem inset key={index} className='pl-2 mr-2.5' onClick={(event) => {
                onAddAPIFunctionNode(event, spec);
              }}>
                {spec.api_function_id}
              </ContextMenuItem>
            ))}
            </ScrollArea>
            {/* <div className='p-5 flex flex-row space-x-1'>
              <ScrollArea className='h-[400px]'>

                <div className='w-[50px] h-[500px] bg-red-500'/>
              </ScrollArea>
            </div> */}
					</ContextMenuSubContent>
				</ContextMenuSub>
			</ContextMenuContent>
		</ContextMenu>
  );
}