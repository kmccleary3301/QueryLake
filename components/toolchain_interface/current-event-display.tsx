"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { displayMapping } from "@/types/toolchain-interface";
import { useToolchainContextAction } from "@/app/app/context-provider";
import BounceLoader from "react-spinners/BounceLoader";

export function CurrentEventDisplaySkeleton({
	configuration
}:{
	configuration: displayMapping
}) {
  return (
    <div className="w-auto h-11 flex flex-row justify-center gap-2">
      <Skeleton className="rounded-full w-[200px] h-10"/>
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
} & documentEmbeddingSpecialFields1 & documentEmbeddingSpecialFields2 & documentEmbeddingSpecialFields3

export type chatEntry = {
	role?: "user" | "assistant",
	content: string,
	sources?: DocumentEmbeddingDictionary[]
}

export default function CurrentEventDisplay({
	configuration
}:{
	configuration: displayMapping
}) {
	
	const { currentEvent } = useToolchainContextAction();

  return (
    <>
      {(currentEvent !== undefined) && (
        <div className="w-auto h-11 flex flex-row justify-center gap-2">
          <div className="h-auto flex flex-col justify-center">
            <div className="">
              <BounceLoader size={20} color="rgb(20 184 166)" className="h-2 w-2 text-primary"/>
            </div>
          </div>
          <p className="h-auto flex flex-col justify-center">Running Event Node: {currentEvent}</p>
        </div>
      )}
    </>
	);
}