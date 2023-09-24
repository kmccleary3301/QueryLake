import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
	Animated,
	Easing
} from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
import { useState, useRef, useEffect } from 'react';
import { Feather } from '@expo/vector-icons';

type CollectionPreviewProps = {
	onToggleSelected?: (selected: boolean) => void,
	selectedState: {
		selected: boolean,
		setSelected: React.Dispatch<React.SetStateAction<boolean>>,
	},
	title: string,
}

export default function CollectionPreview(props: CollectionPreviewProps) {
	const [panelMode, setPanelMode] = useState("");
	// const [opened, setOpened] = useState(true);
	// const [selected, setSelected] = useState(false);
	const {selectedState: {selected, setSelected}, title} = props;

	function changePanelMode(new_mode: string) {
		setPanelMode(new_mode);
		// Fill this out with fetch functionality for
		// user collections, user history, and toolchains.
	}

	// const AnimatedFeather = Animated.createAnimatedComponent(Feather);


	const test_url_pointer = () => {
		const url = new URL("http://localhost:5000/uploadfile");
		url.searchParams.append("query", "test test test");
		return url.toString();
	};

	// const selectionCircleSize = new Animated.Value(0);

	const selectionCircleSize = useRef(new Animated.Value(0)).current; // Initial value for opacity: 0
	// const collapseIconRotation = useRef(new Animated.Value(0)).current;


  useEffect(() => {
    Animated.timing(selectionCircleSize, {
      toValue: selected?12:0,
      duration: 100,
			easing: Easing.elastic(1),
      useNativeDriver: true,
    }).start();
  }, [selected]);

	return (
		<View style={{
			height: 40,
			paddingTop: 10,
			borderRadius: 20,
			backgroundColor: '#23232D',
			flexDirection: 'row',
		}}>
			<View style={{flexDirection: 'column', justifyContent: 'center'}}>
				<Pressable style={{
					width: 25,
					height: 25,
					borderRadius: 12,
					backgroundColor: '#7968D9',
					alignItems: 'center',
					justifyContent: 'center',
				}}
				onPress={() => {
					if (props.onToggleSelected) { props.onToggleSelected(!selected); }
					setSelected(selected => !selected);
				}}
				>
					<Animated.View style={{
						paddingLeft: 1,
						backgroundColor: '#23232D',
						height: selectionCircleSize,
						borderRadius: 6,
						width: selectionCircleSize,
						// opacity: selectionCircleSize
					}}/>
				</Pressable>
			</View>
			<View style={{
				width: '80%',
				flexDirection: 'column',
				justifyContent: 'center',
				paddingLeft: 9,
			}}>
				<Text style={{
					fontSize: 20,
					color: '#E8E3E3',
					textAlign: 'left',
					textAlignVertical: 'center',
				}}>
					{props.title}
				</Text>
			</View>

		</View>
	);
}