"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { displayMapping } from "@/types/toolchain-interface";

export function MarkdownSkeleton({
	configuration
}:{
	configuration: displayMapping
}) {
	return (
		<div className="flex-grow flex flex-col space-y-3">
			{Array(10).fill(0).map((_, i) => (
				<Skeleton key={i} className="rounded-full w-auto h-3"/>
			))}
		</div>
	);
}


export default function Markdown({
	configuration
}:{
	configuration: displayMapping
}) {
    
}