"use client";

import { ViewVerticalIcon, ViewHorizontalIcon } from '@radix-ui/react-icons'

import {
	ContextMenu,
	ContextMenuContent,
	ContextMenuSeparator,
	ContextMenuItem,
	ContextMenuLabel,
	ContextMenuShortcut,
	ContextMenuSub,
	ContextMenuSubContent,
	ContextMenuSubTrigger,
	ContextMenuTrigger,
} from '@/registry/default/ui/context-menu';
import { 
	AlignLeft,
	AlignRight,
	AlignCenter,
	AlignJustify
} from 'lucide-react';
import { Button } from '@/registry/default/ui/button';
import { ToggleGroup, ToggleGroupItem } from '@/registry/default/ui/toggle-group';
import { alignType } from '../page';
import CompactInput from '@/registry/default/ui/compact-input';

export function ContextMenuViewportWrapper({
	onSplit,
	onCollapse,
	headerAvailable = true,
	footerAvailable = true,
	children
}: {
	onSplit : (split_type : "horizontal" | "vertical" | "header" | "footer", count: number) => void,
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
			<ContextMenuContent className="space-y-2 pt-6 p-2">
				<CompactInput placeholder='Inner Tailwind' className='h-8'/>
				<ContextMenuSeparator/>
				<ContextMenuSub>
          <ContextMenuSubTrigger inset>
					<p className='text-primary/0 text-xs'>.</p>Split Horizontal <div className='w-2'/><ViewVerticalIcon viewBox="0 0 15.5 15"/>
					</ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-48">
            <ContextMenuItem inset onClick={() => (onSplit("horizontal", 2))}>2</ContextMenuItem>
            <ContextMenuItem inset onClick={() => (onSplit("horizontal", 3))}>3</ContextMenuItem>
            <ContextMenuItem inset onClick={() => (onSplit("horizontal", 4))}>4</ContextMenuItem>
						<ContextMenuItem inset onClick={() => (onSplit("horizontal", 5))}>5</ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>
				<ContextMenuSub>
          <ContextMenuSubTrigger inset>
						<p className='text-primary/0 text-xs'>.</p>Split Vertical <div className='w-2'/><ViewHorizontalIcon/>
					</ContextMenuSubTrigger>
          <ContextMenuSubContent className="w-48">
            <ContextMenuItem inset onClick={() => (onSplit("vertical", 2))}>2</ContextMenuItem>
            <ContextMenuItem inset onClick={() => (onSplit("vertical", 3))}>3</ContextMenuItem>
            <ContextMenuItem inset onClick={() => (onSplit("vertical", 4))}>4</ContextMenuItem>
						<ContextMenuItem inset onClick={() => (onSplit("vertical", 5))}>5</ContextMenuItem>
          </ContextMenuSubContent>
        </ContextMenuSub>
				{/* <ContextMenuItem inset className='pr-2' onClick={() => (onSplit("horizontal"))}>
					Split Horizontal <div className='w-2'/><ViewVerticalIcon viewBox="0 0 15.5 15"/>
				</ContextMenuItem> */}
				{/* <ContextMenuItem inset onClick={() => (onSplit("vertical"))}>
					Split Vertical <div className='w-2'/><ViewHorizontalIcon/>
				</ContextMenuItem> */}
				{headerAvailable && (<ContextMenuItem inset onClick={() => (onSplit("header", 0))}>
					<p className='text-primary/0 text-xs'>.</p>Add Header
				</ContextMenuItem>)}
				{footerAvailable && (<ContextMenuItem inset onClick={() => (onSplit("footer", 0))}>
					<p className='text-primary/0 text-xs'>.</p>Add Footer
				</ContextMenuItem>)}
				<ContextMenuItem inset onClick={onCollapse}>
					<p className='text-primary/0 text-xs'>.</p>Delete
				</ContextMenuItem>
			</ContextMenuContent>
		</ContextMenu>
  );
}

export function ContextMenuHeaderWrapper({
	onCollapse,
	onAlign,
	align,
	children
}: {
	onCollapse : () => void,
	onAlign: (a : alignType) => void,
	align: alignType,
	children: React.ReactNode,
}) {
  return (
		<ContextMenu>
			<ContextMenuTrigger className="flex z-5 h-full w-full items-center justify-center text-sm">
				{children}
			</ContextMenuTrigger>
			<ContextMenuContent className="space-y-2 pt-4 p-2">
				<ToggleGroup 
					type="single" 
					onValueChange={(value : alignType | "") => {
						if (value !== "") onAlign(value);
					}}
					className='flex flex-row justify-between'
					value={align}
				>
					<ToggleGroupItem value="left" aria-label="Align left">
						<AlignLeft className="h-4 w-4" />
					</ToggleGroupItem>
					<ToggleGroupItem value="center" aria-label="Align center">
						<AlignCenter className="h-4 w-4" />
					</ToggleGroupItem>
					<ToggleGroupItem value="justify" aria-label="Align justify">
						<AlignJustify className="h-4 w-4" />
					</ToggleGroupItem>
					<ToggleGroupItem value="right" aria-label="Align right">
						<AlignRight className="h-4 w-4" />
					</ToggleGroupItem>
				</ToggleGroup>
				<ContextMenuItem inset onClick={onCollapse}>
					Delete
				</ContextMenuItem>
			</ContextMenuContent>
		</ContextMenu>
  );
}