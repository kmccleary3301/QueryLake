"use client";
import { Button } from "@/registry/default/ui/button"
import { Input } from "@/registry/default/ui/input"
import { Label } from "@/registry/default/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/registry/default/ui/popover"
import { feedMapping, staticRoute } from "@/types/toolchains"
import { StaticRouteCreation } from "./StaticRouteCreation"
import { HoverCard, HoverCardContent } from "@/registry/default/ui/hover-card"
import { HoverCardTrigger } from "@radix-ui/react-hover-card"
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "@/registry/default/ui/context-menu"
import Code from "@/components/markdown/code"
import MarkdownCodeBlock from "@/components/markdown/markdown-code-block";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/registry/default/ui/accordion";

export default function AddFeedMapSheet({
  data,
  className,
  children,
}: {
  data?: feedMapping,
  className?: string,
  children?: React.ReactNode
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <div className={className}>
          {children}
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        {(data && data.route !== undefined && data.route !== null) && (
          <StaticRouteCreation values={data.route} className=""/>
        )}
      </PopoverContent>
    </Popover>
  )
}


export function ModifyFeedMapSheet({
  data,
  className,
  children,
  ...props
}: {
  data?: feedMapping,
  className?: string,
  children?: React.ReactNode
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <div className={className}>
          {children}
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-auto pr-0 py-0">
        <ScrollArea className="h-[400px]">
          <div className="w-[60vw] lg:w-[40vw] xl:w-[30vw] pr-5 py-2">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>Raw Value</AccordionTrigger>
              <AccordionContent>
                <MarkdownCodeBlock text={JSON.stringify(data, null, 4)} lang="JSON" finished/>
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-2">
              <AccordionTrigger>Sequence</AccordionTrigger>
              <AccordionContent>
                Yes. It comes with default styles that matches the other
                components&apos; aesthetic.
              </AccordionContent>
            </AccordionItem>
          </Accordion>

            
            {(data && data.route !== undefined && data.route !== null) && (
              <StaticRouteCreation values={data.route} className=""/>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
}