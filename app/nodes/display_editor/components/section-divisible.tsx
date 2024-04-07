"use client";
import { Dispatch, SetStateAction, useState, Fragment } from "react"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/registry/default/ui/resizable"
import { 
  ContextMenuViewportWrapper
} from "./context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import {
	divisionSection,
	headerSection,
	displaySection,
  contentSection,
  alignType
} from "@/types/toolchain-interface";
import { HeaderSection } from "./section-header";
import { ContentSection } from "./section-content";

const large_array = Array(350).fill(0);


export function DivisibleSection({
  onCollapse,
  onSectionUpdate,
  windowNumber,
  currentWindowCount,
  setCurrentWindowCount,
  sectionInfo = {split: "none", align: "center", tailwind: "", mappings: []}
}:{
  onCollapse: () => void,
  onSectionUpdate: (section : displaySection) => void,
  windowNumber: number,
  currentWindowCount: number,
  setCurrentWindowCount: Dispatch<SetStateAction<number>>,
  sectionInfo: displaySection,
}) {

  // const [section, setSection] = useState<displaySection>(sectionInfo);

  const onSplit = (splitType : "horizontal" | "vertical" | "header" | "footer", count: number) => {
    if (splitType == "horizontal" || splitType == "vertical") {
      let sections_array : contentSection[] = Array(count).fill({
        split: "none",
        align: "center",
        mappings: []
      });
      
      sections_array[0] = JSON.parse(JSON.stringify(sectionInfo)) as contentSection;
      sections_array[0].header = undefined;
      sections_array[0].footer = undefined;


      const { mappings, ...sectionInfoReduced } = sectionInfo as contentSection;

      const new_section : divisionSection = {
        ...sectionInfoReduced,
        split: splitType as "horizontal" | "vertical",
        sections: sections_array
      }
      // setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "header") {
      const new_section : displaySection = {
        ...sectionInfo,
        header: {
          align: "justify",
          tailwind: "",
          mappings: []
        }
      }
      // setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "footer") {
      const new_section : displaySection = {
        ...sectionInfo,
        footer: {
          align: "justify",
          tailwind: "",
          mappings: []
        }
      }
      // setSection(new_section);
      onSectionUpdate(new_section);
    }
  }

  const resetSection = (index : "header" | "footer" | number) => {
		if (index === "header") {
			const { header, ...new_section } = sectionInfo;
			// setSection(new_section);
			onSectionUpdate(new_section);
		} 
		else if (index === "footer") {
			const { footer, ...new_section } = sectionInfo;
			// setSection(new_section);
			onSectionUpdate(new_section);
		}
    else {

      if (sectionInfo.split === "none") return;
			
      const { sections, ...new_section_one } = sectionInfo;
			if (sections.length === 2) {
				const new_section : displaySection = {...new_section_one, ...sections[(index + 1) % 2]};
				// setSection(new_section);
				onSectionUpdate(new_section);
			} else {
				const new_section : divisionSection = {
					...new_section_one,
					sections: [
						...sections.slice(0, index),
						...sections.slice(index + 1)
					]
				}
				// setSection(new_section);
				onSectionUpdate(new_section);
			}
    }
  }

  const PrimaryContent = () => (
    <>
      {(sectionInfo.split === "none" && (sectionInfo as contentSection)) ? (
        <ContentSection
          onSplit={onSplit}
          onCollapse={onCollapse}
          onSectionUpdate={(sectionLocal) => {
            // setSection(sectionLocal);
            onSectionUpdate(sectionLocal);
          }}
          sectionInfo={sectionInfo as contentSection}
        />
      ):(
        <ResizablePanelGroup direction={(sectionInfo as divisionSection).split}>

          {(sectionInfo as divisionSection).sections.map((split_section, index) => (
            <Fragment key={index}>
              <ResizablePanel defaultSize={100/(sectionInfo as divisionSection).sections.length}>
                <DivisibleSection
                  onCollapse={() => {resetSection(index)}}
                  onSectionUpdate={(sectionLocal) => {
                    //TODO Problem probably originates here.

                    // let new_section = sectionInfo as divisionSection;
                    // new_section.sections[index] = sectionLocal;
                    // setSection(new_section);
                    onSectionUpdate({...(sectionInfo as divisionSection), sections: [
                      ...(sectionInfo as divisionSection).sections.slice(0, index),
                      sectionLocal,
                      ...(sectionInfo as divisionSection).sections.slice(index+1)
                    ]});
                  }}
                  windowNumber={windowNumber}
                  currentWindowCount={currentWindowCount}
                  setCurrentWindowCount={setCurrentWindowCount}
                  sectionInfo={split_section}
                />
              </ResizablePanel>
              {(index < (sectionInfo as divisionSection).sections.length - 1) && (
                <ResizableHandle/>
              )}
            </Fragment>
          ))}
        </ResizablePanelGroup>
      )}
    </>
  );


  return (
    <>
    {(sectionInfo.header !== undefined || sectionInfo.footer !== undefined) ? (
      <ResizablePanelGroup direction="vertical">
        {(sectionInfo.header !== undefined) && (
          <HeaderSection 
            onCollapse={() => {resetSection("header")}} 
            onSectionUpdate={(s : headerSection) => {

              // TODO: If it breaks, it's probably this
              onSectionUpdate({...sectionInfo, header: s});
            }} 
            sectionInfo={sectionInfo.header}
          />
        )}
        <ResizablePanel defaultSize={100} >
          <PrimaryContent />
        </ResizablePanel>
        {(sectionInfo.footer !== undefined) && (
          <HeaderSection 
            onCollapse={() => {resetSection("footer")}} 
            onSectionUpdate={(s : headerSection) => {
              onSectionUpdate({...sectionInfo, footer: s});
            }} 
            sectionInfo={sectionInfo.footer}
            type="footer"
          />
        )}
      </ResizablePanelGroup>
    ) : (
      <PrimaryContent />
    )}
    </>
  );
}

