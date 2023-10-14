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
import CollectionPreview from './CollectionPreview';

type collectionType = {
  title: string,
  items: number,
  id?: number,
}

type CollectionWrapperProps = {
	onToggleCollapse?: (opened: boolean) => void,
	onToggleSelected?: (selected: boolean) => void,
	children?: any,
	title: string,
  collections: collectionType[]
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(false);
	// const [selected, setSelected] = useState(false);
	const [viewScrollable, setViewScrollable] = useState(false);
	
	const [selected, setSelected] = useState(false);
	const {children, title} = props;
	
	const selectionCircleSize = useRef(new Animated.Value(0)).current;
	const boxHeight = useRef(new Animated.Value(42));
  let selected_values : [boolean, React.Dispatch<React.SetStateAction<boolean>>][] = [];
  for (let i = 0; i < props.collections.length; i++) {
    selected_values.push(useState(false));
  }

  useEffect(() => {
    if (boxHeight > 42) {
      setViewScrollable(true);
    }
  }, [boxHeight]);

  let direct_opened_state = false;
	useEffect(() => {
    direct_opened_state = opened;
    let tmp_cmp = opened;
    Animated.timing(boxHeight.current, {
      toValue: (opened && props.collections.length > 0)?(props.collections.length*45+48):42,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
		setTimeout(() => {
			setViewScrollable(direct_opened_state);
		}, 300)
    if (opened) {
      setViewScrollable(opened);
      // setTimeout(() => {
      // }, 300)
    }
  }, [opened]);

  useEffect(() => {
    Animated.timing(selectionCircleSize, {
      toValue: selected?11:0,
      duration: 100,
			easing: Easing.elastic(1),
      useNativeDriver: false,
    }).start();
    if (selected) {
      for (let i = 0; i < selected_values.length; i++) {
        selected_values[i][1](true);
      }
    }

  }, [selected]);

  // useEffect(() => {
  //   selected_values = [];
  //   for (let i = 0; i < props.collections.length; i++) {
  //     selected_values.push(useState(false));
  //   }
  // }, [props.collections]);

	return (
		<Animated.ScrollView style={{
			width: '100%',
			backgroundColor: '#39393C',
			flexDirection: 'column',
			borderRadius: 20,
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingTop: 8,
			height: boxHeight.current,
			// alignSelf: 'center',
		}} scrollEnabled={false} showsVerticalScrollIndicator={false}>
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
            if (selected == true) {
              for (let i = 0; i < selected_values.length; i++) {
                selected_values[i][1](false);
              }
            }
						setSelected(selected => !selected);
            
						// if (props.onToggleSelected) { props.onToggleSelected(!selected); }
					}}
					>
						{/* {selected && ( */}
							<Animated.View style={{
								backgroundColor: '#23232D',
								height: selectionCircleSize,
								borderRadius: '50%',
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
								transform: opened?"rotate(0deg)":"rotate(90deg)"
							}}
						/>
					</Pressable>
				</View>
			</View>
			
			<ScrollView style={{
				  paddingBottom: 5,
			  }}
			  showsVerticalScrollIndicator={false}
			>
			  {props.collections.map((value : collectionType, index: number) => (
          <View style={{paddingBottom: 5}} key={index}>
            <CollectionPreview
              title={value.title} 
              documentCount={value.items} 
              onToggleSelected={(collection_selected: boolean) => {
                if (selected && !collection_selected) {
                  // selected_values[index][1](false);
                  setSelected(false);
                }
                // if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
              }}
              selectedState={{selected: selected_values[index][0], setSelected: selected_values[index][1]}}
            />
          </View>
        ))}
			</ScrollView>
			
		</Animated.ScrollView>
	);
}