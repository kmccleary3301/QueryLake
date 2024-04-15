"use client";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
  contentSection
} from "@/types/toolchain-interface";
import DisplayMappings from "./display-mappings";
// import tailwindToStyle from "@/hooks/tailwind-to-obj/tailwind-to-style-obj";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import { substituteAny } from "@/types/toolchains";
import { useEffect } from "react";

export function ContentSection({
  section
}:{
  section: contentSection,
}) {
	const { 
		breakpoint
  } = useContextAction();

  useEffect(() => {console.log("Rerendering")}, []);

  return (
    <div className="w-full h-full">
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
							/>
						))}
					</div>
				</div>
			</ScrollSection>
    </div>
  );
}

