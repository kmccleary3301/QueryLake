"use client";
import { Dispatch, SetStateAction, useState, useMemo } from "react"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/registry/default/ui/resizable"
import ContextMenuWrapper from "./components/context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";

export type displayMappings = {
  display_route: string[],
  display_as: "chat" | "markdown" | "graph"
}

export type contentSection = {
  split: "none",
  mappings: displayMappings[],
  header?: displaySection,
  footer?: displaySection
}

export type divisionSection = {
  split: "horizontal" | "vertical",
  sectionOne: displaySection,
  sectionTwo: displaySection,
  header?: displaySection,
  footer?: displaySection
}

export type displaySection = contentSection | divisionSection

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

  const onSplit = (splitType : "horizontal" | "vertical" | "header" | "footer") => {
    if (splitType == "horizontal" || splitType == "vertical") {
      const new_section : divisionSection = {
        ...section,
        split: splitType as "horizontal" | "vertical",
        sectionOne: {
          split: "none",
          mappings: []
        },
        sectionTwo: {
          split: "none",
          mappings: []
        }
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "header") {
      const new_section : displaySection = {
        ...section,
        header: {
          split: "none",
          mappings: []
        }
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    } else if (splitType === "footer") {
      const new_section : displaySection = {
        ...section,
        footer: {
          split: "none",
          mappings: []
        }
      }
      setSection(new_section);
      onSectionUpdate(new_section);
    }
  }

  const resetSection = (type : 1 | 2 | 3 | 4) => {
    if (type === 1) {

      if (section.split === "none") return;
      
      const { sectionOne, sectionTwo, ...new_section_one } = section;
      const new_section : displaySection = {...new_section_one, ...sectionOne};


      setSection(new_section);
      onSectionUpdate(new_section);
    } 
    else if (type === 3) {
      const { header, ...new_section } = section;
      setSection(new_section);
      onSectionUpdate(new_section);
    } 
    else if (type === 4) {
      const { footer, ...new_section } = section;
      setSection(new_section);
      onSectionUpdate(new_section);
    }
    else {
      if (section.split === "none") return;
      
      const { sectionOne, sectionTwo, ...new_section_one } = section;
      // const new_section : displaySection = {...new_section_one, mappings: [], split: "none"};
      const new_section : displaySection = {...new_section_one, ...sectionTwo};

      setSection(new_section);
      onSectionUpdate(new_section);
    }
  }

  const PrimaryContent = () => (
    <>
      {(section.split === "none") ? (
        <ContextMenuWrapper 
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
        </ContextMenuWrapper>
      ):(
        <ResizablePanelGroup direction={section.split}>
          <ResizablePanel defaultSize={50}>
            <DivisibleSection
              onCollapse={() => {resetSection(2)}}
              onSectionUpdate={(sectionLocal) => {
                const new_section = section as divisionSection;
                new_section.sectionOne = sectionLocal;
                setSection(new_section);
                onSectionUpdate(new_section);
              }}
              windowNumber={windowNumber}
              currentWindowCount={currentWindowCount}
              setCurrentWindowCount={setCurrentWindowCount}
              sectionInfo={section.sectionOne}
            />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel defaultSize={50}>
            <DivisibleSection
              onCollapse={() => {resetSection(1)}}
              onSectionUpdate={(sectionLocal) => {
                const new_section = section as divisionSection;
                new_section.sectionTwo = sectionLocal;
                setSection(new_section);
                onSectionUpdate(new_section);
              }}
              windowNumber={windowNumber}
              currentWindowCount={currentWindowCount}
              setCurrentWindowCount={setCurrentWindowCount}
              sectionInfo={section.sectionOne}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      )}
    </>
  );


  return (
    <>
    {(section.header !== undefined || section.footer !== undefined) ? (
      <ResizablePanelGroup direction="vertical">
        {(section.header !== undefined) && (
          
            <div className="h-[50px] border-green-500 border-[2px] text-center flex flex-col justify-center">Header</div>
        )}
        <ResizablePanel defaultSize={100} >
        <PrimaryContent />
        </ResizablePanel>
        {(section.footer !== undefined) && (
          // <ResizablePanel defaultSize={10}>
          //   <DivisibleSection
          //     onCollapse={() => {resetSection(4)}}
          //     onSectionUpdate={(sectionLocal) => {
          //       const new_section = section as displaySection;
          //       new_section.footer = sectionLocal;
          //       setSection(new_section);
          //       onSectionUpdate(new_section);
          //     }}
          //     windowNumber={windowNumber}
          //     currentWindowCount={currentWindowCount}
          //     setCurrentWindowCount={setCurrentWindowCount}
          //     sectionInfo={section.footer}
          //   />
          // </ResizablePanel>
          <div className="h-[50px] border-red-500 border-[2px] text-center flex flex-col justify-center">Footer</div>
        )}
      </ResizablePanelGroup>
    ) : (
      <PrimaryContent />
    )}
    </>
  );
}



export default function DisplayEditorPage() {
  const [windowCount, setWindowCount] = useState(1);
  const [section, setSection] = useState<displaySection>({
    split: "none",
    mappings: []
  });

  return (
    <div className="h-[calc(100vh-60px)] w-full pr-0 pl-0">
      <DivisibleSection
        onCollapse={() => {}}
        onSectionUpdate={(sectionLocal) => {
          setSection(sectionLocal);
        }}
        windowNumber={windowCount}
        currentWindowCount={windowCount}
        setCurrentWindowCount={setWindowCount}
        sectionInfo={section}
      />
    </div>
  )
}
