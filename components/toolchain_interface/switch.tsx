"use client";

import { Skeleton } from "@/registry/default/ui/skeleton";
import { componentMetaDataType, configEntriesMap, inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import { substituteAny } from "@/types/toolchains";
import FileDropzone from "@/registry/default/ui/file-dropzone";
import { useToolchainContextAction } from "@/app/app/context-provider";
import uploadFiles from "@/hooks/upload-files";
import { Switch } from "@/registry/default/ui/switch";
import { Label } from "@/registry/default/ui/label";

export const METADATA : componentMetaDataType = {
  label: "Switch",
  category: "ShadCN Components",
  description: "A simple toggle switch.",
  config: {
    hooks: [
      "value_map",
    ],
    config: [
      {
        "name": "Label",
        "type": "string",
        "default": ""
      }
    ],
  }
};


export function SwitchInputSkeleton({
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

export default function SwitchInput({
	configuration,
  entriesMap,
}:{
	configuration: inputMapping,
  entriesMap: configEntriesMap
}) {
  const { 
    userData, 
    breakpoint, 
    selectedCollections
  } = useContextAction();

  const { 
    callEvent,
    storedEventArguments,
    sessionId,
  } = useToolchainContextAction();

  const handleSubmission = async (files: File[]) => {
    const fire_queue : {[key : string]: object}[]= 
    Array(Math.max(...configuration.hooks.map(hook => hook.fire_index))).fill({});
    
    configuration.hooks.forEach(hook => {
      let new_args = {};

      if (hook.hook === "selected_collections") {
        const collections = Array.from(selectedCollections.keys()).filter((key) => selectedCollections.get(key) === true);
        new_args = {
          [`${hook.target_route}`]: collections,
        }
      }
      fire_queue[hook.fire_index-1][hook.target_event] = {
        ...fire_queue[hook.fire_index-1][hook.target_event] || {},
        ...new_args,
      }
    })

    fire_queue.forEach((fire_index_bin) => {
      Object.entries(fire_index_bin).forEach(([event, event_params]) => {
        callEvent(userData?.auth || "", event, {
          ...(storedEventArguments?.current.get(event) || {}),
          ...event_params,
        })
      })
    })

  }

  return (
    <div style={tailwindToObject([configuration.tailwind], breakpoint)}>
      <div className="flex flex-row">
        <Switch className="" onCheckedChange={(c : boolean) => {}}/>
        <div className="h-auto flex flex-col justify-center pl-2">
          <Label>{entriesMap.get("Label")?.value as string}</Label>
        </div>
      </div>
    </div>
  )
}