"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import {default as ChatInputProto} from "@/registry/default/ui/chat-input";
import { substituteAny } from "@/types/toolchains";

export function ChatInputSkeleton({
	configuration,
  children
}:{
	configuration: inputMapping,
  children: React.ReactNode
}) {
  const { breakpoint } = useContextAction();
  
  return (
    <Skeleton 
      className="rounded-md h-10 border-dashed border-[2px] border-primary/50 flex flex-col justify-center"
      style={tailwindToObject([configuration.tailwind], breakpoint)}
    >
      {children}
    </Skeleton>
  )
}


export default function ChatInput({
	configuration,
  sendEvent = () => {},
}:{
	configuration: inputMapping,
  sendEvent?: (event: string, event_params: {[key : string]: substituteAny}) => void
}) {
  const { breakpoint } = useContextAction();

  const handleSubmission = (text : string, files: File[]) => {
    console.log("ChatInput handleSubmission", text, files);
    configuration.hooks.forEach(hook => {
      if (hook.hook === "on_submit") {
        sendEvent(hook.target_event, {
          [`${hook.target_route}`]: text,
        })
      }
    })
  }

  return (
    <ChatInputProto 
      style={tailwindToObject([configuration.tailwind], breakpoint)}
      onSubmission={handleSubmission}
    />
  )
}