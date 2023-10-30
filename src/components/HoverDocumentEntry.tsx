import AnimatedPressable from "./AnimatedPressable";
import { Text, View } from "react-native";
import { useState, useRef, useEffect } from "react";
import { Feather } from "@expo/vector-icons";

type HoverDocumentEntryProps = {
  deleteIndex: () => void,
  title: string,
  onPress?: () => void,
  textStyle?: React.CSSProperties,
}

export default function HoverDocumentEntry(props : HoverDocumentEntryProps) {
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
      <View style={hover?{width: '100%', paddingRight: 5}:{flex: 1, paddingRight: 5}}>
        <Text style={(props.textStyle)?props.textStyle:{
          fontFamily: 'Inter-Regular',
          fontSize: 14,
          color: '#E8E3E3',
          paddingVertical: 2,
          // paddingHorizontal: 4
        }} numberOfLines={1}>
          {props.title}
        </Text>
      </View>
      {hover && (
        <AnimatedPressable onPress={props.deleteIndex} style={{paddingRight: 10}}>
          <Feather name="trash" size={16} color={'#E8E3E3'} st/>
        </AnimatedPressable>
      )}
    </AnimatedPressable>
  );
}