"use client";
import { 
  ContextMenuViewportWrapper
} from "./context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
  contentSection,
  alignType
} from "@/types/toolchain-interface";
import { cn } from "@/lib/utils";
import DisplayMappings from "./display-mappings";
import { useEffect } from "react";

const large_array = Array(350).fill(0);

export function ContentSection({
	onSplit,
  onCollapse,
  onSectionUpdate,
  sectionInfo = {split: "none", align: "center", tailwind: "", mappings: []}
}:{
	onSplit: (split_type : "horizontal" | "vertical" | "header" | "footer", count: number) => void,
  onCollapse: () => void,
  onSectionUpdate: (section : contentSection) => void,
  sectionInfo: contentSection,
}) {
	useEffect(() => {console.log(cn(sectionInfo.tailwind, "flex flex-col"))}, [sectionInfo.tailwind]);


  return (
    <ContextMenuViewportWrapper
			onSplit={onSplit} 
			onCollapse={onCollapse}
			onAlign={(a : alignType) => {
				onSectionUpdate({...sectionInfo, align: a} as contentSection);
			}}
			setTailwind={(t : string) => {
				onSectionUpdate({...sectionInfo, tailwind: t} as contentSection);
			}}
			addComponent={(component) => {
				onSectionUpdate({...sectionInfo, mappings: [...sectionInfo.mappings, component]} as contentSection);
			}}
			align={sectionInfo.align}
			tailwind={sectionInfo.tailwind}
			headerAvailable={(sectionInfo.header === undefined)}
			footerAvailable={(sectionInfo.footer === undefined)}
		>
			<ScrollSection scrollBar={true} scrollToBottomButton={true} innerClassName={`w-full`}>
				<div className={`flex flex-row justify-${
					(sectionInfo.align === "justify") ? "around" :
					(sectionInfo.align === "left") ?    "start"   :
					(sectionInfo.align === "center") ?  "center"  :
					"end"
				}`}>
					<div className={cn("flex flex-col", sectionInfo.tailwind)}>
						{/* {large_array.map((_, index) => (
							<div key={index} className="h-[50px]">{index+1}</div>
						))} */}
						{sectionInfo.mappings.map((mapping, index) => (
							// <div key={index} className="h-[50px]">{mapping.display_as}</div>
							<DisplayMappings 
								key={index} 
								info={mapping}
								onDelete={() => {onSectionUpdate({
									...sectionInfo, 
									mappings: [...sectionInfo.mappings.slice(0, index), ...sectionInfo.mappings.slice(index+1)]
								} as contentSection)}}
								onRouteSet={(route : (string | number)[]) => {
									onSectionUpdate({
										...sectionInfo, 
										mappings: [...sectionInfo.mappings.slice(0, index), {...mapping, display_route: route}, ...sectionInfo.mappings.slice(index+1)]
									} as contentSection);
								}}
							/>
						))}
					</div>
				</div>
			</ScrollSection>
		</ContextMenuViewportWrapper>
  );
}

