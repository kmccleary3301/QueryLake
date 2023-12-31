import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  Text,
  View,
  Platform,
  Image,
  Animated,
  Easing
} from "react-native";
import { Feather } from "@expo/vector-icons";
import Markdown from "@ronradtke/react-native-markdown-display";
import MarkdownRenderer from "../markdown/MarkdownRenderer";
import ChatBubbleSource from "./ChatBubbleSource";
import { ScrollView } from "react-native-gesture-handler";
import globalStyleSettings from "../../globalStyleSettings";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type sourceMetadata = {
  "type": "pdf"
  "collection_type": "user" | "organization" | "global",
  "document": string,
  "document_id": string,
  "document_name": string,
  "location_link_chrome": string,
  "location_link_firefox": string,
} | {
  "type": "web"
  "url": string, 
  "document": string,
  "document_name": string
};

type ChatBubbleProps = {
  role: "user" | "assistant" | "display",
  displayCharacter?: string,
  input: string,
  userData: userDataType,
  sources: {
    document: string,
    metadata: sourceMetadata,
    img?: any
  }[],
  state: "finished" | "searching_web" | "searching_vector_database" | "crafting_query" | "writing" | undefined,
};

export default function ChatBubble(props: ChatBubbleProps) {
  const normalTextFont = "Inter-Regular";
  const [maxWidth, setMaxWidth] = useState(40);
  const [currentWidth, setCurrentWidth] = useState(40);
  const [bubbleWidth, setBubbleWidth] = useState(10);
  const transparentDisplay = (props.role === "user" || props.role === "display");
  const queryLakeIcon = require("../../assets/favicon.png");
  const bubbleHeight = useRef(new Animated.Value(40)).current;
  const sourceBarWidth = useRef(new Animated.Value(10)).current;
  const [targetBubbleHeight, setTargetBubbleHeight] = useState(40);
  const sourcesDividerColor = "#969696";
  const bubbleState = (props.state === undefined)?"finished":props.state
  // useEffect(() => {
  //   console.log("sources:", props.sources);
  // }, [props.sources]);

  useEffect(() => {
    if (props.sources.length > 0) {
      Animated.timing(sourceBarWidth, {
        toValue: 400,
        duration: 100,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }
  }, [props.sources])

  useEffect(() => {
    Animated.timing(bubbleHeight, {
      toValue: targetBubbleHeight+10,
      duration: 50,
      easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [targetBubbleHeight]);

  useEffect(() => {
    Animated.timing(sourceBarWidth, {
      toValue: currentWidth-28,
      duration: 100,
      easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [currentWidth])

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
      {(props.role !== "display") && (
        <>
          {(props.role === "user")?(
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
                    {(props.displayCharacter && props.displayCharacter.length > 0)?props.displayCharacter[0].toUpperCase():"U"}
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
        </>
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
        <View>
          <View style={{
            maxWidth: "60vw",
            minWidth: 40,
            minHeight: 40,
            // width: "80svw",
            paddingRight: 50
          }}>
            <View style={{
              paddingHorizontal: 14,
              paddingVertical: transparentDisplay?0:6,
              backgroundColor: transparentDisplay?"none":"#39393C",
              // backgroundColor: "#1E1E1E",
              borderRadius: 10,
              alignSelf: "center",
              minHeight: 40,
              flexDirection: 'column',
              justifyContent: 'center',
              maxWidth: '100%'
            }} onLayout={(event) => {setCurrentWidth(event.nativeEvent.layout.width)}}>
              {(props.state === "finished" || props.state === "writing" || props.state === undefined)?(
                <>
                  <Animated.ScrollView style={{...{
                    height: bubbleHeight,
                    // justifyContent: transparentDisplay?"center":"flex-start",
                    // alignContent: 'center'
                  }, ...(transparentDisplay)?{width: "60vw"}:{maxWidth: "100%"}}} showsVerticalScrollIndicator={false} showsHorizontalScrollIndicator={false} scrollEnabled={false}>
                    <View 
                      style={{
                        flexDirection: "column",
                        justifyContent: transparentDisplay?"center":"flex-start",
                        alignContent: 'center',
                        minHeight: 40,
                      }}
                      onLayout={(event) => {
                        setBubbleWidth(event.nativeEvent.layout.width);
                        setTargetBubbleHeight(event.nativeEvent.layout.height);
                      }}
                    >
                      {props.input && props.input.length > 0 && (
                        <MarkdownRenderer 
                          finished={(props.state === "finished")}
                          maxWidth={maxWidth} 
                          input={props.input} 
                          bubbleWidth={bubbleWidth}
                          disableRender={(props.role === "user")}
                        />
                      )}
                    </View>
                  </Animated.ScrollView>
                  {(props.sources.length > 0 && props.role === "assistant" && bubbleState === "finished") && (
                    <Animated.View style={{
                      flexDirection: 'column',
                      justifyContent: 'center',
                      width: sourceBarWidth,
                    }}>
                      {(currentWidth > 100) && (
                        <View style={{
                          flexDirection: 'row',
                          maxWidth: '100%'
                        }}>
                          <View style={{height: 20, flex: 1, flexDirection: 'column', justifyContent: 'center'}}>
                            <View style={{
                              backgroundColor: sourcesDividerColor,
                              borderRadius: 1,
                              height: 2,
                              width: '100%'
                            }}/>
                          </View>
                          
                          <Text style={{
                            fontFamily: 'Inter-Light',
                            fontSize: 14,
                            color: sourcesDividerColor,
                            textAlignVertical: 'center',
                            fontStyle: 'italic',
                            paddingHorizontal: 10
                          }}>
                            {"Sources"}
                          </Text>
                          <View style={{height: 20, flex: 1, flexDirection: 'column', justifyContent: 'center'}}>
                            <View style={{
                              backgroundColor: sourcesDividerColor,
                              borderRadius: 1,
                              height: 2,
                              width: '100%'
                            }}/>
                          </View>
                        </View>
                      )}
                      <ScrollView style={{
                        width: sourceBarWidth
                      }} showsHorizontalScrollIndicator={false} horizontal={true}>
                        <View style={{
                          maxWidth: '100%',
                          flexDirection: 'row',
                          flexWrap: 'wrap',
                          justifyContent: 'center'
                        }}>
                          {props.sources.map((value, index : number) => (
                            <ChatBubbleSource
                              key={index}
                              userData={props.userData}
                              metadata={value.metadata}
                              document={value.document}
                            />
                          ))}
                        </View>
                      </ScrollView>
                    </Animated.View>
                  )}
                </>
              ):(
                (props.state === "crafting_query")?(
                  <View>
                    <Text style={{
                      fontFamily: globalStyleSettings.chatRegularFont,
                      fontSize: globalStyleSettings.chatDefaultFontSize,
                      color: globalStyleSettings.colorText
                    }}>
                      {"Crafting Google Query"}
                    </Text>
                  </View>
                ):(
                  (props.state === "searching_web")?(
                    <View>
                      <Text style={{
                        fontFamily: globalStyleSettings.chatRegularFont,
                        fontSize: globalStyleSettings.chatDefaultFontSize,
                        color: globalStyleSettings.colorText
                      }}>
                        {"Searching The Web"}
                      </Text>
                    </View>
                  ):(
                    <View>
                      <Text style={{
                        fontFamily: globalStyleSettings.chatRegularFont,
                        fontSize: globalStyleSettings.chatDefaultFontSize,
                        color: globalStyleSettings.colorText
                      }}>
                        {"Searching Vector Database"}
                      </Text>
                    </View>
                  )
                )

              )}
            </View>
          </View>
        </View>
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