"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { 
	DISPLAY_COMPONENTS, 
	contentMapping, 
	displayComponents, 
	displayMapping, 
	inputComponents, 
	inputMapping
} from "@/types/toolchain-interface";
import { Input } from "@/registry/default/ui/input";
import { 
	Trash2,
	Plus,
	CircleEllipsis
} from 'lucide-react';
import { Button } from "@/registry/default/ui/button";
import RouteSetter from "./route-setter";
import RouteAddSheet from "./route-add-sheet";
import SheetDemo from "@/registry/default/example/sheet-demo";
import InputComponentSheet from "./input-component-sheet";
import { BreadcrumbEllipsis } from "@/registry/default/ui/breadcrumb";
import { FileUploadSkeleton } from "@/components/toolchain_interface/file-upload";
import { ChatInputSkeleton } from "@/components/toolchain_interface/chat-input";
import { ChatSkeleton } from "@/components/toolchain_interface/chat";
import { MarkdownSkeleton } from "@/components/toolchain_interface/markdown";
import { TextSkeleton } from "@/components/toolchain_interface/text";
import { CurrentEventDisplaySkeleton } from "@/components/toolchain_interface/current-event-display";

export function DisplayComponentSkeletonMapper({
	info,
	children
}:{
	info: contentMapping,
	children?: React.ReactNode
}) {
	switch(info.display_as) {
		// Display Components
		case "chat":
			return (
				<ChatSkeleton configuration={info}/>
			);
		case "markdown":
			return (
				<MarkdownSkeleton	configuration={info}/>
			);
		case "text":
			return (
				<TextSkeleton configuration={info}/>
			);
		case "graph":
			return (
				<div>
					<h2>{"Graph (Not Implemented)"}</h2>
				</div>
			);
    case "running_event_display":
      return (
        <CurrentEventDisplaySkeleton configuration={info}/>
      )

		// Input Components
		case "chat_input":
			return (
				<ChatInputSkeleton configuration={info}>
					{children}
				</ChatInputSkeleton>
			)
		case "file_upload":
			return (
				<FileUploadSkeleton configuration={info}>
					{children}
				</FileUploadSkeleton>
			);
	}
}

export default function DisplayMappings({
	info,
	onDelete,
	setInfo,
}:{
	info: contentMapping,
	onDelete: () => void,
	setInfo: (value: contentMapping) => void
}) {

	const onRouteSet = (value: (string | number)[]) => {
		setInfo({...info, display_route: value} as displayMapping);
	}	

	return (
		<>
		{(DISPLAY_COMPONENTS.includes(info.display_as as displayComponents)) ? ( // Display Component
			<div className="flex-grow flex flex-col pt-4 space-y-2">
				<div className="w-auto flex flex-row space-x-2 justify-between">
					<div className="flex-grow h-auto flex flex-col justify-center text-base">
						<div className="flex flex-row">
							Display as:
							<p className="underline pl-2">{" "+info.display_as}</p>
						</div>
					</div>
					<Button size="icon" variant="ghost" onClick={onDelete}>
						<Trash2 className="w-4 h-4 text-primary" />
					</Button>
				</div>
				<div className="w-auto flex flex-row space-x-2 min-h-10 justify-between">
					<div className="flex-grow h-auto flex flex-col justify-center">
						{((info as displayMapping).display_route.length > 0) ? (
							<RouteSetter onRouteSet={onRouteSet} route={(info as displayMapping).display_route}/>
						) : (
							<p className="text-primary/40 select-none h-auto flex flex-col justify-center">{"Add a state object route."}</p>
						)}
					</div>
					{/* <div className="pr-2"> */}
						<RouteAddSheet
							type={"string"}
							onChange={(value) => {
								onRouteSet([...(info as displayMapping).display_route, value]);
							}}
						>
							<Button size="icon" variant="ghost">
									<Plus className="w-4 h-4 text-primary" />
							</Button>
						</RouteAddSheet>
					{/* </div> */}
				</div>
				<DisplayComponentSkeletonMapper info={info}/>
			</div>
		) : ( // Input Component
			<div className="flex flex-row space-x-2 w-auto">
				<DisplayComponentSkeletonMapper info={info}>
					<div className="flex flex-row space-x-1 w-auto justify-between">
					<InputComponentSheet
						value={info as inputMapping}
						type={info.display_as as inputComponents}
						onChange={(value : inputMapping) => {
							setInfo(value);
						}}
						onDelete={onDelete}
					>
						{/* <Button size="icon" variant="ghost"> */}
						<div className="w-10 flex flex-col justify-center">
							<div className="w-auto flex flex-row justify-center">
								<BreadcrumbEllipsis className="w-4 h-4 text-primary" />
							</div>
						</div>
						{/* </Button> */}
					</InputComponentSheet>
					<p className="flex-grow text-center select-none h-auto flex flex-col justify-center">
						{info.display_as}
					</p>
					{/* <Button size="icon" variant="ghost" onClick={onDelete}> */}
					<div className="w-10 flex flex-col justify-center">
						<div className="w-auto flex flex-row justify-center">
							<Trash2 className="w-4 h-4 text-primary" onClick={onDelete} />
						</div>
					</div>
					{/* </Button> */}
					</div>
				</DisplayComponentSkeletonMapper>
				
				
			</div>
		)}
		</>
	)
}