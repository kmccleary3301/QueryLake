"use client";
import { Dispatch, SetStateAction, useState } from "react"
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
	displaySection
} from "../page";
import { HeaderSection } from "./section-header";

const large_array = Array(350).fill(0);


export function DivisibleSection({
  onCollapse,
  onSectionUpdate,
  windowNumber,
  currentWindowCount,
  setCurrentWindowCount,
  sectionInfo = {split: "none", mappings: []}
}:{
  onCollapse: () => void,
  onSectionUpdate: (section : displaySection) => void,
  windowNumber: number,
  currentWindowCount: number,
  setCurrentWindowCount: Dispatch<SetStateAction<number>>,
  sectionInfo: displaySection,
}) {

  const [section, setSection] = useState<displaySection>(sectionInfo);

  const onSplit = (splitType : "horizontal" | "vertical" | "header" | "footer", count: number) => {
    if (splitType == "horizontal" || splitType == "vertical") {
      const new_section : divisionSection = {
        ...section,
        split: splitType as "horizontal" | "vertical",
        sections: Array(count).fill({
          split: "none",
          mappings: []
        })
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "header") {
      const new_section : displaySection = {
        ...section,
        header: {
          // split: "none",
          align: "justify",
          mappings: []
        }
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "footer") {
      const new_section : displaySection = {
        ...section,
        footer: {
          align: "justify",
          mappings: []
        }
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    }
  }

  const resetSection = (index : "header" | "footer" | number) => {
		if (index === "header") {
			const { header, ...new_section } = section;
			setSection(new_section);
			onSectionUpdate(new_section);
		} 
		else if (index === "footer") {
			const { footer, ...new_section } = section;
			setSection(new_section);
			onSectionUpdate(new_section);
		}
    else {

      if (section.split === "none") return;
			
      const { sections, ...new_section_one } = section;
			if (sections.length === 2) {
				const new_section : displaySection = {...new_section_one, ...sections[(index + 1) % 2]};
				setSection(new_section);
				onSectionUpdate(new_section);
			} else {
				const new_section : divisionSection = {
					...new_section_one,
					sections: [
						...sections.slice(0, index),
						...sections.slice(index + 1)
					]
				}
				setSection(new_section);
				onSectionUpdate(new_section);
			}
    }
  }

  const PrimaryContent = () => (
    <>
      {(section.split === "none") ? (
        <ContextMenuViewportWrapper
          onSplit={onSplit} 
          onCollapse={onCollapse}
          headerAvailable={(section.header === undefined)}
          footerAvailable={(section.footer === undefined)}
        >
          <ScrollSection scrollBar={true} scrollToBottomButton={true}>
            <div className="flex flex-col w-full">
              {large_array.map((_, index) => (
                <div key={index} className="h-[50px]">{index+1}</div>
              ))}
            </div>
          </ScrollSection>
        </ContextMenuViewportWrapper>
      ):(
        <ResizablePanelGroup direction={section.split}>

          {section.sections.map((split_section, index) => (
            <>
              <ResizablePanel key={index} defaultSize={100/section.sections.length}>
                <DivisibleSection
                  onCollapse={() => {resetSection(index)}}
                  onSectionUpdate={(sectionLocal) => {
                    const new_section = section as divisionSection;
                    new_section.sections[index] = sectionLocal;
                    setSection(new_section);
                    onSectionUpdate(new_section);
                  }}
                  windowNumber={windowNumber}
                  currentWindowCount={currentWindowCount}
                  setCurrentWindowCount={setCurrentWindowCount}
                  sectionInfo={split_section}
                />
              </ResizablePanel>
              {(index < section.sections.length - 1) && (
                <ResizableHandle />
              )}
            </>
          ))}
        </ResizablePanelGroup>
      )}
    </>
  );


  return (
    <>
    {(section.header !== undefined || section.footer !== undefined) ? (
      <ResizablePanelGroup direction="vertical">
        {(section.header !== undefined) && (
          <HeaderSection 
            onCollapse={() => {resetSection("header")}} 
            onSectionUpdate={(s : headerSection) => {
              setSection((section) => ({...section, header: s}));
            }} 
            sectionInfo={section.header}
          />
        )}
        <ResizablePanel defaultSize={100} >
        <PrimaryContent />
        </ResizablePanel>
        {(section.footer !== undefined) && (
          <HeaderSection 
            onCollapse={() => {resetSection("footer")}} 
            onSectionUpdate={(s : headerSection) => {
              setSection((section) => ({...section, footer: s}));
            }} 
            sectionInfo={section.footer}
          />
        )}
      </ResizablePanelGroup>
    ) : (
      <PrimaryContent />
    )}
    </>
  );
}

