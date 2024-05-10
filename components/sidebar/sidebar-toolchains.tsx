import { useEffect } from 'react';
import { userDataType, toolchainCategory, toolchain_type, setStateOrCallback } from '@/types/globalTypes';
import { ScrollArea } from '@radix-ui/react-scroll-area';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';
import { cn } from '@/lib/utils';
import { usePathname, useRouter } from 'next/navigation';

type SidebarToolchainsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>,

  selected_toolchain : string | undefined,
  set_selected_toolchain : setStateOrCallback<string | undefined>,

  scrollClassName : string,
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
        <div key={category_index}>
          {(toolchain_category.entries.length > 0) && (
            <>
            <p className="w-full text-left text-primary/50 text-sm pt-2">
              {toolchain_category.category}
            </p>
            {toolchain_category.entries.map((toolchain_entry : toolchain_type, index : number) => (
              <div className="w-full flex flex-row justify-start" key={index}>
                <Button variant={"ghost"} className="py-0 px-[6px] w-full flex flex-row justify-start"
                  onClick={() => {
                    if (toolchain_entry.id !== props.selected_toolchain && pathname?.startsWith("/app/session")) {
                      router.push(`/app/create`);
                    }
                    setSelectedToolchain(toolchain_entry.id);
                  }}>
                  <div className="flex flex-row justify-start">
                    <div className="w-6 h-auto flex flex-col justify-center">
                      {((props.selected_toolchain !== undefined && props.selected_toolchain !== null) && props.selected_toolchain === toolchain_entry.id) && (
                        <Icon.Check style={{paddingLeft: 2}} size={16} color="#7968D9"/>
                      )}
                    </div>
                    <p className="text-left text-sm h-auto flex flex-col justify-center">
                      {toolchain_entry.title}
                    </p>
                  </div>
                </Button>
              </div>
            ))}
            </>
          )}
        </div>
      ))}
    </ScrollArea>
  );
}