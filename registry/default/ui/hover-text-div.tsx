import { CalendarDays } from "lucide-react"

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "./avatar"
import { Button } from "./button"
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "./hover-card"

export function HoverTextDiv({
  className,
  hint,
  children,
}:{
  className?: string,
  hint: string,
  children: React.ReactNode
}) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <div className={className}>
          {children}
        </div>
      </HoverCardTrigger>
      <HoverCardContent>
        <p className="text-sm">
          {hint}
        </p>
      </HoverCardContent>
    </HoverCard>
  )
}
