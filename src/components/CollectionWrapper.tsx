import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
	Animated,
	Easing,
	ScrollView,
} from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
import { useState, useRef, useEffect } from 'react';
import { Feather } from '@expo/vector-icons';

type CollectionWrapperProps = {
	onToggleCollapse?: (opened: boolean) => void,
	onToggleSelected?: (selected: boolean) => void,
	selectedState: {
		selected: boolean,
		setSelected: React.Dispatch<React.SetStateAction<boolean>>,
	},
	children?: any,
	title: string,
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(true);
	// const [selected, setSelected] = useState(false);
	const [viewScrollable, setViewScrollable] = useState(false);
	
	const {selectedState: {selected, setSelected}, children, title,} = props;
	
	const selectionCircleSize = useRef(new Animated.Value(0)).current;
	const boxHeight = useRef(new Animated.Value(50)).current;

	useEffect(() => {
    Animated.timing(boxHeight, {
      toValue: opened?((children?children.length:0)*45+48):42,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
		setTimeout(() => {
			setViewScrollable(opened);
		}, opened?0:300)
  }, [opened]);

  useEffect(() => {
    Animated.timing(selectionCircleSize, {
      toValue: selected?11:0,
      duration: 100,
			easing: Easing.elastic(1),
      useNativeDriver: false,
    }).start();
  }, [selected]);

	return (
		<Animated.View style={{
			width: '100%',
			backgroundColor: '#39393C',
			flexDirection: 'column',
			borderRadius: 20,
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingTop: 8,
			height: boxHeight,
			// alignSelf: 'center',
		}}>
			<View style={{
				// height: 200,
				flexDirection: 'row',
				paddingRight: 16,
        paddingLeft: 12,
				paddingBottom: 8,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}}>
				<View style={{flexDirection: 'column', justifyContent: 'center'}}>
					<Pressable style={{
						width: 21,
						height: 21,
						borderRadius: 12,
						backgroundColor: '#7968D9',
						alignItems: 'center',
						justifyContent: 'center',
						// flexDirection: 'column',
						// paddingLeft: 1,
					}}
					onPress={() => {
						if (props.onToggleSelected) { props.onToggleSelected(!selected); }
						setSelected(selected => !selected);
					}}
					>
						{/* {selected && ( */}
							<Animated.View style={{
								backgroundColor: '#23232D',
								height: selectionCircleSize,
								borderRadius: 6,
								width: selectionCircleSize,
								// opacity: selectionCircleSize
							}}/>
						{/* )} */}
					</Pressable>
				</View>
				<View style={{
					width: '83%',
					flexDirection: 'column',
					justifyContent: 'center',
					paddingLeft: 9,
				}}>
					<Text style={{
						fontSize: 16,
						color: '#E8E3E3',
						textAlign: 'left',
						textAlignVertical: 'center',
            height: 25,
					}}
          numberOfLines={1}
          >
						{title}
					</Text>
				</View>
				<View style={{flexDirection: 'column', justifyContent: 'center'}}>
					<Pressable 
						onPress={() => {
							if (props.onToggleCollapse) { props.onToggleCollapse(!opened); }
							setOpened(opened => !opened);
						}}
					>
						<Feather 
							name="chevron-down" 
							size={24} 
							color="#E8E3E3"
							style={{
								transform: [{rotate: opened?"0deg":"90deg"}]
							}}
						/>
					</Pressable>
				</View>
			</View>
			{viewScrollable &&
			<ScrollView style={{
				paddingBottom: 5,
			}}
			showsVerticalScrollIndicator={false}
			>
			{props.children}
			</ScrollView>
			}
		</Animated.View>
	);
}