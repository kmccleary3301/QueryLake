import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  Text,
  View,
  Pressable,
  TextInput,
  Platform,
  Animated,
  Easing,
  Image
} from "react-native";
import { Feather } from "@expo/vector-icons";
import Markdown from "@ronradtke/react-native-markdown-display";
import MarkdownRenderer from "../markdown/MarkdownRenderer";

type ChatBubbleProps = {
  origin: ("user" | "server"),
  input: string
};

export default function ChatBubble(props: ChatBubbleProps) {
  const normalTextFont = "Inter-Regular";
  const codeFont = "Consolas";
  const [maxWidth, setMaxWidth] = useState(40);


  const queryLakeIcon = require("../../assets/favicon.png");

  return (
    <View 
      style={{
        flexDirection: Platform.select({web: "row", default: "column"}),
        width: "60vw",
        justifyContent: 'flex-start',
        paddingBottom: 20,
        paddingRight: 10
      }}
    >
      {(props.origin === "user")?(
        <View style={Platform.select({web: {paddingRight: 10}, default: {paddingBottom: 10}})}>
          <View style={{
            width: 40,
            height:40,
            borderRadius: 25,
            backgroundColor: "#E8E3E3",
            justifyContent: 'center',
            alignItems: 'center'
          }}>
            <View style={{
              justifyContent: 'center',
              alignSelf: 'center'
            }}>
              <Text style={{
                fontFamily: normalTextFont,
                fontSize: 24,
              }}>
                {"K"}
              </Text>
            </View>
          </View>
        </View>
      ):(
        <View style={Platform.select({web: {paddingRight: 10}, default: {paddingBottom: 10}})}>
          <Image 
            style={{
              width: 40,
              height:40,
              borderRadius: 25,
            }}
            source={queryLakeIcon}
          />
        </View>
      )}
      <View 
        style={{
          // flex: 1,
          flexDirection: 'row',
          justifyContent: 'flex-start'
        }}
        onLayout={(event) => {
          setMaxWidth(event.nativeEvent.layout.width);
        }}
      >
        {props.input && props.input.length > 0 && (
          <MarkdownRenderer maxWidth={maxWidth} input={props.input} transparentDisplay={(props.origin === "user")}/>
        )}
      </View>
    </View>
  );
}



const markdown_style = {
  'heading1': {
    color: '#E8E3E3',
    FontFace: 'Inter',
  },
}