"use client";
import { 
  ContextMenuViewportWrapper
} from "./context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
  contentSection,
  alignType
} from "../page";

const large_array = Array(350).fill(0);


export function ContentSection({
	onSplit,
  onCollapse,
  onSectionUpdate,
  sectionInfo = {split: "none", align: "center", mappings: []}
}:{
	onSplit: (split_type : "horizontal" | "vertical" | "header" | "footer", count: number) => void,
  onCollapse: () => void,
  onSectionUpdate: (section : contentSection) => void,
  sectionInfo: contentSection,
}) {

  return (
    <ContextMenuViewportWrapper
			onSplit={onSplit} 
			onCollapse={onCollapse}
			onAlign={(a : alignType) => {
				const new_section = {...sectionInfo, align: a} as contentSection;
				onSectionUpdate(new_section);
			}}
			align={sectionInfo.align}
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
					<div className="w-shrink flex flex-col">
						{large_array.map((_, index) => (
							<div key={index} className="h-[50px]">{index+1}</div>
						))}
					</div>
				</div>
			</ScrollSection>
		</ContextMenuViewportWrapper>
  );
}

