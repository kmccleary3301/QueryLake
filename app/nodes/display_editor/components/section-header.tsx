"use client";
import { useEffect, useRef, useState } from "react"
import {
  ContextMenuHeaderWrapper
} from "./context-menu-wrapper";
import {
	alignType,
	contentMapping,
	contentSection,
	headerSection
} from "@/types/toolchain-interface";
import { cn } from "@/lib/utils";
import DisplayMappings from "./display-mappings";

export function HeaderSection({
	onCollapse,
	onSectionUpdate,
	sectionInfo = {align: "justify", tailwind: "", mappings: []},
	type = "header"
}:{
	onCollapse: () => void,
	onSectionUpdate: (section : headerSection) => void,
	sectionInfo: headerSection,
	type?: "header" | "footer"
}) {
	const [section, setSection] = useState<headerSection>(sectionInfo);
	const sectionRef = useRef<headerSection>(sectionInfo);

	const updateSectionUpstream = (sectionLocal : headerSection) => {
    sectionRef.current = JSON.parse(JSON.stringify(sectionLocal));
    onSectionUpdate(sectionRef.current);
  }

  const updateSection = (sectionLocal : headerSection) => {
    setSection(sectionLocal);
    updateSectionUpstream(sectionLocal);
  }


	useEffect(() => {
		console.log("New Header Tailwind:", sectionInfo.tailwind);
	}, [sectionInfo.tailwind]);

	return (
		(typeof sectionInfo.tailwind === "string") &&
		<div className={`text-center flex flex-row`}>
			<ContextMenuHeaderWrapper 
				onCollapse={onCollapse} 
				onAlign={(a : alignType) => {
					updateSection({...section, align: a})
				}}
				setTailwind={(t : string) => {
					updateSection({...section, tailwind: t} as headerSection)
				}}
				addComponent={(component) => {
					updateSection({...section, mappings: [...section.mappings, component]} as headerSection);
				}}
				align={section.align}
				tailwind={section.tailwind}
			>
				<div className={cn(`w-full h-full border-primary/50 border-[2px] border-dashed flex flex-row justify-${
					(section.align === "justify") ? "around" :
					(section.align === "left") ?    "start"   :
					(section.align === "center") ?  "center"  :
					"end"
				}`, section.tailwind)}>
					{(section.mappings.length === 0) && (<p className="select-none">{(type === "header")?"Header":"Footer"}</p>)}

					{section.mappings.map((mapping, index) => (
							// <div key={index} className="h-[50px]">{mapping.display_as}</div>
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
			</ContextMenuHeaderWrapper>
		</div>
	)
}