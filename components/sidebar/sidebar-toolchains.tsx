import { useEffect } from 'react';
import { userDataType, toolchainCategory, toolchain_type, setStateOrCallback } from '@/types/globalTypes';
import { ScrollArea } from '@radix-ui/react-scroll-area';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';
import { cn } from '@/lib/utils';
import { usePathname, useRouter } from 'next/navigation';
import { HoverTextDiv } from '@/registry/default/ui/hover-text-div';
import Link from 'next/link';
import { Copy, Pencil, Trash } from 'lucide-react';

type SidebarToolchainsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>,

  selected_toolchain : string | undefined,
  set_selected_toolchain : setStateOrCallback<string | undefined>,

  scrollClassName : string,
}

function ToolchainEntry({
  toolchain,
  selected = false,
  onSelect = () => {},
}:{
  toolchain: toolchain_type,
  selected?: boolean,
  onSelect?: () => void,
}) {
  return (
    <div className={cn(
      "relative hover:bg-accent hover:text-accent-foreground hover:text-accent-foreground/",
      'p-0 w-full flex flex-row-reverse justify-between h-10 rounded-lg'
    )}>
      <div className='w-full h-full text-left flex flex-row rounded-[inherit] bg-gradient-to-r to-transparent'>
        <button className="w-full h-full flex flex-row rounded-[inherit] overflow-hidden" onClick={onSelect}>
          <div className="w-7 h-full flex flex-col justify-center rounded-[inherit]">
              <div className='w-7 flex flex-row justify-center'>
            {(selected) && (
                <Icon.Check className='w-3 h-3 text-[#7968D9]'/>
              )}
              </div>
          </div>
          <div className='rounded-[inherit] w-auto flex flex-col justify-center h-full'>
            <div className='flex flex-row'>

              <p className='relative pr-2 overflow-hidden text-nowrap text-sm'>{toolchain.title}</p>
            </div>
          </div>
        </button>
      </div>
      <div className='h-10 absolute flex flex-col justify-center opacity-0 hover:opacity-100 rounded-r-[inherit]'>
        <div className='h-auto flex flex-row rounded-r-[inherit]'>
          <div onClick={onSelect} className="w-[20px] h-auto rounded-md bg-gradient-to-l from-accent to-accent/0"/>
          <div className="rounded-r-[inherit] display-none bg-accent">
            <div className='space-x-2 pr-2'>
              <Link href={`/nodes/node_editor?mode=create&ref=${toolchain.id}`}>
                <Button className='h-6 w-4 rounded-full p-0 m-0 text-primary active:text-primary/70' variant={"ghost"}>
                  <Copy className='w-3.5 h-3.5'/>
                </Button>
              </Link>
              <Link href={`/nodes/node_editor?mode=edit&t_id=${toolchain.id}`}>
                <Button className='h-6 w-4 rounded-full p-0 m-0 text-primary active:text-primary/70' variant={"ghost"}>
                  <Pencil className='w-3.5 h-3.5'/>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
  // return (
  //   <div className="relative not-prose h-auto opacity-100 text-sm">
  //     <div className="group relative rounded-lg active:opacity-90 hover:bg-token-sidebar-surface-secondary">
  //       <a className="flex items-center gap-2 p-2">
  //         <div className="relative grow overflow-hidden whitespace-nowrap select-none">
  //           {toolchain.title}
  //           <div className="absolute bottom-0 right-0 top-0 bg-gradient-to-l to-transparent from-token-sidebar-surface-primary from-token-sidebar-surface-primary group-hover:from-token-sidebar-surface-secondary  w-8 from-0% group-hover:w-20 group-hover:from-60% juice:group-hover:w-10">
  //           </div>
  //         </div>
  //       </a>
  //       <div className="absolute bottom-0 right-0 top-0 items-center gap-1.5 pr-2 hidden group-hover:flex group-hover">
  //         <span className="flex flex-row">
  //           <button className="flex items-center justify-center text-token-text-primary transition hover:text-token-text-secondary radix-state-open:text-token-text-secondary juice:text-token-text-secondary juice:hover:text-token-text-primary" type="button" id="radix-:r1k:" aria-haspopup="menu" aria-expanded="false" data-state="closed">
  //             <Pencil className='w-3.5 h-3.5 text-primary'/>
  //           </button>
  //           <button className="flex items-center justify-center text-token-text-primary transition hover:text-token-text-secondary radix-state-open:text-token-text-secondary juice:text-token-text-secondary juice:hover:text-token-text-primary" type="button" id="radix-:r1k:" aria-haspopup="menu" aria-expanded="false" data-state="closed">
  //             <Pencil className='w-3.5 h-3.5 text-primary'/>
  //           </button>
  //         </span>
  //       </div>
  //     </div>
  //   </div>
  // )
}

export default function SidebarToolchains(props: SidebarToolchainsProps) {
  const pathname = usePathname(),
        router = useRouter();

  useEffect(() => {
    console.log("new userdata selected", props.userData);
  }, [props.userData]);

  useEffect(() => {
    console.log("Toolchains called");
  }, []);

  const setSelectedToolchain = (toolchain : string) => {
    props.set_selected_toolchain(toolchain);
  };

  return (
    <ScrollArea className={cn("w-full px-[4px] space-y-2", props.scrollClassName)}>
      {props.userData.available_toolchains.map((toolchain_category : toolchainCategory, category_index : number) => (
        <div key={category_index} className='space-y-1'>
          {(toolchain_category.entries.length > 0) && (
            <>
            <p className="w-full text-left text-primary/50 text-sm pt-2">
              {toolchain_category.category}
            </p>
            {toolchain_category.entries.map((toolchain_entry : toolchain_type, index : number) => (
              // <div className="w-full flex flex-row justify-start" key={index}>
              //   <Button variant={"ghost"} className="py-0 px-[6px] w-full flex flex-row justify-start"
              //     onClick={() => {
              //       if (toolchain_entry.id !== props.selected_toolchain && pathname?.startsWith("/app/session")) {
              //         router.push(`/app/create`);
              //       }
              //       setSelectedToolchain(toolchain_entry.id);
              //     }}>
              //     <div className="flex flex-row justify-start">
              //       <div className="w-6 h-auto flex flex-col justify-center">
              //         {((props.selected_toolchain !== undefined && props.selected_toolchain !== null) && props.selected_toolchain === toolchain_entry.id) && (
              //           <Icon.Check style={{paddingLeft: 2}} size={16} color="#7968D9"/>
              //         )}
              //       </div>
              //       <p className="text-left text-sm h-auto flex flex-col justify-center">
              //         {toolchain_entry.title}
              //       </p>
              //     </div>
              //   </Button>
              // </div>
              <div className='w-[220px]'>

                <ToolchainEntry key={index} toolchain={toolchain_entry} 
                  selected={((props.selected_toolchain !== undefined && props.selected_toolchain !== null) && 
                  props.selected_toolchain === toolchain_entry.id)}
                  onSelect={() => {
                    if (toolchain_entry.id !== props.selected_toolchain && pathname?.startsWith("/app/session")) {
                      router.push(`/app/create`);
                    }
                    setSelectedToolchain(toolchain_entry.id);
                  }}
                />
              </div>
            ))}
            </>
          )}
        </div>
      ))}
    </ScrollArea>
  );
}