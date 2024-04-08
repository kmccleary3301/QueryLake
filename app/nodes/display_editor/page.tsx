"use client";
import { useState } from "react"
import { DivisibleSection } from "./components/section-divisible";
import { displaySection } from "@/types/toolchain-interface";
import { useNodeContextAction } from "../context-provider"


export default function DisplayEditorPage() {
  const { 
    interfaceConfiguration, 
    setInterfaceConfiguration
  } = useNodeContextAction();

  const [windowCount, setWindowCount] = useState(1);
  const [section, setSection] = useState<displaySection>({
    split: "none",
    align: "center",
    tailwind: "",
    mappings: []
  });
  
  return (
    <div className="h-[calc(100vh-60px)] w-full pr-0 pl-0">
      <DivisibleSection
        onCollapse={() => {}}
        onSectionUpdate={(sectionLocal) => {
          setInterfaceConfiguration(sectionLocal);
        }}
        windowNumber={windowCount}
        currentWindowCount={windowCount}
        setCurrentWindowCount={setWindowCount}
        sectionInfo={interfaceConfiguration}
      />
    </div>
  )
}
