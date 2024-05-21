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
      "relative hover:bg-accent active:bg-accent/70 hover:text-accent-foreground hover:text-accent-foreground/",
      'p-0 w-full flex flex-row-reverse justify-between h-10 rounded-lg'
    )}>
      <HoverTextDiv hint={toolchain.title} className='w-full h-full text-left flex flex-row rounded-[inherit]'>
        <button className="w-full h-full flex flex-row rounded-[inherit] overflow-hidden" onClick={onSelect}>
          <div className="w-7 h-full flex flex-col justify-center rounded-[inherit]">
            {(selected) && (
              <div className='w-full flex flex-row justify-center'>
              <Icon.Check className='w-3 h-3 text-[#7968D9]'/>
              </div>
            )}
          </div>
          <div className='rounded-[inherit] w-auto flex flex-col justify-center h-full'>
            <p className='relative pr-2 overflow-hidden overflow-ellipsis text-sm whitespace-nowrap'>{toolchain.title}</p>
          </div>
        </button>
      </HoverTextDiv>
      <div className='h-10 absolute flex flex-col justify-center opacity-0 hover:opacity-100 rounded-r-[inherit]'>
        <div className='h-auto flex flex-row rounded-r-[inherit]'>
          <div onClick={onSelect} className="w-[20px] h-auto rounded-md bg-gradient-to-l from-accent to-accent/0"/>
          <div className="bg-accent rounded-r-[inherit] display-none">
            <div className='space-x-2 pr-2'>
              <Link href={`/nodes/node_editor?mode=create&ref=${toolchain.id}`}>
                <Button className='h-6 w-4 rounded-full p-0 m-0' variant={"ghost"}>
                  <Copy className='w-3.5 h-3.5 text-primary'/>
                </Button>
              </Link>
              <Link href={`/nodes/node_editor?mode=edit&t_id=${toolchain.id}`}>
                <Button className='h-6 w-4 rounded-full p-0 m-0' variant={"ghost"}>
                  <Pencil className='w-3.5 h-3.5 text-primary'/>
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
      
  );
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
            ))}
            </>
          )}
        </div>
      ))}
    </ScrollArea>
  );
}