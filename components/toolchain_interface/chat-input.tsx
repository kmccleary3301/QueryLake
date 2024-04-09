"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import { useEffect } from "react";

export function ChatInputSkeleton({
	configuration,
  children
}:{
	configuration: inputMapping,
  children: React.ReactNode
}) {
	useEffect(() => {console.log("ChatInputSkeleton configuration:", configuration)}, [configuration]);

  return (
    <Skeleton className={cn("rounded-md h-10 border-dashed border-[2px] border-primary/50 flex flex-col justify-center", configuration.tailwind)}>
      {children}
    </Skeleton>
  )
}


export default function ChatInput({
	configuration,
  on_upload = () => {},
  on_submit = () => {}
}:{
	configuration: inputMapping,
  on_upload?: (files: File[]) => void,
  on_submit?: (text: string) => void
}) {
    
}