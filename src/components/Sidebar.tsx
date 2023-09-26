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

export default function Sidebar(props: any) {
	const [panelMode, setPanelMode] = useState("");
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


	const changePanelMode = (new_mode : string) => {
		setPanelMode(new_mode);
		// Fill this out with fetch functionality for
		// user collections, user history, and toolchains.
	};

	const width = useWindowDimensions().width;
	const height = useWindowDimensions().height;

	const icons = {
		aperture: require('../../assets/aperture.svg'),
		clock: require('../../assets/clock.svg'),
		folder: require('../../assets/folder.svg')
	};

	const big_array = Array(100).fill(0);

	const test_url_pointer = () => {
		const url = new URL("http://localhost:5000/uploadfile");
		url.searchParams.append("query", "test test test");
		return url.toString();
	};

	const toggleMyCollections = (selected: boolean, group_key: number) => {
		// if (selected) {
		for (let i = 0; i < CollectionGroups[group_key].collections.length; i++) {
			CollectionGroups[group_key].toggleSelections[i][1](selected);
		}
		// }
	};

	return (
		// <DrawerContent>
			<View {...props} style={{height: height}}>
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
							<Pressable style={{padding: 0}}>
								<Feather name="settings" size={24} color="#E8E3E3" />
							</Pressable>
							<Pressable style={{padding: 0}}>
								<Feather name="info" size={24} color="#E8E3E3" />
							</Pressable>
							<Pressable style={{padding: 0}}>
								<Feather name="sidebar" size={24} color="#E8E3E3" />
							</Pressable>
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
								height={35}
								borderRadius={10}
								hasPadding={false}
								imageStyle={{
									height: 24,
									width: 24,
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
						<View style={{
							width: '100%',
							// paddingVertical: 10,
							paddingHorizontal: 22,
							paddingTop: 10,
							paddingBottom: 10,
							
						}}>
							<View style={{
								flexDirection: 'row',
								backgroundColor: '#23232D',
								paddingVertical: 10,
								paddingHorizontal: 10,
								borderRadius: 10,
							}}>
								<Feather name="search" size={24} color="#E8E3E3" style={{flex: 1}}/>
								<View style={{width: '86%', paddingRight: 5}}>
									<TextInput
										style={{
											color: '#E8E3E3',
											fontSize: 18,
											outlineStyle: 'none',
										}}
										spellCheck={false}
										placeholder={'Search Public Collections'}
										placeholderTextColor={'#E8E3E3'}
									/>
								</View>
							</View>
						</View>
						<ScrollView style={{
							width: '100%',
							paddingHorizontal: 22,
							// paddingTop: 10,
						}}>
							{CollectionGroups.map((v, k) => (
								<View key={k} style={{
									paddingVertical: 5
								}}>
									<CollectionWrapper key={k} 
										title={CollectionGroups[k].title}
										// onToggleCollapse={() => {console.log("Toggle collapse upper");}} 
										onToggleSelected={(selected: boolean) => {toggleMyCollections(selected, k)}}
										selectedState={{
											selected: CollectionGroups[k].selected[0],
											setSelected: CollectionGroups[k].selected[1]
										}}
									>
										{CollectionGroups[k].collections.map((v_2, k_2) => (
											<CollectionPreview key={k_2}
												style={{
													paddingTop: (k_2===0)?0:10,
												}}
												title={CollectionGroups[k].collections[k_2].title}
												selectedState={{
													selected: CollectionGroups[k].toggleSelections[k_2][0],
													setSelected: CollectionGroups[k].toggleSelections[k_2][1]
												}}
												documentCount={v_2.items}
												onToggleSelected={(collection_selected: boolean) => {
													if (!collection_selected &&  CollectionGroups[k].selected[0]) {
														CollectionGroups[k].selected[1](false);
													}
												}}
											/>
										))}
									</CollectionWrapper>
								</View>
							))}
						</ScrollView>
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
		/* </DrawerContent> */
	);
}

const styles={
	topContainer: {
		
	}
}