"use client";
import { toolchainStateType } from "@/hooks/toolchain-session";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { componentMetaDataType, displayMapping } from "@/types/toolchain-interface";
import { substituteAny } from "@/types/toolchains";

export const METADATA : componentMetaDataType = {
	label: "Markdown",
	category: "Text Display",
	description: "Displays text as markdown.",
};

export function SKELETON({
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
	configuration,
	toolchainState
}:{
	configuration: displayMapping,
	toolchainState: toolchainStateType
}) {
  
  return (
    <>
    </>
  );
}