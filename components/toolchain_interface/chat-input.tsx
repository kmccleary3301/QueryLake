"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";

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
  toolchainWebsocket,
}:{
	configuration: inputMapping,
  toolchainWebsocket?: ToolchainSession
}) {
  
}