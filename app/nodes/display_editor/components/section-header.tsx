"use client";
import { useEffect } from "react"
import {
  ContextMenuHeaderWrapper
} from "./context-menu-wrapper";
import {
	alignType,
	headerSection
} from "../page";

export function HeaderSection({
	onCollapse,
	onSectionUpdate,
	sectionInfo = {align: "justify", mappings: []}
}:{
	onCollapse: () => void,
	onSectionUpdate: (section : headerSection) => void,
	sectionInfo: headerSection,
}) {

	return (
		<div className={`text-center flex flex-row`}>
			<ContextMenuHeaderWrapper 
				onCollapse={onCollapse} 
				onAlign={(a : alignType) => {
					onSectionUpdate({...sectionInfo, align: a})
				}}
				align={sectionInfo.align}
			>
				<div className={`w-full h-full border-red-500 border-[2px] flex flex-row justify-${
					(sectionInfo.align === "justify") ? "around" :
					(sectionInfo.align === "left") ?    "start"   :
					(sectionInfo.align === "center") ?  "center"  :
					"end"
				}`}>
					Header
				</div>
			</ContextMenuHeaderWrapper>
		</div>
	)
}