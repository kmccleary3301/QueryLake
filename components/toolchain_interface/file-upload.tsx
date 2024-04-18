"use client";

import { cn } from "@/lib/utils";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import { substituteAny } from "@/types/toolchains";
import FileDropzone from "@/registry/default/ui/file-dropzone";
import { useToolchainContextAction } from "@/app/app/context-provider";

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
  // sendEvent = () => {},
}:{
	configuration: inputMapping,
  // sendEvent?: (event: string, event_params: {[key : string]: substituteAny}) => void
}) {
  const { userData, breakpoint } = useContextAction();
  const { callEvent } = useToolchainContextAction();

  const handleSubmission = (files: File[]) => {
    configuration.hooks.forEach(hook => {
      if (hook.hook === "on_upload") {

        // files.forEach(file => {

        //   sendEvent(hook.target_event, {
        //     [`${hook.target_route}`]: file,
        //   })
        // })
      }
    })
  }

  return (
    <FileDropzone onFile={handleSubmission} style={tailwindToObject([configuration.tailwind], breakpoint)}/>
  )
}