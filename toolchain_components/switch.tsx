"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { componentMetaDataType, configEntriesMap, inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import { substituteAny } from "@/types/toolchains";
import FileDropzone from "@/components/ui/file-dropzone";
import { useToolchainContextAction } from "@/app/app/context-provider";
import uploadFiles from "@/hooks/upload-files";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

export const METADATA : componentMetaDataType = {
  label: "Switch",
  type: "Input",
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

export default function SwitchInput({
	configuration,
  entriesMap,
  demo = false
}:{
	configuration: inputMapping,
  entriesMap: configEntriesMap,
  demo?: boolean
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
  } = (demo)?useToolchainContextAction():{callEvent: () => {}, storedEventArguments: null, sessionId: null};

  const handleSubmission = async (files: File[]) => {
    if (demo) return;

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
      <div className="inline-flex flex-row flex-shrink">
        <Switch className="" onCheckedChange={(c : boolean) => {}}/>
        <div className="h-auto flex flex-col justify-center pl-2">
          <Label>{entriesMap.get("Label")?.value as string}</Label>
        </div>
      </div>
    </div>
  )
}