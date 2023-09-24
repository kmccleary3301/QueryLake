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

type CollectionWrapperProps = {
	onToggleCollapse?: (opened: boolean) => void,
	onToggleSelected?: (selected: boolean) => void,
	children: any,
	title: string,
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(true);
	const [selected, setSelected] = useState(false);
	
	const selectionCircleSize = useRef(new Animated.Value(0)).current;

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
			width: '100%',
			backgroundColor: '#39393C',
			flexDirection: 'column',
			borderRadius: 20,
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingHorizontal: 16,
			paddingTop: 10,
			// alignSelf: 'center',
		}}>
			<View style={{
				// height: 200,
				flexDirection: 'row',
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}}>
				<View style={{flexDirection: 'column', justifyContent: 'center'}}>
					<Pressable style={{
						width: 25,
						height: 25,
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
								paddingLeft: 1,
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
						/>
					</Pressable>
				</View>
			</View>
			<View style={{
				paddingVertical: 10,
			}}>
			{props.children}
			</View>
		</View>
	);
}