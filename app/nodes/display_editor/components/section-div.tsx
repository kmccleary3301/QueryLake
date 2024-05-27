"use client";
import { 
  ContextMenuViewportWrapper
} from "./context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
  contentSection,
  contentDiv,
  alignType,
	contentMapping
} from "@/types/toolchain-interface";
import DisplayMappings from "./display-mappings";
import { useState, useRef, Fragment } from "react";
// import tailwindToStyle from "@/hooks/tailwind-to-obj/tailwind-to-style-obj";
import tailwindToObject from "@/hooks/tailwind-to-obj/tailwind-to-style-obj-imported";
import { useContextAction } from "@/app/context-provider";

export function ContentDiv({
	onSplit,
  onCollapse, // Delete this section
  onSectionUpdate,
  sectionInfo = {type: "div", align: "center", tailwind: "min-w-[20px] min-h-[20px]", mappings: []}
}:{
	onSplit: (split_type : "horizontal" | "vertical" | "header" | "footer", count: number) => void,
  onCollapse: () => void,
  onSectionUpdate: (section : contentDiv) => void,
  sectionInfo: contentDiv,
}) {
	
	const { 
		breakpoint
  } = useContextAction();

	const [section, setSection] = useState<contentDiv>(sectionInfo);
	const sectionRef = useRef<contentDiv>(sectionInfo);

	const updateSectionUpstream = (sectionLocal : contentDiv) => {
    sectionRef.current = JSON.parse(JSON.stringify(sectionLocal));
    onSectionUpdate(sectionRef.current);
  }

  const updateSection = (sectionLocal : contentDiv) => {
    setSection(sectionLocal);
    updateSectionUpstream(sectionLocal);
  }

	// useEffect(() => {console.log(cn(section.tailwind, "flex flex-col"))}, [section.tailwind]);

  return (
    <div onContextMenu={(e) => {e.preventDefault(); e.stopPropagation()}}>
      <ContextMenuViewportWrapper
        onSplit={onSplit} 
        onCollapse={onCollapse}
        onAlign={(a : alignType) => {
          updateSection({...section, align: a} as contentDiv);
        }}
        setTailwind={(t : string) => {
          updateSection({...section, tailwind: t} as contentDiv);
        }}
        addComponent={(component) => {
          updateSection({...section, mappings: [...section.mappings, component]} as contentDiv);
        }}
        align={section.align}
        tailwind={section.tailwind}
        headerAvailable={false}
        footerAvailable={false}
      >
        <div className="border-2 border-dashed border-red-500" style={tailwindToObject([section.tailwind], breakpoint)}>
          <div className={`flex flex-row justify-${
            (section.align === "justify") ? "around" :
            (section.align === "left") ?    "start"   :
            (section.align === "center") ?  "center"  :
            "end"
          }`}>
            <div style={tailwindToObject(["flex flex-col", section.tailwind], breakpoint)}>
              {section.mappings.map((mapping, index) => (
                <Fragment key={index}>
                  {((mapping as contentDiv).type && (mapping as contentDiv).type === "div") ? (
                    <ContentDiv
                      onSplit={onSplit}
                      onCollapse={() => {updateSection({
                        ...section, 
                        mappings: [...section.mappings.slice(0, index), ...section.mappings.slice(index+1)]
                      } as contentDiv)}}
                      onSectionUpdate={(value : contentDiv) => {
                        updateSection({
                          ...section, 
                          mappings: [...section.mappings.slice(0, index), value, ...section.mappings.slice(index+1)]
                        } as contentDiv);
                      }}
                      sectionInfo={mapping as contentDiv}
                    />
                  ) : (
                    <DisplayMappings
                      info={mapping as contentMapping}
                      onDelete={() => {updateSection({
                        ...section, 
                        mappings: [...section.mappings.slice(0, index), ...section.mappings.slice(index+1)]
                      } as contentDiv)}}
                      setInfo={(value : contentMapping) => {
                        updateSection({
                          ...section, 
                          mappings: [...section.mappings.slice(0, index), value, ...section.mappings.slice(index+1)]
                        } as contentDiv);
                      }}
                    />

                  )}
                </Fragment>
              ))}
            </div>
          </div>
        </div>
      </ContextMenuViewportWrapper>
    </div>
  );
}

