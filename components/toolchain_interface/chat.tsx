"use client";
import { retrieveValueFromObj } from "@/hooks/toolchain-session";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { displayMapping } from "@/types/toolchain-interface";
import { Fragment, useEffect, useState } from "react";
import MarkdownRenderer from "../markdown/markdown-renderer";
import { useToolchainContextAction } from "@/app/app/context-provider";
import { useContextAction } from "@/app/context-provider";
import { Button } from "@/registry/default/ui/button";
import { Copy } from "lucide-react";
import { toast } from "sonner";

export function ChatSkeleton({
	configuration
}:{
	configuration: displayMapping
}) {
  return (
		<div className="flex flex-row space-x-4 w-auto">
			<div>
				<Skeleton className="rounded-full w-10 h-10"/>
			</div>
			<div className="flex-grow flex flex-col space-y-3">
				{Array(10).fill(0).map((_, i) => (
					<Skeleton key={i} className="rounded-full w-auto h-3"/>
				))}
			</div>
		</div>
	);
}

export type DocumentEmbeddingDictionary = {
	id: string;
	document_name: string;
	private: boolean;
	text: string;
} & (
	{
		collection_type: string;
		document_id: string;
		document_chunk_number: number;
		document_integrity: string;
		parent_collection_hash_id: string;
	} | {
		website_url: string;
	}
) & (
	{ headline: string; cover_density_rank: number; } | {}
) & (
	{ rerank_score: number; } | {}
)

export type chatInput = {
	role: "user" | "assistant",
	content: string,
	sources?: DocumentEmbeddingDictionary[]
}[]

export default function Chat({
	configuration
}:{
	configuration: displayMapping
}) {
	
	const { toolchainState, toolchainWebsocket } = useToolchainContextAction();
  const { userData } = useContextAction();

	const [currentValue, setCurrentValue] = useState<chatInput>(
		retrieveValueFromObj(toolchainState, configuration.display_route) as chatInput || []
	);

	// useEffect(() => {
	// 	console.log("Chat currentValue", JSON.parse(JSON.stringify(currentValue)));
	// }, [toolchainState]);

	// useEffect(() => {console.log("Rerendering chat")}, []);

	useEffect(() => {
		if (toolchainWebsocket?.current === undefined) return;
    const newValue = retrieveValueFromObj(toolchainState, configuration.display_route) as chatInput || [];
    // console.log("Chat newValue", JSON.parse(JSON.stringify(newValue)));
		setCurrentValue(newValue);
	}, [toolchainState]);

  const handleCopy = (text : string) => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.navigator.clipboard.writeText(text);
      toast("Copied to clipboard");
    } catch (err) {
      toast("Failed to copy to clipboard");
    }
  };

  return (
		<div className="flex flex-col gap-6 pb-2">
			{currentValue.map((value, index) => (
        <div className="flex flex-col gap-0" key={index}>
          <div key={index} className="flex flex-row">
            <div className="w-11 h-8 pt-1">
              <div className={`rounded-full h-7 w-7 ${(value.role === "user")?"bg-red-500":"bg-green-500"}`}>
                <p className="w-full h-full text-center text-xs flex flex-col justify-center pt-[2px] select-none">
                  {userData?.username.slice(0, Math.max(2, userData?.username.length)).toUpperCase()}
                </p>
              </div>
            </div>
            {/* <div className="border-[2px] border-green-500 h-[50px] w-[1200px]"/> */}
            {/* <div className="flex-1 flex flex-col h-auto justify-start pt-1">
              <div className={`rounded-full h-7 w-7 ${(value.role === "user")?"bg-red-500":"bg-green-500"}`}>
                <p className="w-full h-full text-center text-xs flex flex-col justify-center pt-[2px] select-none">
                  {userData?.username.slice(0, Math.max(2, userData?.username.length)).toUpperCase()}
                </p>
              </div>
            </div> */}
            {/* <div className="flex flex-col space-y-1"> */}
            <p className="select-none h-7 text-primary/70"><strong>{(value.role === "user")?"You":"QueryLake"}</strong></p>
            {/* </div> */}
          </div>
          <div className="max-w-full p-0 pl-11 -mt-2">
            <MarkdownRenderer 
              disableRender={(value.role === "user")}
              input={(value || {}).content || ""} 
              finished={false}
            />
          </div>
          {(value.role === "assistant") && (
            <div className="w-full flex flex-row pl-11 pt-2">
              <Button variant={"ghost"} className="rounded-full p-0 h-8 w-8" onClick={() => handleCopy((value || {}).content || "")}>
                <Copy className="w-4 h-4 text-primary"/>
              </Button>

            </div>
          )}
        </div>
			))}
		</div>
	);
}