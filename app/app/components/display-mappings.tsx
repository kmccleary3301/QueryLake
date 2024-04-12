"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { 
	DISPLAY_COMPONENTS, 
	contentMapping, 
	displayComponents, 
	displayMapping,
} from "@/types/toolchain-interface";
import { FileUploadSkeleton } from "@/components/toolchain_interface/file-upload";
import { ChatInputSkeleton } from "@/components/toolchain_interface/chat-input";
import { ChatSkeleton } from "@/components/toolchain_interface/chat";
import { MarkdownSkeleton } from "@/components/toolchain_interface/markdown";
import { TextSkeleton } from "@/components/toolchain_interface/text";
import { useToolchainContextAction } from "../context-provider";

export function ToolchainComponentMapper({
	info,
	children
}:{
	info: contentMapping,
	children?: React.ReactNode
}) {
	const {
    toolchainState,
		toolchainWebsocket,
  } = useToolchainContextAction();

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
	setInfo,
}:{
	info: contentMapping,
	setInfo: (value: contentMapping) => void
}) {

	const onRouteSet = (value: (string | number)[]) => {
		setInfo({...info, display_route: value} as displayMapping);
	}	

	return (
		<>
		{(DISPLAY_COMPONENTS.includes(info.display_as as displayComponents)) ? ( // Display Component
			<div className="flex-grow flex flex-col pt-4 space-y-2">
				<ToolchainComponentMapper info={info}/>
			</div>
		) : ( // Input Component
			<div className="flex flex-row space-x-2 w-auto">
				<ToolchainComponentMapper info={info}/>
			</div>
		)}
		</>
	)
}