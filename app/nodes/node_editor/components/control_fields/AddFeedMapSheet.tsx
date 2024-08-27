"use client";
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { feedMapping, staticRoute } from "@/types/toolchains"
import { StaticRouteCreation } from "./StaticRouteCreation"
import { HoverCard, HoverCardContent } from "@/components/ui/hover-card"
import { HoverCardTrigger } from "@radix-ui/react-hover-card"
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "@/components/ui/context-menu"
import Code from "@/components/markdown/code"
import MarkdownCodeBlock from "@/components/markdown/markdown-code-block";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import SequenceActionModifier from "./SequenceActionModifier";

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
          <div className="w-[60vw] lg:w-[40vw] xl:w-[25vw] pr-5 py-2">
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1">
              <AccordionTrigger>Raw Value</AccordionTrigger>
              <AccordionContent>
                <MarkdownCodeBlock text={JSON.stringify(data, null, 4)} lang="JSON" finished/>
              </AccordionContent>
            </AccordionItem>
            {(data && data.sequence !== undefined && data.sequence !== null) && (
              <AccordionItem value="item-2" className="border-b-0">
                <AccordionTrigger>Sequence</AccordionTrigger>
                <AccordionContent className="space-y-4">
                {/* <p>Static Route Creator</p> */}
                {data.sequence.map((seq, index) => (
                  <SequenceActionModifier data={seq} key={index}/>
                ))}
                </AccordionContent>
              </AccordionItem>
            )}
          </Accordion>
            
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
}
