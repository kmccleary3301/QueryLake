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
  displaySelected: boolean,
  selected?: boolean,
  onSelect?: () => void,
}) {
  // return (
  //   <div className={cn(
  //     "relative hover:bg-accent hover:text-accent-foreground hover:text-accent-foreground/",
  //     'p-0 w-full flex flex-row-reverse justify-between h-10 rounded-lg'
  //   )}>
  //     <div className='w-full h-full text-left flex flex-row rounded-[inherit] bg-gradient-to-r to-transparent'>
  //       <button className="w-full h-full flex flex-row rounded-[inherit] overflow-hidden" onClick={onSelect}>
  //         <div className="w-7 h-full flex flex-col justify-center rounded-[inherit]">
  //             <div className='w-7 flex flex-row justify-center'>
  //           {(selected) && (
  //               <Icon.Check className='w-3 h-3 text-[#7968D9]'/>
  //             )}
  //             </div>
  //         </div>
  //         <div className='rounded-[inherit] w-auto flex flex-col justify-center h-full'>
  //           <div className='flex flex-row'>

  //             <p className='relative pr-2 overflow-hidden text-nowrap text-sm'>{toolchain.title}</p>
  //           </div>
  //         </div>
  //       </button>
  //     </div>
  //     <div className='h-10 absolute flex flex-col justify-center opacity-0 hover:opacity-100 rounded-r-[inherit]'>
  //       <div className='h-auto flex flex-row rounded-r-[inherit]'>
  //         <div onClick={onSelect} className="w-[20px] h-auto rounded-md bg-gradient-to-l from-accent to-accent/0"/>
  //         <div className="rounded-r-[inherit] display-none bg-accent">
  //           <div className='space-x-2 pr-2'>
  //             <Link href={`/nodes/node_editor?mode=create&ref=${toolchain.id}`}>
  //               <Button className='h-6 w-4 rounded-full p-0 m-0 text-primary active:text-primary/70' variant={"ghost"}>
  //                 <Copy className='w-3.5 h-3.5'/>
  //               </Button>
  //             </Link>
  //             <Link href={`/nodes/node_editor?mode=edit&t_id=${toolchain.id}`}>
  //               <Button className='h-6 w-4 rounded-full p-0 m-0 text-primary active:text-primary/70' variant={"ghost"}>
  //                 <Pencil className='w-3.5 h-3.5'/>
  //               </Button>
  //             </Link>
  //           </div>
  //         </div>
  //       </div>
  //     </div>
  //   </div>
  // );
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
          <div className='h-full w-full bg-gradient-to-r from-accent/0 from-[calc(100%-80px)] to-background hover:to-accent'/>
        </div>
        <div className="absolute h-full rounded-r-[inherit] w-full hidden group-hover:flex group-hover flex-row-reverse overflow-hidden pointer-events-none">
          <div className='h-full flex flex-col justify-center bg-accent z-10'>
            {children}
          </div>
          <div className='h-full w-[80px] bg-gradient-to-r from-accent/0 to-accent'/>
        </div>
      </div>
    </div>
  )
}