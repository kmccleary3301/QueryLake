import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
} from 'react-native';
import { ScrollView, TextInput } from 'react-native-gesture-handler';
import TestUploadBox from './TestUploadBox';
// import SwitchSelector from "react-native-switch-selector";
import SwitchSelector from '../lib/react-native-switch-selector';
import { Feather } from '@expo/vector-icons';
import { useState, useEffect } from 'react';
import CollectionWrapper from './CollectionWrapper';
import CollectionPreview from './CollectionPreview';
import { useDrawerStatus } from '@react-navigation/drawer';
import SidebarCollectionSelect from './SidebarCollectionSelect';
import AnimatedPressable from './AnimatedPressable';
import SidebarChatHistory from './SidebarChatHistory';
import getChatHistory from '../hooks/getChatHistory';
import getUserCollections from '../hooks/getUserCollections';

type selectedState = [
	selected: boolean,
	setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionGroup = {
	title: string,
	toggleSelections: selectedState[],
	selected: selectedState,
	collections: any,
};



type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships: object[],
  is_admin: boolean
};

type SidebarProps = {
  toggleSideBar?: () => void,
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void, 
  userData: userDataType,
  setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  pageNavigateArguments: string,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<any>>,
  refreshSidePanel: string[],
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  setSelectedCollections: React.Dispatch<React.SetStateAction<object>>,
  selectedCollections: object
  // sidebarOpened?: boolean,
}

type panelModeType = "collections" | "history" | "tools";

