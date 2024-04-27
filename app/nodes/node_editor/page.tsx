import { Metadata } from "next"

import "public/registry/themes.css"
import { Announcement } from "@/components/inherited/announcement"
import {
  PageActions,
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/inherited/page-header"
import { ThemeCustomizer } from "@/components/inherited/theme-customizer"
import { ThemeWrapper } from "@/components/inherited/theme-wrapper"
import { ThemesTabs } from "@/app/themes/tabs"
// import Flow from "./components/Flow"
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
