import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
} from 'react-native';
import { ScrollView, TextInput } from 'react-native-gesture-handler';
import TestUploadBox from './TestUploadBox';
// import SwitchSelector from "react-native-switch-selector";
import SwitchSelector from '../react-native-switch-selector';
import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import CollectionWrapper from './CollectionWrapper';
import CollectionPreview from './CollectionPreview';
import { useDrawerStatus } from '@react-navigation/drawer';
import SidebarColectionSelect from './SidebarCollectionSelect';
import AnimatedPressable from './AnimatedPressable';

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



const test_collections = [
	{
		"title": "Test Collectionsajdhfkshdkfhskd",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 55
	},
	{
		"title": "Test Collection",
		"items": 555
	},
	{
		"title": "Test Collection sdfasdfasdfsf",
		"items": 5555
	},
	{
		"title": "Test Collection",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 5
	},
	{
		"title": "Test Collection",
		"items": 5
	},
];

type SidebarProps = {
  toggleSideBar?: () => void,
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void, 
  // sidebarOpened?: boolean,
}

type panelModeType = "collections" | "history" | "tools";

export default function Sidebar(props: SidebarProps) {
  // console.log(props);
	const [panelMode, setPanelMode] = useState<panelModeType>("collections");

	let toggleSelections: selectedState[] = [];
	for (let i = 0; i < test_collections.length; i++) {
		toggleSelections.push(useState(false));
	}

	let CollectionGroups : collectionGroup[] = [
		{
			title: "My Collections",
			toggleSelections: [],
			selected: useState(false),
			collections: test_collections,
		},
		{
			title: "Added Collections",
			toggleSelections: [],
			selected: useState(false),
			collections: test_collections,
		}
	];

	const reloadCollectionGroup = (group_key : number) => {
		CollectionGroups[group_key].toggleSelections = [];
		for (let i = 0; i < CollectionGroups[group_key].collections.length; i++) {
			CollectionGroups[group_key].toggleSelections.push(useState(false));
		} 
	};

	for (let i = 0; i < CollectionGroups.length; i++) {
		reloadCollectionGroup(i);
	}

	const [myCollectionsSelected, setMyCollectionsSelected] = useState(false);

  const onChangeCollectionsHook = (collectionGroups: collectionGroup[]) => {
    if (props.onChangeCollections) { props.onChangeCollections(collectionGroups); }
  };

	const changePanelMode = (new_mode : string) => {
		setPanelMode(new_mode);
		// Fill this out with fetch functionality for
		// user collections, user history, and toolchains.
	};

	const icons = {
		aperture: require('../../assets/aperture.svg'),
		clock: require('../../assets/clock.svg'),
		folder: require('../../assets/folder.svg')
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
          }}>
            <SwitchSelector
              initial={0}
              width={"100%"}
              onPress={(value : string) => {
                setPanelMode(value);
                console.log(value);
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
          <SidebarColectionSelect onChangeCollections={onChangeCollectionsHook}/>
        </View>
        <View style={{
          flexDirection: "column", 
          justifyContent: "flex-end", 
          paddingHorizontal: 20, 
          paddingBottom: 15,
          paddingTop: 15,
        }}>
          
          <Pressable>
            <Text style={{
              fontSize: 20,
              color: "#E8E3E3",
            }}>
              {"Model Settings"}
            </Text>
          </Pressable>
          <Pressable>
            <Text style={{
              fontSize: 20,
              color: "#E8E3E3",
            }}>
              {"Manage Collections"}
            </Text>
          </Pressable>
        </View>
      </View>
    </View>
	);
}

const styles={
	topContainer: {
		
	}
}