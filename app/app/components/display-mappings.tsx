"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { 
	DISPLAY_COMPONENTS, 
	contentMapping, 
	displayComponents, 
	displayMapping,
} from "@/types/toolchain-interface";
import FileUpload, { FileUploadSkeleton } from "@/components/toolchain_interface/file-upload";
import ChatInput, { ChatInputSkeleton } from "@/components/toolchain_interface/chat-input";
import Chat, { ChatSkeleton } from "@/components/toolchain_interface/chat";
import Markdown, { MarkdownSkeleton } from "@/components/toolchain_interface/markdown";
import Text, { TextSkeleton } from "@/components/toolchain_interface/text";
import { useToolchainContextAction } from "../context-provider";
import { useContextAction } from "@/app/context-provider";
import { useCallback, useEffect } from "react";
import { substituteAny } from "@/types/toolchains";

export function ToolchainComponentMapper({
	info
}:{
	info: contentMapping
}) {
	const {
    toolchainState,
		toolchainWebsocket,
    sessionId,
  } = useToolchainContextAction();

  const {
    userData,
  } = useContextAction();

  const callEvent = useCallback((event: string, event_params: {[key : string]: substituteAny}) => {
    console.log("ToolchainComponentMapper callEvent", event, event_params, toolchainWebsocket, sessionId, userData?.auth)
    if (toolchainWebsocket?.current && sessionId?.current) {
      console.log("Sending Event", event, event_params);
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId.current,
          "event_node_id": event,
          "event_parameters": event_params
        }
      });
    }
  }, [userData]);

  // useEffect(() => {
  //   console.log("websocket changed in toolchain component mapper");
  // }, [callEvent]);

  // useEffect(() => {
  //   console.log("info updated!");
  
  // }, [info]);
  useEffect(() => {console.log("Rerendering")}, []);


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


		// Input Components
		case "chat_input":
			return (
				<ChatInput configuration={info} sendEvent={callEvent}/>
			)
		case "file_upload":
			return (
				<FileUpload configuration={info} sendEvent={callEvent}/>
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