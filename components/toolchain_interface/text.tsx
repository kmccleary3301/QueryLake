"use client";
import { toolchainStateType } from "@/hooks/toolchain-session";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { componentMetaDataType, displayMapping } from "@/types/toolchain-interface";
import { substituteAny } from "@/types/toolchains";

export const METADATA : componentMetaDataType = {
  label: "Text",
  category: "Text Display",
  description: "Displays text as-is, without rendering it as markdown or processing it in any way.",
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


export default function Text({
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