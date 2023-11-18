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
  origin: ("user" | "server"),
  input: string,
  userData: userDataType,
  sources: {
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
  const transparentDisplay = (props.origin === "user");
  const queryLakeIcon = require("../../assets/favicon.png");
  const bubbleHeight = useRef(new Animated.Value(40)).current;
  const sourceBarWidth = useRef(new Animated.Value(10)).current;
  const [targetBubbleHeight, setTargetBubbleHeight] = useState(40);
  const sourcesDividerColor = "#969696";
  const bubbleState = (props.state === undefined)?"finished":props.state

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
              {}
              {(bubbleState === "finished" || bubbleState === "writing") && (
                <>
                  <Animated.ScrollView style={{
                    height: bubbleHeight,
                    maxWidth: "100%",
                    // justifyContent: transparentDisplay?"center":"flex-start",
                    // alignContent: 'center'
                  }} showsVerticalScrollIndicator={false} showsHorizontalScrollIndicator={false} scrollEnabled={false}>
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
                          maxWidth={maxWidth} 
                          input={props.input} 
                          bubbleWidth={bubbleWidth}
                          disableRender={(props.origin === "user")}
                        />
                      )}
                    </View>
                  </Animated.ScrollView>
                  {(props.sources.length > 0 && props.origin === "server" && bubbleState === "finished") && (
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
                          {props.sources.map((value : { metadata: sourceMetadata, img?: any }, index : number) => (
                            <ChatBubbleSource
                              key={index}
                              userData={props.userData}
                              metadata={value.metadata}
                            />
                          ))}
                        </View>
                      </ScrollView>
                    </Animated.View>
                  )}
                </>
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