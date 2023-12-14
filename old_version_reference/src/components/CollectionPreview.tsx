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
import AnimatedPressable from './AnimatedPressable';
import globalStyleSettings from '../../globalStyleSettings';

type CollectionPreviewProps = {
  selectedPrior?: boolean,
	style?: React.CSSProperties,
	onToggleSelected?: (selected: boolean) => void,
	title: string,
	documentCount: number;
  onPress: () => void,
  parentSelected: boolean,
  parentMixedSelection: boolean,
}

export default function CollectionPreview(props: CollectionPreviewProps) {
  const [selected, setSelected] = useState((props.selectedPrior)?props.selectedPrior:false);


  useEffect(()=>{
    if (props.selectedPrior)
      setSelected(props.selectedPrior);
  }, [props.selectedPrior])
	const {title, documentCount} = props;

	const selectionCircleSize = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(selectionCircleSize, {
      toValue: selected?11:0,
      duration: 100,
			easing: Easing.elastic(1),
      useNativeDriver: false,
    }).start();
  }, [selected]);

  useEffect(() => {
    if (props.parentSelected) {
      setSelected(true);
    } else if (!props.parentMixedSelection && !props.parentMixedSelection) {
      setSelected(false);
    }
  }, [props.parentSelected]);

	return (
		<View style={{
			...props.style,
			width: '100%',
			flexDirection: 'column',
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingHorizontal: 4,
			// alignSelf: 'center',
		}}>
			<AnimatedPressable style={{
				height: 40,
				borderRadius: 20,
				backgroundColor: globalStyleSettings.collectionPreviewBackgroundColor,
				flexDirection: 'row',
				paddingLeft: 8,
				paddingRight: -10,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}} onPress={props.onPress}>
        <View style={{flex:1, flexDirection: 'row'}}>
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
                if (props.onToggleSelected) { props.onToggleSelected(!selected); }
                setSelected(selected => !selected);
            }}>
              {/* {selected && ( */}
                <Animated.View style={{
                  backgroundColor: globalStyleSettings.collectionSelectCircleFillColor,
                  height: selectionCircleSize,
                  borderRadius: "50%",
                  width: selectionCircleSize,
                  // opacity: selectionCircleSize
                }}/>
              {/* )} */}
            </Pressable>
          </View>
          <View style={{
            width: '100%',
            height: 40,
            flexDirection: 'column',
            justifyContent: 'center',
            paddingLeft: 9,
          }}>
            <View style={{width: '83%'}}>
              <Text style={{
                fontSize: 16,
                color: globalStyleSettings.colorText,
                textAlign: 'left',
                textAlignVertical: 'center',
                paddingBottom: 3,
              }}
              numberOfLines={1}
              >
                {title}
              </Text>
            </View>
          </View>
        </View>
				<View style={{flexDirection: 'column', justifyContent: 'center', paddingLeft: 5}}>
					{/* Notification count */}
					<View style={{
						// flexDirection: 'row',
						// justifyContent: 'flex-start',
						width: 45,
						paddingRight: 10,
						// alignSelf: 'flex-end',
					}}>
						<View style={{
							flexDirection: 'column',
							alignSelf: 'flex-end',
							// paddingHorizontal: 10,
							borderRadius: 10,
						}}>
							<Text style={{
                fontFamily: 'Inter-Light',
								backgroundColor: globalStyleSettings.collectionPreviewCountBubbleColor,
								color: globalStyleSettings.collectionPreviewCountTextColor,
								fontSize: 11,
								textAlign: 'center',
								alignSelf: 'flex-end',
								borderRadius: 8,
								paddingVertical: 2,
								paddingHorizontal: 6,
								verticalAlign: 'bottom',
							}}>
								{(documentCount <= 999)?documentCount.toString():"999+"}
							</Text>
						</View>
					</View>
				</View>
			</AnimatedPressable>
		</View>
	);
}