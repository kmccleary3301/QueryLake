"use client";

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

  const onAddTestItem = useCallback(
    (event : MouseEvent<HTMLDivElement, globalThis.MouseEvent>) => {
      // event.preventDefault();
      if (!reactFlowInstance) {
        return;
      }

      // const type = event.dataTransfer.getData('application/reactflow');

      // check if the dropped element is valid
      // if (typeof type === 'undefined' || !type) {
      //   return;
      // }

      // reactFlowInstance.project was renamed to reactFlowInstance.screenToFlowPosition
      // and you don't need to subtract the reactFlowBounds.left/top anymore
      // details: https://reactflow.dev/whats-new/2023-11-10
      // console.log("Event called with:", event);

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      // const newNode = {
      //   id: getId(),
      //   ,
      //   position,
      //   data: { label: `${type} node` },
      // };

      const newNode = {
        id: getId(),
        type: 'custom',
        data: { name: 'New Node', job: 'Beginner', emoji: '😎' },
        position: position,
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [reactFlowInstance],
  );

  return (
		<ContextMenu>
			<ContextMenuTrigger className="flex z-5 h-full w-full items-center justify-center rounded-md border border-dashed text-sm">
				{children}
			</ContextMenuTrigger>
			<ContextMenuContent className="w-64">
				<ContextMenuItem inset onClick={(event) => {
          onAddTestItem(event);
        }}>
          Add Test Item
				</ContextMenuItem>
				<ContextMenuItem inset disabled>
					Forward
					<ContextMenuShortcut>⌘]</ContextMenuShortcut>
				</ContextMenuItem>
				<ContextMenuItem inset>
					Reload
					<ContextMenuShortcut>⌘R</ContextMenuShortcut>
				</ContextMenuItem>
				<ContextMenuSub>
					<ContextMenuSubTrigger inset>More Tools</ContextMenuSubTrigger>
					<ContextMenuSubContent className="w-48">
						<ContextMenuItem>
							Save Page As...
							<ContextMenuShortcut>⇧⌘S</ContextMenuShortcut>
						</ContextMenuItem>
						<ContextMenuItem>Create Shortcut...</ContextMenuItem>
						<ContextMenuItem>Name Window...</ContextMenuItem>
						<ContextMenuSeparator />
						<ContextMenuItem>Developer Tools</ContextMenuItem>
					</ContextMenuSubContent>
				</ContextMenuSub>
				<ContextMenuSeparator />
				<ContextMenuCheckboxItem checked>
					Show Bookmarks Bar
					<ContextMenuShortcut>⌘⇧B</ContextMenuShortcut>
				</ContextMenuCheckboxItem>
				<ContextMenuCheckboxItem>Show Full URLs</ContextMenuCheckboxItem>
				<ContextMenuSeparator />
				<ContextMenuRadioGroup value="pedro">
					<ContextMenuLabel inset>People</ContextMenuLabel>
					<ContextMenuSeparator />
					<ContextMenuRadioItem value="pedro">
						Pedro Duarte
					</ContextMenuRadioItem>
					<ContextMenuRadioItem value="colm">Colm Tuite</ContextMenuRadioItem>
				</ContextMenuRadioGroup>
			</ContextMenuContent>
		</ContextMenu>
  );
}