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
	style?: React.CSSProperties,
	onToggleSelected?: (selected: boolean) => void,
	selectedState: {
		selected: boolean,
		setSelected: React.Dispatch<React.SetStateAction<boolean>>,
	},
	title: string,
	documentCount: number;
}

export default function CollectionPreview(props: CollectionPreviewProps) {
	const [panelMode, setPanelMode] = useState("");
	// const [opened, setOpened] = useState(true);
	// const [selected, setSelected] = useState(false);
	const {selectedState: {selected, setSelected}, title, documentCount} = props;

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
      useNativeDriver: false,
    }).start();
  }, [selected]);

	return (
		<View style={{
			...props.style,
			width: '100%',
			flexDirection: 'column',
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingHorizontal: 8,
			// alignSelf: 'center',
		}}>
			<View style={{
				height: 40,
				borderRadius: 20,
				backgroundColor: '#23232D',
				flexDirection: 'row',
				paddingLeft: 8,
				paddingRight: -10,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}}>
        <View style={{flex:1, flexDirection: 'row'}}>
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
            width: '100%',
            height: 40,
            flexDirection: 'column',
            justifyContent: 'center',
            paddingLeft: 9,
          }}>
            <View style={{width: '83%'}}>
              <Text style={{
                fontSize: 16,
                color: '#E8E3E3',
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
								backgroundColor: '#D9D9D9',
								color: '#000000',
								fontSize: 9,
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
			</View>
		</View>
	);
}