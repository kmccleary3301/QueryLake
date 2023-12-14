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


type MembershipPreviewProps = {
  selectedPrior?: boolean,
	style?: React.CSSProperties,
	title: string,
  onDecision?: (accepted : boolean) => void,
  onClick?: () => void,
}

export default function MembershipPreview(props: MembershipPreviewProps) {

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
				backgroundColor: '#23232D',
				flexDirection: 'row',
				paddingLeft: 8,
				paddingRight: -10,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}} onPress={props.onPress}>
        <View style={{flex:1, flexDirection: 'row'}}>
          
          <View style={{
            width: '100%',
            height: 40,
            flexDirection: 'column',
            justifyContent: 'center',
            paddingLeft: 9,
          }}>
            <View style={{width: '80%'}}>
              <Text 
                style={{
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
            <AnimatedPressable style={{
              flexDirection: 'column',
							alignSelf: 'flex-end',
							// paddingHorizontal: 10,
							borderRadius: 10,
            }}>
              <Feather name="check" size={24} color="#E8E3E3" />
            </AnimatedPressable>
            <AnimatedPressable style={{
              flexDirection: 'column',
              alignSelf: 'flex-end',
              // paddingHorizontal: 10,
              borderRadius: 10,
            }}>
              <Feather name="x" size={24} color="#E8E3E3" />
            </AnimatedPressable>
					</View>
				</View>
			</AnimatedPressable>
		</View>
	);
}