import {
  View,
  Text,
  useWindowDimensions,
	Pressable,
	Animated,
	Easing
} from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
import { useState, useRef, useEffect, ReactNode } from 'react';
// import { Feather } from '@expo/vector-icons';

type AnimatedPressableProps = {
	style?: React.CSSProperties,
	onPress?: () => void,
  children: ReactNode,
	hoverColor?: string,
  pressColor?: string,
  onHover?: (hovering : boolean) => void,
  invert?: boolean,
}

export default function AnimatedPressable(props: AnimatedPressableProps) {
	const [hover, setHover] = useState(false);
  const [pressed, setPressed] = useState(false);
  // const anim = useMemo(() => new Animated.Value(0), [color]);

  const invert = (props.invert)?props.invert:false;

	const hoverOpacity = useRef(new Animated.Value(0)).current; // Initial value for opacity: 0
	
  useEffect(() => {
    Animated.timing(hoverOpacity, {
      toValue: (invert)?(pressed?0.3:(hover?0.2:0)):(pressed?0.3:(hover?0.5:1)),
      duration: 100,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [pressed]);


  useEffect(() => {
    Animated.timing(hoverOpacity, {
      toValue: (invert)?(hover?0.2:0):(hover?0.5:1),
      duration: 100,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [hover]);

  const handleDragOver = (event: any) => {
    setHover(true);
    event.preventDefault();
    if (props.onHover) { props.onHover(true); }
  };

  const handleDragEnd = (event: any) => {
    setHover(false);
    event.preventDefault();
    if (props.onHover) { props.onHover(false); }
  };

	return (
		<div
      onMouseEnter={handleDragOver}
      onMouseLeave={handleDragEnd}
    >
      <Animated.View style={{
        // backgroundColor: hoverOpacity,
        opacity: hoverOpacity,
        borderRadius: 10,
      }}>
        <Pressable 
          style={(props.style)?props.style:{}}
          onPress={() => {
            if (props.onPress) {
              props.onPress();
            }
          }}
          onPressIn={() => {
            setPressed(true);
          }}
          onPressOut={() => {
            setPressed(false);
          }}
        >
          {props.children}
        </Pressable>
      </Animated.View>
    </div>
	);
}