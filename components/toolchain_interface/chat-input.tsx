"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { inputMapping } from "@/types/toolchain-interface";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import ToolchainSession from "@/hooks/toolchain-session";
import {default as ChatInputProto} from "@/registry/default/ui/chat-input";
import { substituteAny } from "@/types/toolchains";
import { useToolchainContextAction } from "@/app/app/context-provider";
import craftUrl from "@/hooks/craftUrl";
import uploadFiles from "@/hooks/upload-files";

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
}:{
	configuration: inputMapping,
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

  const handleSubmission = async (text : string, files: File[]) => {
    const fire_queue : {[key : string]: object}[]= 
    Array(Math.max(...configuration.hooks.map(hook => hook.fire_index))).fill({});
    const collections = Array.from(selectedCollections.keys()).filter((key) => selectedCollections.get(key) === true);
    console.log("ChatInput handleSubmission", text, files, collections, Array.from(selectedCollections.entries()));
    
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

      if (hook.hook === "on_submit") {
        new_args = {
          [`${hook.target_route}`]: text,
        }
      } else if (hook.hook === "on_upload") {
        new_args = {
          [`${hook.target_route}`]: file_upload_hashes,
        }
      } else if (hook.hook === "selected_collections") {
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
    <ChatInputProto 
      style={tailwindToObject([configuration.tailwind], breakpoint)}
      onSubmission={handleSubmission}
    />
  )
}