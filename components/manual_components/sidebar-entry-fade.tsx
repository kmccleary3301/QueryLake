import { cn } from "@/lib/utils";
import { Button } from "@/registry/default/ui/button";
import { Check, Copy, Pencil } from "lucide-react";
import Link from "next/link";
// import Link from "next/link";

function LinkOptional({
  href,
  className,
  children
}:{
  href?: string, 
  className?: string,
  children?: React.ReactNode
}) {
  if (href) {
    return (
      <Link href={href} className={className}>
        {children}
      </Link>
    )
  } else {
    return (
      <a className={className}>
        {children}
      </a>
    )
  }
}

export default function SidebarEntry({
  title,
  children,
  className = "",
  href = undefined,
  displaySelected = true,
  selected = false,
  onSelect = () => {},
}:{
  title: string,
  children?: React.ReactNode,
  className?: string,
  href?: string,
  displaySelected?: boolean,
  selected?: boolean,
  onSelect?: () => void,
}) {

  return (
    <div className={cn("relative not-prose h-10 opacity-100 text-sm rounded-lg hover:bg-accent")}>
      <div className="group h-full relative rounded-lg flex flex-col justify-center z-5">
        <div className="absolute h-full w-full rounded-[inherit] hover:bg-accent"/>
        <LinkOptional className="absolute h-full w-full rounded-[inherit] overflow-hidden whitespace-nowrap" href={href}>
          <Button variant={"ghost"} className={cn("w-full h-full flex flex-row justify-start p-0 m-0 hover:bg-accent", className)} onMouseDown={onSelect}>
            {displaySelected && (
              <div className="w-7 h-full flex flex-col justify-center">
                <div className='w-7 flex flex-row justify-center'>
                  {(selected) && (
                    <Check className='w-3 h-3 text-[#7968D9]'/>
                  )}
                </div>
              </div>
            )}
            <div className='rounded-[inherit] w-auto overflow-hidden flex flex-col justify-center h-full'>
              <div className='flex flex-row'>
                <p className='relative pr-2 mr-[1px] overflow-hidden text-nowrap text-sm'>{title}</p>
              </div>
            </div>
          </Button>
        </LinkOptional>
        <div className="absolute h-full w-full bottom-0 right-0 top-0 items-center gap-1.5 rounded-[inherit] overflow-hidden flex flex-row-reverse pointer-events-none">
          <div className='h-full w-full bg-gradient-to-r from-accent/0 from-[calc(100%-30px)] to-card hover:to-accent'/>
        </div>
        <div className="absolute h-full rounded-r-[inherit] w-full hidden group-hover:flex group-hover flex-row-reverse overflow-hidden pointer-events-none">
          <div className="pointer-events-none">
            <div className='h-full flex flex-col justify-center bg-accent z-10 pointer-events-auto'>
              {children}
            </div>
          </div>
          <LinkOptional href={href} className='h-full w-[30px] bg-gradient-to-r from-accent/0 to-accent'/>
            {/* {(href) && (<Link href={href} className="w-inherit h-inherit"/>)}
          </a> */}
        </div>
      </div>
    </div>
  )
}