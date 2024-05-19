"use client";
import { useEffect, useRef, useState } from "react"
import { DivisibleSection } from "./components/section-divisible";
import { displaySection } from "@/types/toolchain-interface";
import { useNodeContextAction } from "../context-provider"
import { usePathname } from 'next/navigation';

export default function DisplayEditorPage() {
  const { 
    interfaceConfiguration, 
    setInterfaceConfiguration,
    getInterfaceConfiguration
  } = useNodeContextAction();

  const pathname = usePathname();

  const [windowCount, setWindowCount] = useState(1);
  const [section, setSection] = useState<displaySection>(JSON.parse(JSON.stringify(getInterfaceConfiguration())));

  const sectionRef = useRef<displaySection>(JSON.parse(JSON.stringify(interfaceConfiguration)));

  const sectionUpdate = (sectionLocal : displaySection) => {
    sectionRef.current = sectionLocal;
    setInterfaceConfiguration(sectionRef.current);
  }

  useEffect(() => {
    setSection(JSON.parse(JSON.stringify(getInterfaceConfiguration())));

  }, [pathname])

  return (
    <div className="h-[100vh] w-full pr-0 pl-0">
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
