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
      <PopoverContent className="w-auto pr-0">
        <ScrollArea className="w-100 h-[400px]">
          <div className="w-95 pr-5">
            <MarkdownCodeBlock text={JSON.stringify(data, null, 4)} lang="JSON" finished/>
            {(data && data.route !== undefined && data.route !== null) && (
              <StaticRouteCreation values={data.route} className=""/>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  )
}
