import AnimatedPressable from "./AnimatedPressable";
import { Text, View } from "react-native";
import { useState, useRef, useEffect } from "react";
import { Feather } from "@expo/vector-icons";

type HoverDocumentEntryProps = {
  deleteIndex: () => void,
  title: string,
  onPress?: () => void,
  iconColor?: string,
  textStyle?: React.CSSProperties,
  style?: React.CSSProperties,
  disableOpacity?: boolean
}

export default function HoverDocumentEntry(props : HoverDocumentEntryProps) {
  const [hover, setHover] = useState(false);
  
  return (
    <AnimatedPressable 
      disableOpacity={(props.disableOpacity)?props.disableOpacity:false}
      style={{...{
        borderRadius: 4,
        paddingVertical: 1,
        flexDirection: 'row',
        justifyContent: 'space-around',
        paddingRight: 4,
        maxWidth: "100%",
        height: 28,
        // borderWidth: 2,
        // borderColor: "#FF0000",
      }, ...(props.style)?props.style:{}}}
      onHover={setHover}
      onPress={() => {
        if (props.onPress) { props.onPress(); }
      }}
    >
      <View style={{...{
        flex: 1, 
        maxWidth: '100%',
        height: '100%',
        alignContent: 'center',
      }}}>
        <View style={{
          justifyContent: 'center',
          alignSelf: 'center',
          // borderWidth: 2,
          // borderColor: "#FF0000",
          height: "100%",
          width: '100%'
        }}>
          <Text style={{...{
            fontFamily: 'Inter-Regular',
            fontSize: 14,
            color: '#E8E3E3',
            // paddingVertical: 2,

            // height: "100%",
            // textAlignVertical: 'center',
            textAlign: 'left',
            maxWidth: "100%"
            // paddingHorizontal: 4
          }, ...(props.textStyle)?props.textStyle:{}}} numberOfLines={1}>
            {props.title}
          </Text>
        </View>
      </View>

      {hover && (
        <View style={{
          justifyContent: 'center',
          alignSelf: 'center',
          // borderWidth: 2,
          // borderColor: "#FF0000",
          height: 30,
          paddingLeft: 10
        }}>
          <AnimatedPressable onPress={props.deleteIndex} style={{flexDirection: 'column', alignContent: 'center'}}>
            <Feather name="trash" size={14} color={(props.iconColor)?props.iconColor:'#E8E3E3'} st/>
          </AnimatedPressable>
        </View>
      )}
    </AnimatedPressable>
  );
}