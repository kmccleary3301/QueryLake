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
import AnimatedPressable from "./AnimatedPressable";

type ChatWindowSuggestionsProps = {
  onSelectSuggestion: (suggestion : string) => void,
  mode?: string
};

export default function ChatWindowSuggestions(props: ChatWindowSuggestionsProps) {

  return (
    <View style={{
      height: '100%',
      flexDirection: 'column',
      justifyContent: 'flex-end'
    }}>
      {defaultSuggestions.map((row, index : number) => (
        <View key={index} style={{
          flexDirection: 'row',
          justifyContent: 'space-around'
        }}>
          {row.map((entry, index_row : number) => (
            <View key={index_row} style={{
              paddingVertical: 5,
              paddingHorizontal: 5,
            }}>
              <AnimatedPressable
                style={{
                  borderRadius: 15,
                  width: '25vw',
                  height: 40,
                  borderColor: '#4D4D56',
                  borderWidth: 2,
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignContent: 'center'
                }}
                onPress={() => {
                  console.log("Changing suggestion to:", entry.text);
                  props.onSelectSuggestion(entry.text);
                }}
              >
                <View>
                  <Text style={{
                    width: '100%',
                    height: '100%',
                    fontFamily: 'Inter-Regular',
                    fontSize: 14,
                    color: '#E8E3E3',
                    textAlignVertical: 'center',
                    textAlign: 'center'
                  }}>
                    {entry.label}
                  </Text>
                </View>
              </AnimatedPressable> 
            </View>
          ))}
        </View>
      ))}

    </View>
  );
}

const defaultSuggestions = [
  [
    {label: "Explain the Naive Bayes Classifier", text: "Give me a formatted set of markdown and latex notes on kernel regression. Include formatted math equations whenever\npossible, and use inline LaTeX styling. Include some example python code using sklearn."},
    {label: "What is a Jacobian?", text: "What is the Jacobian of a function?"}
  ],
  [
    {label: "Sightseeing in Rome", text: "Write an itenerary for a vacation to Rome. Include some of the must-see places, and explain their significance. Format your response in markdown."},
    {label: "Compare storytelling techniques.", text: "Compare storytelling techniques in novels and in films in a concise table across different aspects"}
  ]
]