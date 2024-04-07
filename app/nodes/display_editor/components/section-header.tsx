"use client";
import { useEffect } from "react"
import {
  ContextMenuHeaderWrapper
} from "./context-menu-wrapper";
import {
	alignType,
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

	useEffect(() => {
		console.log("New Header Tailwind:", sectionInfo.tailwind);
	}, [sectionInfo.tailwind]);

	return (
		(typeof sectionInfo.tailwind === "string") &&
		<div className={`text-center flex flex-row`}>
			<ContextMenuHeaderWrapper 
				onCollapse={onCollapse} 
				onAlign={(a : alignType) => {
					onSectionUpdate({...sectionInfo, align: a})
				}}
				setTailwind={(t : string) => {
					onSectionUpdate({...sectionInfo, tailwind: t} as headerSection)
				}}
				addComponent={(component) => {
					onSectionUpdate({...sectionInfo, mappings: [...sectionInfo.mappings, component]} as headerSection);
				}}
				align={sectionInfo.align}
				tailwind={sectionInfo.tailwind}
			>
				<div className={cn(`w-full h-full border-primary/50 border-[2px] border-dashed flex flex-row justify-${
					(sectionInfo.align === "justify") ? "around" :
					(sectionInfo.align === "left") ?    "start"   :
					(sectionInfo.align === "center") ?  "center"  :
					"end"
				}`, sectionInfo.tailwind)}>
					{(sectionInfo.mappings.length === 0) && (<p className="select-none">{(type === "header")?"Header":"Footer"}</p>)}

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
			</ContextMenuHeaderWrapper>
		</div>
	)
}