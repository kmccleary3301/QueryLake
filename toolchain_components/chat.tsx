"use client";
import { retrieveValueFromObj } from "@/hooks/toolchain-session";
import { Skeleton } from "@/components/ui/skeleton";
import { componentMetaDataType, configEntriesMap, displayMapping } from "@/types/toolchain-interface";
import { Fragment, useEffect, useState } from "react";
import MarkdownRenderer from "@/components/markdown/markdown-renderer";
import { useToolchainContextAction } from "@/app/app/context-provider";
import { useContextAction } from "@/app/context-provider";
import { Button } from "@/components/ui/button";
import { ArrowUpRight, Copy } from "lucide-react";
import { toast } from "sonner";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import Link from "next/link";
import { openDocument } from "@/hooks/querylakeAPI";
import { QueryLakeLogoSvg } from "@/components/logo";
import { MARKDOWN_CHAT_SAMPLE_TEXT } from "@/components/markdown/demo-text";
import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CHAT_RENDERING_STYLE } from "@/components/markdown/configs";
import { textSegment } from "@/components/markdown/markdown-text-splitter";
import { parse } from "path";

export const METADATA : componentMetaDataType = {
  label: "Chat",
  type: "Display",
  category: "Text Display",
  description: "A user and assistant chat display component that renders markdown, similar to OpenAI's ChatGPT."
};

export const DEMO_DATA = [
  {role: "user", "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."},
  {role: "assistant", "content": MARKDOWN_CHAT_SAMPLE_TEXT},
] as chatEntry[];

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

function InlineSource({
  sources,
  textSeg,
  user_auth
}:{
  sources: DocumentEmbeddingDictionary[],
  textSeg: textSegment,
  user_auth: string
}) {
  const parseSourceIndex = parseInt(textSeg.text) - 1;
  
  return (
    <>
      {((!isNaN(parseSourceIndex)) && (parseSourceIndex < sources.length)) ? (
        
        <HoverCard>
          <HoverCardTrigger asChild>
            <span style={{ transform: 'translateY(-2px)', display: 'inline-block', marginLeft: '2px' }}>
              <button className="text-primary/50 hover:text-primary inline-block bg-input rounded-full flex-row justify-center -translate-y-[2px]" style={{
                // paddingLeft: "0.1rem",
                fontSize: "0.65rem",
                height: "18px",
                minWidth: "18px",
              }}>
                <div className="w-auto flex flex-row justify-center">
                  <strong className="p-0 m-0 self-center leading-none">
                    {textSeg.text}
                  </strong>
                </div>
              </button>
            </span>
          </HoverCardTrigger>
          <HoverCardContent className="p-0 max-w-[320px] m-0" side="top">
            <h4 className="px-5 py-4 text-base break-words w-[320px]">
              <span>{sources[parseSourceIndex].document_name}</span>
              <Button variant={"transparent"} className="ml-2 p-0 w-8 h-8" onClick={() => {
                openDocument({
                  auth: user_auth,
                  document_id: sources[parseSourceIndex].document_id as string,
                })
              }}>
                <ArrowUpRight className="w-4 h-4 text-theme-one"/>
              </Button>
            </h4>
            {sources[parseSourceIndex].rerank_score && (
              <p className="text-sm py-3">Relevance Score: {sources[parseSourceIndex].rerank_score?.toFixed(2)}</p>
            )}
            <ScrollArea className="h-[200px] pr-3 px-5">
            {(sources[parseSourceIndex].website_url !== undefined) ? (
              <Link href={sources[parseSourceIndex]?.website_url || ""} rel="noopener noreferrer" target="_blank">
                <Button variant={"ghost"} className="p-2 m-0 h-auto">
                  <div className="max-w-[260px]">
                    <p className="max-w-[260px] text-xs text-primary/50 whitespace-pre-wrap text-left overflow-wrap break-words">{sources[parseSourceIndex].text}</p>
                  </div>
                </Button>
              </Link>
            ):(
                <div className="justify-start pb-[20px]">
                  <div className="opacity-30" style={{marginLeft: "0.1rem" }}> {/* The left pad doesn't render for some reason */}
                    <MarkdownRenderer 
                      className="w-[280px] opacity-5"
                      input={sources[parseSourceIndex].text} 
                      finished={false}
                      config={CHAT_RENDERING_STYLE}
                    />
                    </div>
                </div>
            )}
            </ScrollArea>
          </HoverCardContent>
        </HoverCard>
        
      ):(
        <HoverCard>
          <HoverCardTrigger asChild>
            <span style={{ transform: 'translateY(-2px)', display: 'inline-block' }}>
              <button className="text-primary/50 hover:text-primary inline-block bg-accent rounded-full flex-row justify-center -translate-y-[2px]" style={{
                fontSize: "0.65rem",
                height: "18px",
                minWidth: "18px",
              }}>
                <div className="w-auto flex flex-row justify-center">
                  <strong className="p-0 m-0 self-center leading-none">?</strong>
                </div>
              </button>
            </span>
          </HoverCardTrigger>
          <HoverCardContent className="px-5" side="top">
            <p>Unknown source cited: {textSeg.raw_text}</p>
          </HoverCardContent>
        </HoverCard>
      )}
    </>
  )

}

