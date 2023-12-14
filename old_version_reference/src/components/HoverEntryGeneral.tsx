import AnimatedPressable from "./AnimatedPressable";
import { Text, View } from "react-native";
import { useState } from "react";

type HoverEntryGeneralProps = {
  title: string,
  onPress?: () => void,
  textStyle?: React.CSSProperties,
  children: any,
}

export default function HoverEntryGeneral(props : HoverEntryGeneralProps) {
  const [hover, setHover] = useState(false);
  return (
    <AnimatedPressable 
      style={{
        borderRadius: 4,
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingRight: 4,
      }}
      onHover={setHover}
      onPress={() => {
        if (props.onPress) { props.onPress(); }
      }}
    >
      <View style={{paddingVertical: 3, flex: 1, paddingRight: 5}}>
        <Text style={(props.textStyle)?props.textStyle:{
          fontFamily: 'Inter-Regular',
          fontSize: 14,
          color: '#E8E3E3',
          paddingVertical: 4,
          // paddingHorizontal: 4
        }} numberOfLines={1}>
          {props.title}
        </Text>
      </View>
      {(hover) && (
        <View style={{
          alignSelf: 'center',
          justifyContent: 'center',
          flexDirection: 'row'
        }}>

          {props.children}
        </View>
      )}
    </AnimatedPressable>
  );
}