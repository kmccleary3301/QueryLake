// import {
//   View,
//   Text,
// } from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
// import SwitchSelector from '../lib/react-native-switch-selector';
// import { Feather } from '@expo/vector-icons';
import { useState, useEffect } from 'react';
// import SidebarCollectionSelect from './SidebarCollectionSelect';
// import AnimatedPressable from './AnimatedPressable';
// import SidebarChatHistory from './SidebarChatHistory';
// import getChatHistory from '../hooks/getChatHistory';
import { getChatHistory, getUserCollections } from '@/hooks/querylakeAPI';
// import getUserCollections from '../hooks/getUserCollections';
// import SidebarToolchains from './SidebarToolchains';
import { collectionGroup, timeWindowType, userDataType, pageID, selectedCollectionsType } from '@/typing/globalTypes';
import { Button } from '../ui/button';
import {
	TabsContent,
  TabsList,
  TabsTrigger,
	Tabs
} from "@/components/ui/tabs"
import * as Icon from 'react-feather';
import SidebarCollectionSelect from './sidebar-collections';
import SidebarToolchains from './sidebar-toolchains';
import SidebarChatHistory from './sidebar-history';
import { useNavigate } from "react-router-dom";



// type userDataType = {
//   username: string,
//   password_pre_hash: string,
//   memberships: object[],
//   is_admin: boolean,
//   available_toolchains: toolchainCategory[],
//   selected_toolchain: toolchainEntry
// };

type SidebarProps = {
  toggle_sideBar?: () => void,
  on_change_collections?: (collectionGroups: collectionGroup[]) => void, 
  user_data: userDataType,
  set_page_navigate: React.Dispatch<React.SetStateAction<pageID>>,
  // navigation?: any,
  page_navigate_arguments: string,
  set_page_navigate_arguments: React.Dispatch<React.SetStateAction<string>>,
  refresh_side_panel: string[],
  set_refresh_side_panel: React.Dispatch<React.SetStateAction<string[]>>,
  set_selected_collections: React.Dispatch<React.SetStateAction<selectedCollectionsType>>,
  selected_collections: selectedCollectionsType,
  set_user_data: React.Dispatch<React.SetStateAction<userDataType | undefined>>,
  set_chat_history: React.Dispatch<React.SetStateAction<timeWindowType[]>>,
  chat_history: timeWindowType[]
  // sidebarOpened?: boolean,
}



// type panelModeType = "collections" | "history" | "tools";


