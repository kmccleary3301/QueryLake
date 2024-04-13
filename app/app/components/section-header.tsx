"use client";
import {
	headerSection
} from "@/types/toolchain-interface";
import DisplayMappings from "./display-mappings";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";
import { substituteAny } from "@/types/toolchains";

export function HeaderSection({
	stateData,
	section = {align: "justify", tailwind: "", mappings: []},
	type = "header"
}:{
	stateData: Map<string, substituteAny>,
	section: headerSection,
	type?: "header" | "footer"
}) {

	const { 
		breakpoint
  } = useContextAction();

	return (
		(typeof section.tailwind === "string") &&
		<div className={`text-center flex flex-row`}>
			
				<div className={`w-full h-full flex flex-row justify-${
					(section.align === "justify") ? "around" :
					(section.align === "left") ?    "start"   :
					(section.align === "center") ?  "center"  :
					"end"
				}`} style={tailwindToObject([section.tailwind], breakpoint)}>
					{(section.mappings.length === 0) && (<p className="select-none">{(type === "header")?"Header":"Footer"}</p>)}

					{section.mappings.map((mapping, index) => (
							// <div key={index} className="h-[50px]">{mapping.display_as}</div>
							<DisplayMappings
								key={index} 
								stateData={stateData}
                info={mapping}
								setInfo={() => {}}
							/>
						))}
				</div>
		</div>
	)
}