"use client";

import { Skeleton } from "@/registry/default/ui/skeleton";
import { componentMetaDataType, inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import { substituteAny } from "@/types/toolchains";
import FileDropzone from "@/registry/default/ui/file-dropzone";
import { useToolchainContextAction } from "@/app/app/context-provider";
import uploadFiles from "@/hooks/upload-files";

export const METADATA : componentMetaDataType = {
  label: "File Upload",
  category: "Input",
  description: "A dropzone box for file uploads that immediately triggers on upload.",
  config: {
		"hooks": [
      "on_upload",
      "selected_collections"
    ],
		"config": [
			{
				"name": "multiple",
				"type": "boolean",
        "default": false
			}
		],
	}
};


export function SKELETON({
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
    
    const hasOnUploadHook = configuration.hooks.some(hook => hook.hook === 'on_upload');
    let file_upload_hashes : string[] = [];
    if (hasOnUploadHook && files.length > 0) {
      const uploadFileResponses = await uploadFiles({
        files: files,
        url: "/upload/",
        parameters: {
          "auth": userData?.auth as string,
          "collection_hash_id": sessionId?.current as string,
          "collection_type" : "toolchain_session"
        }
      });
      file_upload_hashes = uploadFileResponses.map((response : any) => response.hash_id)
                                              .filter((hash : string) => hash !== undefined);
    }

    configuration.hooks.forEach(hook => {
      let new_args = {};

      if (hook.hook === "on_upload") {
        new_args = {
          [`${hook.target_route}`]: file_upload_hashes,
        }
      } else if (hook.hook === "selected_collections") {
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
    <FileDropzone onFile={handleSubmission} style={tailwindToObject([configuration.tailwind], breakpoint)}/>
  )
}