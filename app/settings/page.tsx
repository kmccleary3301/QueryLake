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
import { ScrollArea } from "@/registry/default/ui/scroll-area"

export const metadata: Metadata = {
  title: "Themes OG",
  description: "Hand-picked themes that you can copy and paste into your apps.",
}

export default function ThemesPage() {
  return (
    <ScrollArea className="w-full h-screen">
      <div className="w-screen flex flex-row justify-center">
        <div className="flex flex-col w-[85vw] md:w-[70vw] lg:w-[60vw] xl:w-[50vw]">
          <ThemeWrapper
            defaultTheme="zinc"
            className="relative flex flex-col items-start md:flex-row md:items-center"
          >
            <PageHeader>
              <Announcement />
              <PageHeaderHeading className="hidden md:block">
                Add colors. Make it yours.
              </PageHeaderHeading>
              <PageHeaderHeading className="md:hidden">
                Make it yours
              </PageHeaderHeading>
              <PageHeaderDescription>
                Hand-picked themes that you can copy and paste into your apps.
              </PageHeaderDescription>
              <PageActions>
                <ThemeCustomizer />
              </PageActions>
            </PageHeader>
          </ThemeWrapper>
          

          {/* <ThemesTabs /> */}
        </div>
      </div>
    </ScrollArea>
  )
}
