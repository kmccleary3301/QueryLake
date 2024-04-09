"use client";
import { useRef, useState } from "react"
import { DivisibleSection } from "./components/section-divisible";
import { displaySection } from "@/types/toolchain-interface";
import { useNodeContextAction } from "../context-provider"


export default function DisplayEditorPage() {
  const { 
    interfaceConfiguration, 
    setInterfaceConfiguration
  } = useNodeContextAction();

  const [windowCount, setWindowCount] = useState(1);
  const [section, setSection] = useState<displaySection>(JSON.parse(JSON.stringify(interfaceConfiguration)));

  

  const sectionRef = useRef<displaySection>({
    split: "none",
    size: 100,
    align: "center",
    tailwind: "",
    mappings: []
  });

  const sectionUpdate = (sectionLocal : displaySection) => {
    sectionRef.current = sectionLocal;
    setInterfaceConfiguration(sectionRef.current);

    // setInterfaceConfiguration(sectionLocal);
    // console.log(sectionLocal);
  }
  
  return (
    <div className="h-[calc(100vh-60px)] w-full pr-0 pl-0">
      <DivisibleSection
        onCollapse={() => {}}
        onSectionUpdate={sectionUpdate}
        windowNumber={windowCount}
        currentWindowCount={windowCount}
        setCurrentWindowCount={setWindowCount}
        // sectionInfo={sectionRef.current}
        sectionInfo={section}
      />
    </div>
  )
}
