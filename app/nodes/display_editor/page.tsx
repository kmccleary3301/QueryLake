"use client";
import { Dispatch, SetStateAction, useState, useMemo, useEffect } from "react"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/registry/default/ui/resizable"
import { 
  ContextMenuViewportWrapper,
  ContextMenuHeaderWrapper
} from "./components/context-menu-wrapper";
import ScrollSection from "@/components/manual_components/scrollable-bottom-stick/custom-scroll-section";
import { DivisibleSection } from "./components/section-divisible";


export type displayMappings = {
  display_route: string[],
  display_as: "chat" | "markdown" | "graph"
}

export type contentSection = {
  split: "none",
  align: alignType,
  mappings: displayMappings[],
  header?: headerSection,
  footer?: headerSection
}

export type divisionSection = {
  split: "horizontal" | "vertical",
  sections: displaySection[],
  header?: headerSection,
  footer?: headerSection
}

export type alignType = "left" | "center" | "right" | "justify";

export type headerSection = {
  align: alignType,
  mappings: displayMappings[]
}

export type displaySection = contentSection | divisionSection


export default function DisplayEditorPage() {
  const [windowCount, setWindowCount] = useState(1);
  const [section, setSection] = useState<displaySection>({
    split: "none",
    align: "center",
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
