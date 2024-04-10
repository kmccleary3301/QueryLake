"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";

export function FileUploadSkeleton({
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


export default function FileUpload({
	configuration,
  on_upload = () => {}
}:{
	configuration: inputMapping,
  on_upload?: (files: File[]) => void
}) {
  
}