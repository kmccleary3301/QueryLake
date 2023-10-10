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
}

export default function AnimatedPressable(props: AnimatedPressableProps) {
	const [hover, setHover] = useState(false);
  const [pressed, setPressed] = useState(false);
  // const anim = useMemo(() => new Animated.Value(0), [color]);

	const test_url_pointer = () => {
		const url = new URL("http://localhost:5000/uploadfile");
		url.searchParams.append("query", "test test test");
		return url.toString();
	};

	// const selectionCircleSize = new Animated.Value(0);

	const hoverOpacity = useRef(new Animated.Value(0)).current; // Initial value for opacity: 0
	// const collapseIconRotation = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(hoverOpacity, {
      toValue: pressed?0.3:(hover?0.5:1),
      duration: 100,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [pressed]);


  useEffect(() => {
    Animated.timing(hoverOpacity, {
      toValue: hover?0.5:1,
      duration: 100,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [hover]);

  const handleDragOver = (event: any) => {
    setHover(true);
    event.preventDefault();
  };

  const handleDragEnd = (event: any) => {
    setHover(false);
    event.preventDefault();
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