"use client";
import { Dispatch, SetStateAction, useState } from "react"
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
  mappings: displayMappings[]
}

export type divisionSection = {
  split: "horizontal" | "vertical",
  sectionOne: displaySection,
  sectionTwo: displaySection
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

  const onSplit = (splitType : "horizontal" | "vertical") => {
    const new_section : divisionSection = {
      split: splitType,
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
  }

  const resetSection = (type : 1 | 2) => {
    if (section.split === "none") return;
    
    const new_section : contentSection = {
      split: "none",
      mappings: []
    }

    // const new_section : displaySection = (type === 1) ? section.sectionOne : section.sectionTwo;
    setSection(new_section);
    onSectionUpdate(new_section);
  }


  return (
    <>
      {(section.split === "none") ? (
        <ContextMenuWrapper onSplit={onSplit} onCollapse={onCollapse}>
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
