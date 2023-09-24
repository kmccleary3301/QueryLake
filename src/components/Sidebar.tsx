import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
} from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';
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

export default function Sidebar(props: any) {
	const [panelMode, setPanelMode] = useState("");
	let bigArray = Array(20).fill(0);
	let toggleSelections: selectedState[] = [];
	for (let i = 0; i < 20; i++) {
		toggleSelections.push(useState(false));
	}


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

	return (
		// <DrawerContent>
			<View {...props}>
				<View style={{
					backgroundColor: "#17181D", 
					height: height, 
					flexDirection: 'column', 
					padding: 0, 
				}}>
					<View style={{
						flex: 5,
						// paddingHorizontal: 22,
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
						<ScrollView style={{
							width: '100%',
							paddingHorizontal: 22,
							paddingTop: 10,
						}}>
							<CollectionWrapper title="My Collections" onToggleCollapse={() => {console.log("Toggle collapse upper");}} onToggleSelected={() => {}}>
								{bigArray.map((v, k) => (
									<CollectionPreview
										title={"Test Collection"}
										selectedState={{
											selected: toggleSelections[k][0],
											setSelected: toggleSelections[k][1]
										}}
									/>
								))}
							</CollectionWrapper>
							<View style={{
								alignItems: 'center',
								justifyContent: 'center'
							}}>
							<TestUploadBox/>
							{big_array.map((v, k) => (
								<Text key={k}>Hello</Text>
							))}
							</View>
						</ScrollView>
					</View>
					<View style={{backgroundColor: "#00FF00", flex: 1}}>

						<ScrollView>
							{big_array.map((v, k) => (
								<Text key={k}>Goodbye</Text>
							))}
						</ScrollView>
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