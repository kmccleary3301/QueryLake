import { cn } from "@/lib/utils";
import { Button } from "@/registry/default/ui/button";
import { Check, Copy, Pencil } from "lucide-react";
// import Link from "next/link";

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
    <div className={cn("relative not-prose h-10 opacity-100 text-sm rounded-lg hover:bg-accent", className)}>
      <div className="group h-full relative rounded-lg flex flex-col justify-center z-5">
        <div className="absolute h-full w-full rounded-[inherit] hover:bg-accent"/>
        <a className="absolute h-full w-full rounded-[inherit] overflow-hidden whitespace-nowrap" href={href}>
          <Button variant={"ghost"} className="w-full h-full flex flex-row justify-start p-0 m-0 hover:bg-accent" onMouseDown={onSelect}>
            {displaySelected && (
              <div className="w-7 h-full flex flex-col justify-center">
                <div className='w-7 flex flex-row justify-center'>
                  {(selected) && (
                    <Check className='w-3 h-3 text-[#7968D9]'/>
                  )}
                </div>
              </div>
            )}
            <div className='rounded-[inherit] w-auto flex flex-col justify-center h-full'>
              <div className='flex flex-row'>

                <p className='relative pr-2 overflow-hidden text-nowrap text-sm'>{title}</p>
              </div>
            </div>
          </Button>
        </a>
        <div className="absolute h-full w-full bottom-0 right-0 top-0 items-center gap-1.5 rounded-[inherit] overflow-hidden flex flex-row-reverse pointer-events-none">
          <div className='h-full w-full bg-gradient-to-r from-accent/0 from-[calc(100%-30px)] to-card hover:to-accent'/>
        </div>
        <div className="absolute h-full rounded-r-[inherit] w-full hidden group-hover:flex group-hover flex-row-reverse overflow-hidden pointer-events-none">
          <div className='h-full flex flex-col justify-center bg-accent z-10'>
            {children}
          </div>
          <a href={href} className='h-full w-[30px] bg-gradient-to-r from-accent/0 to-accent'/>
        </div>
      </div>
    </div>
  )
}