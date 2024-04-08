"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { displayMapping } from "@/types/toolchain-interface";

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

export interface DocumentEmbeddingDictionary {
	id: string;
	collection_type?: string;
	document_id?: string;
	document_integrity?: string;
	parent_collection_hash_id?: string;
	document_name: string;
	website_url?: string;
	private: boolean;
	text: string;
	headline?: string;
	cover_density_rank?: number;
	rerank_score?: number;
}

export type chatInput = {
	role: "user" | "assistant",
	content: string,
	sources?: string[]
}[]

export default function Chat({
	configuration,
	value
}:{
	configuration: displayMapping,
	value: chatInput
}) {
    
}