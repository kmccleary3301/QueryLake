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

type MarkdownTestComponent = {
  text: string
};

export default function MarkdownTestComponent(props: MarkdownTestComponent) {
  
  return (
    <>
      <Markdown style={{
        
      }}>
        {props.text}
      </Markdown>
    </>
  );
}