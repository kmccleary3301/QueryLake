import { useEffect } from 'react';
import { userDataType, toolchainCategory, toolchain_type, setStateOrCallback } from '@/types/globalTypes';
import { ScrollArea } from '@radix-ui/react-scroll-area';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';

type SidebarToolchainsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>,

  selected_toolchain : toolchain_type | undefined,
  set_selected_toolchain : setStateOrCallback<toolchain_type>,

  scrollClassName : string,
}

export default function SidebarToolchains(props: SidebarToolchainsProps) {
  useEffect(() => {
    console.log("new userdata selected", props.userData);
  }, [props.userData]);

  useEffect(() => {
    console.log("Toolchains called");
  }, []);

  const setSelectedToolchain = (toolchain : toolchain_type) => {
    props.set_selected_toolchain(toolchain);
  };

  return (
    <ScrollArea className={props.scrollClassName} style={{
        width: '100%',
        paddingLeft: 4,
        paddingRight: 4,
        paddingTop: 0,
      }}
    >
      {props.userData.available_toolchains.map((toolchain_category : toolchainCategory, category_index : number) => (
        <div key={category_index}>
          {(toolchain_category.entries.length > 0) && (
            <>
            <p style={{
              width: "100%",
              textAlign: 'left',
              fontSize: 14,
              color: '#74748B',
              paddingBottom: 8,
              paddingTop: 8
            }}>
              {toolchain_category.category}
            </p>
            {toolchain_category.entries.map((toolchain_entry : toolchain_type, index : number) => (
              <div style={{
                // paddingTop: 2, 
                // paddingBottom: 2, 
                width: "100%",
                display: "flex",
                flexDirection: "row",
                justifyContent: "flex-start"
              }} key={index}>
                <Button variant={"ghost"} style={{
                  paddingTop: 0, 
                  paddingBottom: 0, 
                  paddingLeft: 6,
                  paddingRight: 6,
                  width: "100%",
                  display: "flex",
                  flexDirection: "row",
                  justifyContent: "flex-start",
                }}
                  onClick={() => {
                    setSelectedToolchain(toolchain_entry);
                  }}
                >
                  <div style={{
                    display: "flex",
                    flexDirection: 'row',
                    justifyContent: "flex-start",
                  }}>
                    <div style={{
                      width: 20,
                      // height: 24,
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      // paddingBottom: 2,
                    }}>
                      {((props.selected_toolchain !== undefined && props.selected_toolchain !== null) && props.selected_toolchain.id === toolchain_entry.id) && (
                        <Icon.Check style={{paddingLeft: 2}} size={16} color="#7968D9"/>
                      )}
                    </div>
                    <p style={{
                      // width: 280,
                      textAlign: 'left',
                      // paddingLeft: 10,
                      // fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      // height: 24,
                      color: '#E8E3E3'
                    }}>
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