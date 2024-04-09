"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";

export function FileUploadSkeleton({
	configuration,
  children
}:{
	configuration: inputMapping,
  children: React.ReactNode
}) {
  return (
    <Skeleton className={cn("rounded-md h-10 border-dashed border-[2px] border-primary/50 flex flex-col justify-center", configuration.tailwind)}>
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