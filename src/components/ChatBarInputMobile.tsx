import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Pressable,
  TextInput,
  Platform,
  Animated,
  Easing
} from "react-native";
import { Feather } from "@expo/vector-icons";

type ChatBarInputProps = {
  onMessageSend?: (message: string) => void,
  handleDrop?: (event: any) => void,
};

export default function ChatBarInputMobile(props: ChatBarInputProps) {
  const [inputText, setInputText] = useState(
    "Write a python function that calculates the Fibonacci sequence up to a given number n. Include type hints and a function description."
  );
  const [chat, setChat] = useState("Sure! Here's a Python function that calculates the Fibonacci sequence up to a given number n:\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nHello");
  const [fileDragHover, setFileDragHover] = useState(false);
  const [submitInput, setSubmitInput] = useState(false);

  const [inputLineCount, setInputLineCount] = useState(1);


  const log_key_press = (e: {
    nativeEvent: { key: string; shiftKey: boolean };
  }) => {
    if (e.nativeEvent.key === "Enter" && e.nativeEvent.shiftKey === false) {
      setSubmitInput(true);
    }
  };
  
  const inputBoxHeight = useRef(new Animated.Value(26)).current;
  
  useEffect(() => {
    if (submitInput && inputText !== "") {
      setSubmitInput(false);
      setInputText("");
      inputBoxHeight.setValue(26);
      setInputLineCount(1);
    }
  }, [inputText]);


	useEffect(() => {
    Animated.timing(inputBoxHeight, {
      toValue: (24*inputLineCount+6),
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 200,
			easing: Easing.elastic(1),
      useNativeDriver: false,
    }).start();
  }, [inputLineCount]);

  const handleDragOver = (event: any) => {
    setFileDragHover(true);
    event.preventDefault();
  };

  const handleDragEnd = (event: any) => {
    setFileDragHover(false);
    event.preventDefault();
  };

  return (
    <View
      id="Input"
      style={{
        // padding: 0,
        // height: 60,
        width: '100%',
        flexDirection: "row",
        backgroundColor: fileDragHover ? "#836454" : "#17181D",
        borderRadius: 15,
        paddingLeft: 10,
      }}
    >
    <View style={{
      // justifyContent: 'space-between',
      width: "100%",
      flexDirection: 'row',
      display: 'flex',
      paddingVertical: 5,
    }}>
      <View id="InputText" style={{
        // flex: 1,
        // flexGrow: 0.5,

        flexShrink: 0.8,
        width: "100%",
        flexDirection: 'column',
        justifyContent: 'center',
        paddingVertical: 5,

      }}>
        <Animated.View style={{height: inputBoxHeight}}>
          <TextInput
            editable
            multiline
            numberOfLines={inputLineCount}
            placeholder="Ask Anything"
            placeholderTextColor={"#4D4D56"}
            value={inputText}
            onKeyPress={(e) => {
                log_key_press(e);
            }}
            onChangeText={(text) => {
              setInputText(text);
              let line_count = (text === "")?1:text.split("\n").length;
              setInputLineCount(Math.min(line_count, 4));
            }}
            style={{ 
                // height: inputBoxHeight,
                color: '#E8E3E3',
                fontSize: 18,
                textAlignVertical: 'center',
            }}
          />
        </Animated.View>
      </View>
      <View id="PressablePadView" style={{
        paddingLeft: 10,
        paddingRight: 10,
        alignSelf: 'center',
      }}>
        <Pressable 
          id="SendButton"
          onPress={() => {
          if (props.onMessageSend) { props.onMessageSend(inputText); }
            setInputText("");
            setInputLineCount(1);
          }}
          style={{
          // padding: 10,
          height: 30,
          width: 30,
          backgroundColor: "#7968D9",
          borderRadius: 15,
          alignItems: 'center',
          justifyContent: 'center'
          }}
        >
          <Feather name="send" size={15} color="#000000" />
        </Pressable>
      </View>
    </View>
    </View>
    
  );
}