export default function Sidebar(props: SidebarProps) {
  // console.log(props);
	// const [panelMode, setPanelMode] = useState<panelModeType>("collections");
  // const [chatHistory, setChatHistory] = useState<sessionEntry[]>([]);
	const [collectionGroups, setCollectionGroups] = useState<collectionGroup[]>([]);
	const navigate = useNavigate();
	
  // Get all user data for sidebar. This includes chat history and collections
  useEffect(() => {
		const timeWindows = [
			{title: "Last 24 Hours", cutoff: 24*3600, entries: []},
			{title: "Last 2 Days", cutoff: 2*24*3600, entries: []},
			{title: "Past Week", cutoff: 7*24*3600, entries: []},
			{title: "Past Month", cutoff: 30*24*3600, entries: []},
		];

    console.log("userdata:", props.user_data);
    let chat_history_grabbed = false;
    let collections_grabbed = false;
    if (props.chat_history.length == 0) {
      getChatHistory({
				username: props.user_data.username, 
				password_prehash: props.user_data.password_pre_hash, 
				time_windows: timeWindows.slice(), 
				set_value: props.set_chat_history
			});
      chat_history_grabbed = true;
    }
    if (collectionGroups.length == 0) {
      getUserCollections({
				username: props.user_data.username, 
				password_prehash: props.user_data.password_pre_hash, 
				set_value: setCollectionGroups
			});
      collections_grabbed = true;
    }
    for (let i = 0; i < props.refresh_side_panel.length; i++) {
      if (!chat_history_grabbed && props.refresh_side_panel[i] === "chat-history") {
        getChatHistory({
					username: props.user_data.username, 
					password_prehash: props.user_data.password_pre_hash, 
					time_windows: timeWindows.slice(), 
					set_value: props.set_chat_history
				});
        chat_history_grabbed = true;
      } else if (!collections_grabbed && props.refresh_side_panel[i] === "collections") {
        getUserCollections({
					username: props.user_data.username, 
					password_prehash: props.user_data.password_pre_hash, 
					set_value: setCollectionGroups
				});
        collections_grabbed = true;
      }
    }
  }, [props.refresh_side_panel, props.user_data, collectionGroups.length, props.chat_history.length, props.set_chat_history]);

  // Destructure props
	const { set_selected_collections: setSelectedCollections } = props;

  useEffect(() => {
    const new_selections_state = new Map<string, boolean>([]);
    for (let i = 0; i < collectionGroups.length; i++) {
      for (let j = 0; j < collectionGroups[i].collections.length; j++) {
        new_selections_state.set(collectionGroups[i].collections[j]["hash_id"], false); //Change to false
      }
    }
    setSelectedCollections(new_selections_state);
  }, [collectionGroups, setSelectedCollections]);

	const setCollectionSelected = (collection_hash_id : string, value : boolean) => {
		props.selected_collections.set(collection_hash_id, value);
  };

	return (
    <div style={{height: '100vh'}}>
      <div style={{
        backgroundColor: "#17181D", 
        height: "100%", 
        flexDirection: 'column', 
        padding: 0, 
      }}>
        <div style={{
          flex: 5,
          paddingLeft: 0,
          paddingRight: 0,
          // paddingVertical: 10,
          alignItems: 'center',
					display: "flex",
          flexDirection: 'column',
          justifyContent: 'space-evenly'
        }}>
          <div style={{
						display: "flex",
            flexDirection: 'row',
            paddingTop: 4,
						paddingBottom: 7.5,
            paddingLeft: 30,
            paddingRight: 30,
            alignItems: 'center',
            width: '100%',
            justifyContent: 'space-between',
          }}>
            <Button variant="ghost" style={{padding: 0, paddingLeft: 8, paddingRight: 8}}>
              <Icon.Settings size={24} color="#E8E3E3" />
            </Button>
            <Button variant="ghost" style={{padding: 0, paddingLeft: 8, paddingRight: 8}}>
              <Icon.Info size={24} color="#E8E3E3" />
            </Button>
            <Button variant="ghost" style={{padding: 2, borderRadius: 5, paddingLeft: 8, paddingRight: 8}} onClick={() => {
              if (props.toggle_sideBar) { props.toggle_sideBar(); }
            }}>
              <Icon.Sidebar size={24} color="#E8E3E3" />
            </Button>
          </div>
          <div style={{
            width: '100%',
            paddingLeft: 22,
						paddingRight: 22,
            // alignSelf: 'center'
            paddingBottom: 10,
          }}>
						
						<Tabs defaultValue={"collections"}>
							<TabsList className="bg-[#7968D9] grid w-full h-auto grid-cols-3 bottom" style={{
                paddingBottom: 0,
                paddingTop: 0,
                paddingLeft: 0,
                paddingRight: 0,
              }}>
								<TabsTrigger className="data-[state=active]:bg-[#E8E3E3] rounded-lg" value="collections">
									<Icon.Folder size={24} color="#17181D" />
								</TabsTrigger>
								<TabsTrigger className="data-[state=active]:bg-[#E8E3E3] rounded-lg" value="history">
									<Icon.Clock size={24} color="#17181D" />
								</TabsTrigger>
								<TabsTrigger className="data-[state=active]:bg-[#E8E3E3] rounded-lg" value="tools">
									<Icon.Aperture size={24} color="#17181D" />
								</TabsTrigger>
							</TabsList>
							<TabsContent value="collections">
								<SidebarCollectionSelect
									userData={props.user_data}
									setPageNavigate={props.set_page_navigate}
									refreshSidePanel={props.refresh_side_panel}
									setPageNavigateArguments={props.set_page_navigate_arguments}
									collectionGroups={collectionGroups}
									setCollectionGroups={setCollectionGroups}
									setCollectionSelected={setCollectionSelected}
									selectedCollections={props.selected_collections}
								/>
							</TabsContent>
              <TabsContent value="history">
                <SidebarChatHistory 
                  userData={props.user_data} 
                  setPageNavigateArguments={props.set_page_navigate_arguments} 
                  // setPageNavigate={props.set_page_navigate}
                  refreshSidePanel={props.refresh_side_panel}
                  chatHistory={props.chat_history}
                  setChatHistory={props.set_chat_history}
                  pageNavigateArguments={props.page_navigate_arguments}
                />
							</TabsContent>
              <TabsContent value="tools">
                <SidebarToolchains
                  userData={props.user_data}
                  setUserData={props.set_user_data}
                />
							</TabsContent>
						</Tabs>
            {/* <SwitchSelector
              initial={0}
              width={"100%"}
              onPress={(value : string) => {
                setPanelMode(value);
                props.setRefreshSidePanel((oldValue) => ([...oldValue, value]));
                // console.log(value);
              }}
              textColor={'#000000'} //'#7a44cf'
              selectedColor={'#000000'}
              buttonColor={'#E8E3E3'}
              backgroundColor={'#7968D9'}
              // borderColor={'#7a44cf'}
              height={30}
              borderRadius={15}
              hasPadding={false}
              imageStyle={{
                height: 20,
                width: 20,
                resizeMode: 'stretch'
              }}
              options={[
                { value: "collections", imageIcon: icons.folder}, //images.feminino = require('./path_to/assets/img/feminino.png')
                { value: "history", imageIcon: icons.clock}, //images.masculino = require('./path_to/assets/img/masculino.png')
                { value: "tools", imageIcon: icons.aperture}
              ]}
              testID="gender-switch-selector"
              accessibilityLabel="gender-switch-selector"
            /> */}
          </div>
          {/* {(panelMode == "collections") && (
						<></>
            // <SidebarCollectionSelect 
            //   onChangeCollections={onChangeCollectionsHook} 
            //   userData={props.userData} 
            //   setPageNavigate={props.setPageNavigate} 
            //   navigation={props.navigation}
            //   refreshSidePanel={props.refreshSidePanel}
            //   setPageNavigateArguments={props.setPageNavigateArguments}
            //   collectionGroups={collectionGroups}
            //   setCollectionGroups={setCollectionGroups}
            //   setCollectionSelected={setCollectionSelected}
            //   selectedCollections={props.selectedCollections
            //   }
            // />
          )}
          {(panelMode == "history") && (
						<></>
            // <SidebarChatHistory 
            //   userData={props.userData} 
            //   setPageNavigateArguments={props.setPageNavigateArguments} 
            //   setPageNavigate={props.setPageNavigate}
            //   refreshSidePanel={props.refreshSidePanel}
            //   chatHistory={props.chatHistory}
            //   setChatHistory={props.setChatHistory}
            //   pageNavigateArguments={props.pageNavigateArguments}
            // />
          )}
          {(panelMode == "tools") && (
						<></>
            // <SidebarToolchains
            //   userData={props.userData}
            //   setUserData={props.setUserData}
            // />
          )} */}
        </div>
        <div style={{
					display: "flex",
          flexDirection: "column", 
          justifyContent: "flex-end", 
          paddingLeft: 20,
					paddingRight: 20,
          paddingBottom: 10,
          paddingTop: 10,
        }}>
          <Button variant="link" onClick={() => {
						navigate("login_page");
          }}>
            <p style={{
              fontSize: 16,
              color: "#E8E3E3",
							textAlign: "left",
							width: "100%"
            }}>
              {"Logout"}
            </p>
          </Button>
          <Button variant="link">
					<p style={{
              fontSize: 16,
              color: "#E8E3E3",
							textAlign: "left",
							width: "100%"
            }}>
              {"Model Settings"}
            </p>
          </Button>
          <Button variant="link" onClick={() => {
						navigate("organization_manager");
          }}>
            <p style={{
              fontSize: 16,
              color: "#E8E3E3",
							textAlign: "left",
							width: "100%"
            }}>
              {"Organizations"}
            </p>
          </Button>
          <Button variant="link" onClick={() => {
            navigate("user_settings");
          }}>
            <p style={{
              fontSize: 16,
              color: "#E8E3E3",
							textAlign: "left",
							width: "100%"
            }}>
              {"User Settings"}
            </p>
          </Button>
        </div>
      </div>
    </div>
	);
}
