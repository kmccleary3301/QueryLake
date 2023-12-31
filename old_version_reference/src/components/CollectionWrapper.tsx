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
import globalStyleSettings from '../../globalStyleSettings';

type collectionType = {
  title: string,
  items: number,
  hash_id: string,
  type: string,
}

type CollectionWrapperProps = {
	onToggleCollapse?: (opened: boolean) => void,
	onToggleSelected?: (selected: boolean) => void,
	children?: any,
	title: string,
  collections: collectionType[],
  setPageNavigate: React.Dispatch<React.SetStateAction<string>>,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
  setCollectionSelected: (collection_hash_id : string, value : boolean) => void,
  collectionSelected: object
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(false);
	// const [selected, setSelected] = useState(false);
	// const [viewScrollable, setViewScrollable] = useState(false);
	
	const [selected, setSelected] = useState(false);
  const [mixedSelection, setMixedSelection] = useState(true);
	const {children, title} = props;
	
	const selectionCircleSize = useRef(new Animated.Value(0)).current;
	const boxHeight = useRef(new Animated.Value(42));

  let direct_opened_state = false;
	useEffect(() => {
    direct_opened_state = opened;
    // let tmp_cmp = opened;
    Animated.timing(boxHeight.current, {
      toValue: (opened && props.collections.length > 0)?(props.collections.length*45+48):42,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [opened, props.collections]);

  useEffect(() => {
    Animated.timing(selectionCircleSize, {
      toValue: selected?11:0,
      duration: 100,
			easing: Easing.elastic(1),
      useNativeDriver: false,
    }).start();
  }, [selected]);

	return (
		<Animated.ScrollView style={{
			width: '100%',
			backgroundColor: globalStyleSettings.collectionWrapperBackgroundColor,
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
						backgroundColor: globalStyleSettings.collectionSelectCircleEmptyColor,
						alignItems: 'center',
						justifyContent: 'center',
						// flexDirection: 'column',
						// paddingLeft: 1,
					}}
					onPress={() => {
            setMixedSelection(false);
            for (let i = 0; i < props.collections.length; i++) {
              props.setCollectionSelected(props.collections[i].hash_id, !selected);
            }
						setSelected(selected => !selected);
						// if (props.onToggleSelected) { props.onToggleSelected(!selected); }
					}}
					>
						{/* {selected && ( */}
							<Animated.View style={{
								backgroundColor: globalStyleSettings.collectionSelectCircleFillColor,
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
						color: globalStyleSettings.colorText,
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
							color={globalStyleSettings.colorText}
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
                props.setCollectionSelected(value.hash_id, collection_selected);
                if (selected && !collection_selected) {
                  // selected_values[index][1](false);
                  setMixedSelection(true);
                  setSelected(false);
                  
                }
                // if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
              }}
              parentSelected={selected}
              parentMixedSelection={mixedSelection}
              onPress={() => {
                props.setPageNavigateArguments("collection-"+value.type+"-"+value.hash_id);
                props.setPageNavigate("EditCollection");
              }}
              selectedPrior={props.collectionSelected[value.hash_id]}
            />
          </View>
        ))}
			</ScrollView>
			
		</Animated.ScrollView>
	);
}