export default function Chat({
	configuration,
  demo = false,
}:{
	configuration: displayMapping,
  demo?: boolean
}) {
	
	const { toolchainState, toolchainWebsocket } = useToolchainContextAction();
  const { userData } = useContextAction();

	const [currentValue, setCurrentValue] = useState<chatEntry | chatEntry[]>(
    demo ?
    DEMO_DATA :
    retrieveValueFromObj(toolchainState, configuration.display_route) as chatEntry | chatEntry[] || []
	);

	useEffect(() => {
		if (toolchainWebsocket?.current === undefined || demo) return;
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
                  {(value.role === "user") && (
                    <div className={`rounded-full h-7 w-7 bg-primary-foreground text-primary`}>
                    <p className="w-full h-full text-center text-xs flex flex-col justify-center pt-[2px] select-none">
                      {userData?.username.slice(0, Math.min(2, userData?.username.length)).toUpperCase()}
                    </p>
                    </div>
                  )}

                  {(value.role === "assistant") && (
                    <div className="mt-1">
                      <QueryLakeLogoSvg className="w-7 h-7 text-primary"/>
                    </div>
                  )}
                  
                    
                </div>
                <p className="select-none h-7 text-primary/70">{(value.role === "user")?"You":"QueryLake"}</p>
              </div>
              <div className={cn("max-w-full -mt-1.5")} style={{marginLeft: "2.75rem"}}> {/* The left pad doesn't render for some reason */}
                <MarkdownRenderer 
                  className="ml-11"
                  disableRender={(value.role === "user")}
                  input={(value || {}).content || ""} 
                  finished={false}
                  config={{
                    ...CHAT_RENDERING_STYLE,
                    citation: (textSeg: textSegment) => (
                      <InlineSource
                        sources={(value || {}).sources || []}
                        textSeg={textSeg}
                        user_auth={userData?.auth as string}
                      />
                    )
                  }}
                />
              </div>
              {(value.role === "assistant" && value.sources) && (
                <div className="w-full flex flex-wrap gap-3 pl-11 pt-2" style={{marginLeft: "2.75rem"}}>
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
                      <HoverCardContent className="px-5 max-w-[320px]" side="top">
                        <h1 className="text-base">{source.document_name}</h1>
                        {source.rerank_score && (
                          <p className="text-sm py-3">Relevance Score: {source.rerank_score.toFixed(2)}</p>
                        )}
                        <ScrollArea className="h-[200px] pr-3">
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
                        </ScrollArea>
                      </HoverCardContent>
                    </HoverCard>
                  ))}
                </div>
              )}
              {(value.role === "assistant") && (
                <div className="w-full flex flex-row pl-11 pt-2" style={{marginLeft: "2.75rem"}}>
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