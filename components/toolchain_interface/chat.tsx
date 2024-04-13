"use client";
import { retrieveValueFromObj } from "@/hooks/toolchain-session";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { displayMapping } from "@/types/toolchain-interface";
import { substituteAny } from "@/types/toolchains";
import { useEffect, useState } from "react";
import MarkdownRenderer from "../markdown/markdown-renderer";

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
	configuration,
	toolchainState
}:{
	configuration: displayMapping,
	toolchainState: Map<string, substituteAny>
}) {
	const [currentValue, setCurrentValue] = useState<chatInput>(
		retrieveValueFromObj(toolchainState, configuration.display_route) as chatInput || []
	);

	useEffect(() => {
    const newValue = retrieveValueFromObj(toolchainState, configuration.display_route) as chatInput || [];
    console.log("Chat newValue", newValue);
		setCurrentValue(newValue);
	}, [toolchainState]);


  return (
		<div className="w-auto flex flex-col gap-y-2 border-[2px] border-red-500 min-h-[50px]">
			{currentValue.map((value, index) => (

				<div key={index} className="w-auto flex flex-row gap-x-2">
					<div className="rounded-full h-10 w-10 bg-primary/50"/>
					<MarkdownRenderer input={value.content} finished={false}/>
				</div>
			))}
		</div>
	);
}