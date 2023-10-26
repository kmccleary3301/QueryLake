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


  const queryLakeIcon = require("../../assets/favicon.png");

  return (
    <View 
      style={{
        flexDirection: Platform.select({web: "row", default: "column"}),
        width: "100%",
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
      {/* {props.input && props.input.length > 0 && (
        <MarkdownRenderer input={props.input} transparentDisplay={(props.origin === "user")}/>
      )} */}
      {props.input && props.input.length > 0 && (
        <MarkdownRenderer input={props.input} transparentDisplay={(props.origin === "user")}/>
        // <Text>
        //   {props.input}
        // </Text>
      )}
      {/* <View style={{
        paddingRight: 10, 
        flexDirection: "row", 
        width: "100%",
        // backgroundColor: "#3939FF",
        borderRadius: 10,
      }}>
        <View 
          style={{
            
            maxWidth: "100%",
            minWidth: 40,
            minHeight: 40,
            // width: "80svw",
            paddingRight: 50
          }}
        >
          
          <Text 
            style={{
              fontFamily: normalTextFont,
              backgroundColor: "#39393C",
              borderRadius: 15,
              padding: 10,
            }}
            selectable={true}
          >
          {props.entry.content.map((v : ChatContentExcerpt, k : number) => (typeof v === 'string')?(

            <Text 
              key={k} 
              style={{
                fontFamily: normalTextFont,
              // backgroundColor: "#00FF00"
              }}
            >
              <Text style={{color: '#E8E3E3', fontFamily: normalTextFont,}}>{v}</Text>
            </Text>
          ):( //Code Segment
            <View style={{
              // backgroundColor: "#0000FF"
            }}>
              <Text style={{fontFamily: codeFont,}}>
                {v.map((v_2 : CodeSegmentExcerpt, k_2 : number) => (
                  <Text style={{color: v_2.color, fontFamily: codeFont,}}>
                    {v_2.text}
                  </Text>
                ))}
              </Text>
            </View>
          ))}
          </Text>
        </View>
      </View> */}
    </View>
  );
}



const markdown_style = {
  'heading1': {
    color: '#E8E3E3',
    FontFace: 'Inter',
  },
}