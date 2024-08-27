import { Metadata } from "next"

import "public/registry/themes.css"
import FlowDisplay from "./components/flow-page"

export const metadata: Metadata = {
  title: "Nodes",
  description: "Test XYFlow Nodes.",
}

export default function NodeEditorPage() {
  return (
    <div className="h-[calc(100vh)] w-full pr-0 pl-0">
      <FlowDisplay/>
    </div>
  )
}