export default function Sidebar(props: SidebarProps) {
  // console.log(props);
	const [panelMode, setPanelMode] = useState<panelModeType>("collections");
  const [chatHistory, setChatHistory] = useState([]);
	const [collectionGroups, setCollectionGroups] = useState<collectionGroup[]>([]);

  const timeWindows = [
    {title: "Last 24 Hours", cutoff: 24*3600, entries: []},
    {title: "Last 2 Days", cutoff: 2*24*3600, entries: []},
    {title: "Past Week", cutoff: 7*24*3600, entries: []},
    {title: "Past Month", cutoff: 30*24*3600, entries: []},
  ];

  useEffect(() => {
    let chat_history_grabbed = false;
    let collections_grabbed = false;
    if (chatHistory.length == 0) {
      getChatHistory(props.userData.username, props.userData.password_pre_hash, timeWindows.slice(), setChatHistory);
      chat_history_grabbed = true;
    }
    if (collectionGroups.length == 0) {
      getUserCollections(props.userData.username, props.userData.password_pre_hash, setCollectionGroups);
      collections_grabbed = true;
    }
    for (let i = 0; i < props.refreshSidePanel.length; i++) {
      if (!chat_history_grabbed && props.refreshSidePanel[i] === "chat-history") {
        getChatHistory(props.userData.username, props.userData.password_pre_hash, timeWindows.slice(), setChatHistory);
        chat_history_grabbed = true;
      } else if (!collections_grabbed && props.refreshSidePanel[i] === "collections") {
        getUserCollections(props.userData.username, props.userData.password_pre_hash, setCollectionGroups);
        collections_grabbed = true;
      }
    }
  }, [props.refreshSidePanel, props.userData]);

  useEffect(() => {
    let new_selections_state = {};
    for (let i = 0; i < collectionGroups.length; i++) {
      for (let j = 0; j < collectionGroups[i].collections.length; j++) {
        new_selections_state[collectionGroups[i].collections[j]["hash_id"]] = false; //Change to false
      }
    }
    props.setSelectedCollections(new_selections_state);
  }, [collectionGroups]);

  const onChangeCollectionsHook = (collectionGroups: collectionGroup[]) => {
    if (props.onChangeCollections) { props.onChangeCollections(collectionGroups); }
  };

	const icons = {
		aperture: require('../../assets/aperture.svg'),
		clock: require('../../assets/clock.svg'),
		folder: require('../../assets/folder.svg')
	};

	const setCollectionSelected = (collection_hash_id : string, value : boolean) => {
    props.setSelectedCollections((prevState) => ({ ...prevState, [collection_hash_id]: value}));
    // console.log(props.selectedCollections);
  };

	return (
    <View {...props} style={{height: '100vh'}}>
      <View style={{
        backgroundColor: "#17181D", 
        height: "100%", 
        flexDirection: 'column', 
        padding: 0, 
      }}>
        <View style={{
          flex: 5,
          paddingHorizontal: 0,
          // paddingVertical: 10,
          alignItems: 'center',
          flexDirection: 'column',
          justifyContent: 'space-evenly'
        }}>
          <View style={{
            flexDirection: 'row',
            paddingVertical: 7.5,
            paddingHorizontal: 30,
            alignItems: 'center',
            width: '100%',
            justifyContent: 'space-between',
          }}>
            <AnimatedPressable style={{padding: 0}}>
              <Feather name="settings" size={24} color="#E8E3E3" />
            </AnimatedPressable>
            <AnimatedPressable style={{padding: 0}}>
              <Feather name="info" size={24} color="#E8E3E3" />
            </AnimatedPressable>
            <AnimatedPressable style={{padding: 2, borderRadius: 5}} onPress={() => {
              if (props.toggleSideBar) { props.toggleSideBar(); }
            }}>
              <Feather name="sidebar" size={24} color="#E8E3E3" />
            </AnimatedPressable>
          </View>
          <View style={{
            width: '100%',
            paddingHorizontal: 22,
            // alignSelf: 'center'
            paddingBottom: 10,
          }}>
            <SwitchSelector
              initial={0}
              width={"100%"}
              onPress={(value : string) => {
                setPanelMode(value);
                props.setRefreshSidePanel(!props.refreshSidePanel);
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
            />
          </View>
          {(panelMode == "collections") && (
            <SidebarCollectionSelect 
              onChangeCollections={onChangeCollectionsHook} 
              userData={props.userData} 
              setPageNavigate={props.setPageNavigate} 
              navigation={props.navigation}
              refreshSidePanel={props.refreshSidePanel}
              setPageNavigateArguments={props.setPageNavigateArguments}
              collectionGroups={collectionGroups}
              setCollectionGroups={setCollectionGroups}
              setCollectionSelected={setCollectionSelected}
              selectedCollections={props.selectedCollections
              }
            />
          )}
          {(panelMode == "history") && (
            <SidebarChatHistory 
              userData={props.userData} 
              setPageNavigateArguments={props.setPageNavigateArguments} 
              setPageNavigate={props.setPageNavigate}
              refreshSidePanel={props.refreshSidePanel}
              chatHistory={chatHistory}
              setChatHistory={setChatHistory}
              pageNavigateArguments={props.pageNavigateArguments}
            />
          )}
        </View>
        <View style={{
          flexDirection: "column", 
          justifyContent: "flex-end", 
          paddingHorizontal: 20, 
          paddingBottom: 10,
          paddingTop: 10,
        }}>
          <AnimatedPressable onPress={() => {
            if (props.setPageNavigate) { props.setPageNavigate("LoginPage"); }
          }}>
            <Text style={{
              fontSize: 16,
              color: "#E8E3E3",
            }}>
              {"Logout"}
            </Text>
          </AnimatedPressable>
          <AnimatedPressable>
            <Text style={{
              fontSize: 16,
              color: "#E8E3E3",
            }}>
              {"Model Settings"}
            </Text>
          </AnimatedPressable>
          <AnimatedPressable onPress={() => {
            if (props.setPageNavigate) { props.setPageNavigate("OrganizationManager"); }
          }}>
            <Text style={{
              fontSize: 16,
              color: "#E8E3E3",
            }}>
              {"Organizations"}
            </Text>
          </AnimatedPressable>
          <AnimatedPressable onPress={() => {
            if (props.setPageNavigate) { props.setPageNavigate("UserSettings"); }
          }}>
            <Text style={{
              fontSize: 16,
              color: "#E8E3E3",
            }}>
              {"User Settings"}
            </Text>
          </AnimatedPressable>
        </View>
      </View>
    </View>
	);
}

const styles={
	topContainer: {
		
	}
}