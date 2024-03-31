"use client";

import { ViewVerticalIcon, ViewHorizontalIcon } from '@radix-ui/react-icons'

import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuItem,
	ContextMenuTrigger,
} from '@/registry/default/ui/context-menu';

export default function ContextMenuWrapper({
	onSplit,
	onCollapse,
	headerAvailable = true,
	footerAvailable = true,
	children
}: {
	onSplit : (split_type : "horizontal" | "vertical" | "header" | "footer") => void,
	onCollapse : () => void,
	headerAvailable?: boolean,
	footerAvailable?: boolean,
	children: React.ReactNode,
}) {
  return (
		<ContextMenu>
			<ContextMenuTrigger className="flex z-5 h-full w-full items-center justify-center text-sm">
				{children}
			</ContextMenuTrigger>
			<ContextMenuContent className="w-64">
				<ContextMenuItem inset className='pr-2' onClick={() => (onSplit("horizontal"))}>
					Split Horizontal <div className='w-2'/><ViewVerticalIcon viewBox="0 0 15.5 15"/>
				</ContextMenuItem>
				<ContextMenuItem inset onClick={() => (onSplit("vertical"))}>
					Split Vertical <div className='w-2'/><ViewHorizontalIcon/>
				</ContextMenuItem>
				{headerAvailable && (<ContextMenuItem inset onClick={() => (onSplit("header"))}>
					Add Header <div className='w-2'/><ViewHorizontalIcon/>
				</ContextMenuItem>)}
				{footerAvailable && (<ContextMenuItem inset onClick={() => (onSplit("footer"))}>
					Add Footer <div className='w-2'/><ViewHorizontalIcon/>
				</ContextMenuItem>)}
				<ContextMenuItem inset onClick={onCollapse}>
					Delete
				</ContextMenuItem>
			</ContextMenuContent>
		</ContextMenu>
  );
}