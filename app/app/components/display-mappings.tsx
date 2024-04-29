"use client";
import { 
	DISPLAY_COMPONENTS, 
	contentMapping, 
	displayComponents,
} from "@/types/toolchain-interface";
import FileUpload from "@/components/toolchain_interface/file-upload";
import ChatInput from "@/components/toolchain_interface/chat-input";
import Chat from "@/components/toolchain_interface/chat";
import Markdown from "@/components/toolchain_interface/markdown";
import Text from "@/components/toolchain_interface/text";
import { useToolchainContextAction } from "../context-provider";
import CurrentEventDisplay from "@/components/toolchain_interface/current-event-display";
export function ToolchainComponentMapper({
	info
}:{
	info: contentMapping
}) {
	const {
    toolchainState,
  } = useToolchainContextAction();

	switch(info.display_as) {
		// Display Components
		case "chat":
			return (
        <Chat configuration={info}/>
			);
		case "markdown":
			return (
				<Markdown configuration={info} toolchainState={toolchainState}/>
			);
		case "text":
			return (
				<Text configuration={info} toolchainState={toolchainState}/>
			);
		case "graph":
			return (
				<div>
					<h2>{"Graph (Not Implemented)"}</h2>
				</div>
			);
    case "running_event_display":
      return (
        <CurrentEventDisplay configuration={info}/>
      )



		// Input Components
		case "chat_input":
			return (
				<ChatInput configuration={info}/>
			)
		case "file_upload":
			return (
				<FileUpload configuration={info}/>
			);
	}
}

export default function DisplayMappings({
	info
}:{
	info: contentMapping
}) {

	return (
		<>
		{(DISPLAY_COMPONENTS.includes(info.display_as as displayComponents)) ? ( // Display Component
      <ToolchainComponentMapper info={info}/>
		) : ( // Input Component
      <ToolchainComponentMapper info={info}/>
		)}
		</>
	)
}