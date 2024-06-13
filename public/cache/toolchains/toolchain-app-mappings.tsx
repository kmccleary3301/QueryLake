"use client";
import { 
	DISPLAY_COMPONENTS, 
	INPUT_COMPONENT_FIELDS, 
	configEntriesMap, 
	configEntry, 
	contentMapping, 
	displayComponents,
  displayMapping,
  inputMapping,
} from "@/types/toolchain-interface";

import ChatInput, { METADATA as METADATA_ChatInput } from '@/components/toolchain_interface/chat-input';
import Chat, { METADATA as METADATA_Chat } from '@/components/toolchain_interface/chat';
import CurrentEventDisplay, { METADATA as METADATA_CurrentEventDisplay } from '@/components/toolchain_interface/current-event-display';
import FileUpload, { METADATA as METADATA_FileUpload } from '@/components/toolchain_interface/file-upload';
import Markdown, { METADATA as METADATA_Markdown } from '@/components/toolchain_interface/markdown';
import Switch, { METADATA as METADATA_Switch } from '@/components/toolchain_interface/switch';
import Text, { METADATA as METADATA_Text } from '@/components/toolchain_interface/text';

import { useToolchainContextAction } from "@/app/app/context-provider";

export function ToolchainComponentMapper({
	info
}:{
	info: contentMapping
}) {
  
	const {
    toolchainState,
  } = useToolchainContextAction();

  const getEffectiveConfig = (info : inputMapping) => {
    let effectiveConfig : configEntriesMap = new Map();
    const default_fields = INPUT_COMPONENT_FIELDS[info.display_as];
    if (default_fields.config) {
      for (const entry of default_fields.config) {
        effectiveConfig.set(entry.name, {name: entry.name, value: entry.default});
      }
    }
    for (const entry of info.config) {
      effectiveConfig.set(entry.name, entry);
    }

    return effectiveConfig;
  }
  
	switch(info.display_as) {
		
    
    case "chat":
      return (
        <Chat configuration={(info as displayMapping)}/>
      );

    case "current-event-display":
      return (
        <CurrentEventDisplay configuration={(info as displayMapping)}/>
      );

    case "markdown":
      return (
        <Markdown configuration={(info as displayMapping)} toolchainState={toolchainState}/>
      );

    case "text":
      return (
        <Text configuration={(info as displayMapping)} toolchainState={toolchainState}/>
      );

    case "chat-input":
      return (
        <ChatInput configuration={info}/>
      );

    case "file-upload":
      return (
        <FileUpload configuration={info}/>
      );

    case "switch":
      return (
        <Switch configuration={info} entriesMap={getEffectiveConfig(info)}/>
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