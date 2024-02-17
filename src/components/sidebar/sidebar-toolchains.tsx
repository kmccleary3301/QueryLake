
// import { ScrollView, TextInput } from 'react-native-gesture-handler';
// import { Feather } from '@expo/vector-icons';
import { useEffect } from 'react';
// import AnimatedPressable from './AnimatedPressable';
import { userDataType, toolchainEntry, toolchainCategory } from '@/typing/globalTypes';
import { ScrollArea } from '@radix-ui/react-scroll-area';
import { Button } from '../ui/button';
import * as Icon from 'react-feather';

type SidebarToolchainsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>,
}
  
export default function SidebarToolchains(props: SidebarToolchainsProps) {
  useEffect(() => {
    console.log("new userdata selected", props.userData);
  }, [props.userData]);

  useEffect(() => {
    console.log("Toolchains called");
  }, []);

  return (
    <>
      <ScrollArea className="h-[calc(100vh-262px)]" style={{
          width: '100%',
          paddingLeft: 22,
					paddingRight: 22,
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
              {toolchain_category.entries.map((value : toolchainEntry, index : number) => (
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
										width: "100%",
										display: "flex",
										flexDirection: "row",
										justifyContent: "flex-start",
									}}
                    onClick={() => {
                      props.setUserData({...props.userData, selected_toolchain: value});
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
                        {(props.userData.selected_toolchain.id === value.id) && (
                          <Icon.Check size={16} color="#7968D9"/>
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
                        {value.name}
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
    </> 
  );
}