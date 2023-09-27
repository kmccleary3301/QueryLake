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
  Easing
} from "react-native";
import { Feather } from "@expo/vector-icons";

type CodeSegmentExcerpt = {
  text: string,
  color: string,
};

type CodeSegment = CodeSegmentExcerpt[];

type ChatContentExcerpt = string | CodeSegment;

type ChatContent = ChatContentExcerpt[];

type ChatEntry = {
  origin: ("user" | "server"),
  content: ChatContent,
};

type ChatBubbleProps = {
  entry: ChatEntry
};

export default function ChatBubble(props: ChatBubbleProps) {
  

  return (
    <View style={{
      flexDirection: 'column',
      width: "100%",
      paddingBottom: 10,
      paddingRight: 10
    }}>
      <View style={{
        width: 50,
        height:50,
        borderRadius: 25,
        backgroundColor: "#FF0000"
      }}>

      </View>
      <View style={{
        paddingRight: 10, 
        flexDirection: "row", 
        width: "100%",
        // backgroundColor: "#3939FF",
        borderRadius: 10,
      }}>
        <View style={{
          padding: 20,
          maxWidth: "100%",
          // width: "80svw",
          backgroundColor: "#39393C",
          borderRadius: 30,
          
        }}>
          {props.entry.content.map((v : ChatContentExcerpt, k : number) => (typeof v === 'string')?(

            <Text key={k} style={{
              // backgroundColor: "#00FF00"
            }}>
              <Text style={{color: '#E8E3E3'}}>{v}</Text>
            </Text>
          ):( //Code Segment
            <View style={{
              // backgroundColor: "#0000FF"
            }}>
              <Text>
                {v.map((v_2 : CodeSegmentExcerpt, k_2 : number) => (
                  <Text style={{color: v_2.color}}>
                    {v_2.text}
                  </Text>
                ))}
              </Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}