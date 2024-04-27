"use client";
import { 
  ContextMenuViewportWrapper
} from "./context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
  contentSection,
  alignType,
	contentMapping
} from "@/types/toolchain-interface";
import DisplayMappings from "./display-mappings";
import { useState, useRef } from "react";
// import tailwindToStyle from "@/hooks/tailwind-to-obj/tailwind-to-style-obj";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";

export function ContentSection({
	onSplit,
  onCollapse,
  onSectionUpdate,
  sectionInfo = {split: "none", size: 100, align: "center", tailwind: "", mappings: []}
}:{
	onSplit: (split_type : "horizontal" | "vertical" | "header" | "footer", count: number) => void,
  onCollapse: () => void,
  onSectionUpdate: (section : contentSection) => void,
  sectionInfo: contentSection,
}) {
	
	const { 
		breakpoint
  } = useContextAction();

	const [section, setSection] = useState<contentSection>(sectionInfo);
	const sectionRef = useRef<contentSection>(sectionInfo);

	const updateSectionUpstream = (sectionLocal : contentSection) => {
    sectionRef.current = JSON.parse(JSON.stringify(sectionLocal));
    onSectionUpdate(sectionRef.current);
  }

  const updateSection = (sectionLocal : contentSection) => {
    setSection(sectionLocal);
    updateSectionUpstream(sectionLocal);
  }

	// useEffect(() => {console.log(cn(section.tailwind, "flex flex-col"))}, [section.tailwind]);

  return (
    <ContextMenuViewportWrapper
			onSplit={onSplit} 
			onCollapse={onCollapse}
			onAlign={(a : alignType) => {
				updateSection({...section, align: a} as contentSection);
			}}
			setTailwind={(t : string) => {
				updateSection({...section, tailwind: t} as contentSection);
			}}
			addComponent={(component) => {
				updateSection({...section, mappings: [...section.mappings, component]} as contentSection);
			}}
			align={section.align}
			tailwind={section.tailwind}
			headerAvailable={(section.header === undefined)}
			footerAvailable={(section.footer === undefined)}
		>
			<ScrollSection scrollBar={true} scrollToBottomButton={true} innerClassName={`w-full`}>
				<div className={`flex flex-row justify-${
					(section.align === "justify") ? "around" :
					(section.align === "left") ?    "start"   :
					(section.align === "center") ?  "center"  :
					"end"
				}`}>
					<div style={
						tailwindToObject(["flex flex-col", section.tailwind], breakpoint)
					}>
						{section.mappings.map((mapping, index) => (
							<DisplayMappings 
								key={index} 
								info={mapping}
								onDelete={() => {updateSection({
									...section, 
									mappings: [...section.mappings.slice(0, index), ...section.mappings.slice(index+1)]
								} as contentSection)}}
								setInfo={(value : contentMapping) => {
									updateSection({
										...section, 
										mappings: [...section.mappings.slice(0, index), value, ...section.mappings.slice(index+1)]
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

