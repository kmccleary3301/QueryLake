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
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/registry/default/ui/hover-card";
import Link from "next/link";
import { openDocument } from "@/hooks/querylakeAPI";

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

type documentEmbeddingSpecialFields1 ={
  collection_type: string;
  document_id: string;
  document_chunk_number: number;
  document_integrity: string;
  parent_collection_hash_id: string;
} | {
  website_url: string;
}
type documentEmbeddingSpecialFields2 = { headline: string; cover_density_rank: number; } | {}
type documentEmbeddingSpecialFields3 = { rerank_score: number; } | {}

export type DocumentEmbeddingDictionary = {
	id: string;
	document_name: string;
	private: boolean;
	text: string;
  website_url?: string;
  rerank_score?: number;
  document_id?: string;
} & documentEmbeddingSpecialFields1 & documentEmbeddingSpecialFields2 & documentEmbeddingSpecialFields3

export type chatEntry = {
	role?: "user" | "assistant",
	content: string,
	sources?: DocumentEmbeddingDictionary[]
}

export default function Chat({
	configuration
}:{
	configuration: displayMapping
}) {
	
	const { toolchainState, toolchainWebsocket } = useToolchainContextAction();
  const { userData } = useContextAction();

	const [currentValue, setCurrentValue] = useState<chatEntry | chatEntry[]>(
		retrieveValueFromObj(toolchainState, configuration.display_route) as chatEntry | chatEntry[] || []
	);



	useEffect(() => {
    // console.log("DISPLAY ROUTE:", configuration.display_route);
    console.log("Toolchain State:", toolchainState);
		if (toolchainWebsocket?.current === undefined) return;
    const newValue = retrieveValueFromObj(toolchainState, configuration.display_route) as chatEntry | chatEntry[] || [];
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
    <>
      {currentValue && (
        <div className="flex flex-col gap-8 pb-2">
          {(Array.isArray(currentValue)?currentValue:[currentValue]).map((value, index) => (
            <div className="flex flex-col gap-0" key={index}>
              <div key={index} className="flex flex-row">
                <div className="w-11 h-8 pt-[5px]">
                  <div className={`rounded-full h-7 w-7 ${(value.role === "user")?"bg-red-500":"border-teal-500 border-[2px]"}`}>
                    {(value.role === "user") && (
                      <p className="w-full h-full text-center text-xs flex flex-col justify-center pt-[2px] select-none">
                        {userData?.username.slice(0, Math.min(2, userData?.username.length)).toUpperCase()}
                      </p>

                    )}
                  </div>
                </div>
                <p className="select-none h-7 text-primary/70">{(value.role === "user")?"You":"QueryLake"}</p>
              </div>
              <div className="max-w-full p-0 pl-11 -mt-1.5">
                <MarkdownRenderer 
                  disableRender={(value.role === "user")}
                  input={(value || {}).content || ""} 
                  finished={false}
                />
              </div>
              {(value.role === "assistant" && value.sources) && (
                <div className="w-full flex flex-wrap gap-3 pl-11 pt-2">
                  {value.sources.map((source, index) => (
                    <HoverCard key={index}>
                    <HoverCardTrigger asChild>
                      <div
                        className={`rounded-xl px-2 max-w-[120px] h-8 bg-background border-[2px] flex flex-col justify-center`}
                        style={{
                          borderColor: source.website_url ? 
                              `rgba(0, 220, 0, ${(source.rerank_score !== undefined)? (0.5 + 0.5*source.rerank_score/100).toString(): '0.5'})` : 
                              `rgba(220, 0, 0, ${(source.rerank_score !== undefined)? (0.5 + 0.5*source.rerank_score/100).toString(): '0.5'})`
                        }}>
                        <p className="text-primary text-sm whitespace-nowrap overflow-hidden text-ellipsis">{source.document_name}</p>
                      </div>
                    </HoverCardTrigger>
                    <HoverCardContent className="px-5 max-w-[320px]">
                      <h1 className="text-base">{source.document_name}</h1>
                      {source.rerank_score && (
                        <p className="text-sm py-3">Relevance Score: {source.rerank_score.toFixed(2)}</p>
                      )}
                      {(source.website_url) ? (
                        <Link href={source.website_url} rel="noopener noreferrer" target="_blank">
                          <Button variant={"ghost"} className="p-2 m-0 h-auto">
                            <div className="max-w-[260px]">
                              <p className="max-w-[260px] text-xs text-primary/50 whitespace-pre-wrap text-left overflow-wrap break-words">{source.text}</p>
                            </div>
                          </Button>
                        </Link>
                      ):(
                        <Button variant={"ghost"} className="p-2 m-0 h-auto" onClick={()=>{
                          openDocument({
                            auth: userData?.auth as string,
                            document_id: source?.document_id as string,
                          })
                        }}>
                          <div className="max-w-[260px]">
                            <p className="max-w-[260px] text-xs text-primary/50 whitespace-normal text-left overflow-wrap break-word">{source.text}</p>
                          </div>
                        </Button>
                      )}
                    </HoverCardContent>
                  </HoverCard>
                  ))}
                </div>
              )}
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
      )}
    </>
	);
}