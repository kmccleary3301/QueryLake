import { Metadata } from "next"
import Link from "next/link"

import { cn } from "@/lib/utils"
import { Announcement } from "@/components/inherited/announcement"
import {
  PageActions,
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/inherited/page-header"
import { buttonVariants } from "@/registry/new-york/ui/button"
import { AceternityNav } from "@/components/inherited/aceternity-nav"
import { ContextTestDisplay } from "./components/context-test-display"

export const metadata: Metadata = {
  title: "Examples",
  description: "Check out some examples app built using the components.",
}

interface ExamplesLayoutProps {
  children: React.ReactNode
}

export default function AceternityLayout({ children }: ExamplesLayoutProps) {
  return (
    <>
      <div className="container relative pt-14 pb-10">
        <PageHeader>
          <ContextTestDisplay className="text-center text-3xl font-bold leading-tight tracking-tighter md:text-6xl lg:leading-[1.1]"/>
        </PageHeader>
        <section>
          <AceternityNav />
          <div className="overflow-hidden rounded-[0.5rem] border bg-background shadow-md md:shadow-xl">
            {children}
          </div>
        </section>
      </div>
    </>
  )
}
