import {
  Text,
  View,
  Animated,
  Easing,
  Pressable
} from "react-native";
import { useState, useRef, useEffect } from "react";
import openDocumentSecure from "../hooks/openDocumentSecure";
import AnimatedPressable from "./AnimatedPressable";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type ChatBubbleSourceProps = {
  icon?: any,
  userData: userDataType,
  document : string,
  metadata: {
    "type": "pdf"
    "collection_type": "user" | "organization" | "global",
    "document_id": string,
    "document": string,
    "document_name": string,
    "location_link_chrome": string,
    "location_link_firefox": string,
    "page": number,
    "rerank_score"?: number
  } | {
    "type": "web"
    "url": string, 
    "document": string,
    "document_name": string,
    "rerank_score"?: number
  },
};

export default function ChatBubbleSource(props: ChatBubbleSourceProps) {
  const [expanded, setExpanded] = useState(false);
  const [delayedExpanded, setDelayedExpanded] = useState(false);
  const maxWidth = useRef(new Animated.Value(140)).current;
  const maxHeight = useRef(new Animated.Value(19)).current
  const [trueContentWidth, setTrueContentWidth] = useState(140);
  const [trueContentHeight, setTrueContentHeight] = useState(60);
  const [firstLineHeight, setFirstLineHeight] = useState(19);
  const [firstLineWidth, setFirstLineWidth] = useState(30);

  const content_reformat = props.document.replaceAll(/(-[\s]*\n)/g, "").replaceAll(/([\s]*\n)/g, " ");
  const opacity = (props.metadata.rerank_score !== undefined)?(Math.min(255, Math.floor(255*(Math.sqrt(props.metadata.rerank_score)*0.8 + 0.2))).toString(16).toUpperCase()):"FF";

  useEffect(() => {
    // console.log("Set expanded to:", expanded, (expanded)?trueContentWidth:140);
    // console.log("Firstlineheight:", firstLineHeight);
    Animated.timing(maxWidth, {
      toValue: 6+((expanded)?Math.min(trueContentWidth, 400):140),
      duration: 250,
      easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
    Animated.timing(maxHeight, {
      toValue: 10+((expanded)?trueContentHeight:19),
      duration: 250,
      easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
    setTimeout(() => {
      setDelayedExpanded(expanded);
    }, expanded?0:250);
  }, [expanded, firstLineHeight, trueContentWidth, trueContentHeight]);

  return (
    <View style={{
      padding: 5
    }}>
      <Pressable onPress={() => {setExpanded(!expanded)}}>
        <Animated.ScrollView 
          style={{
            borderRadius: 10,
            borderWidth: 2,
            borderColor: (props.metadata.document_name)?"#E50914"+opacity:"#88C285"+opacity,
            backgroundColor: "#17181D",
            width: maxWidth,
            height: maxHeight,
            padding: 0,
            paddingRight: 4,
            flexDirection: 'column',
          }} 
          horizontal={true} 
          scrollEnabled={false} 
        >
          <View style={{padding: 3}} onLayout={(event) => {
            setTrueContentWidth(event.nativeEvent.layout.width);
            setTrueContentHeight(event.nativeEvent.layout.height);
          }}>
            <View onLayout={(event) => {
              setFirstLineHeight(event.nativeEvent.layout.height);
              setFirstLineWidth(event.nativeEvent.layout.width);
            }}>
              <Text 
                style={{
                  fontFamily: "Inter-Regular",
                  fontSize: 12,
                  color: "#E8E3E3",
                  paddingHorizontal: 6,
                  paddingVertical: 2,
                  maxWidth: 400
                }}
                numberOfLines={expanded?0:1}
              >
                {props.metadata.document_name}
              </Text>
            </View>
            {(delayedExpanded) && (
              <View>
                <Text 
                  style={{
                    fontFamily: "Inter-Regular",
                    fontSize: 12,
                    color: "#E8E3E3",
                    paddingHorizontal: 6,
                    paddingVertical: 2,
                    maxWidth: 400
                  }}
                  numberOfLines={1}
                >
                  {"Relevance Score: "+((props.metadata.rerank_score !== undefined)?(props.metadata.rerank_score.toString().slice(0, 5)):"N/A")}
                </Text>
                <Text 
                  style={{
                    fontFamily: "Inter-Regular",
                    fontSize: 12,
                    color: "#E8E3E3",
                    paddingHorizontal: 6,
                    paddingVertical: 2,
                    maxWidth: 400
                  }}
                  numberOfLines={1}
                >
                  {"Content"}
                </Text>
                <AnimatedPressable onPress={() => {openDocumentSecure(props.userData, props.metadata)}}>
                  <Animated.Text 
                    style={{
                      fontFamily: "Inter-Thin",
                      fontStyle: 'italic',
                      fontSize: 12,
                      color: "#E8E3E3",
                      paddingHorizontal: 6,
                      paddingVertical: 2,
                      maxWidth: 400,
                      textAlign: 'center'
                      // flexGrow: 1
                    }}
                  >
                    {content_reformat}
                  </Animated.Text>
                </AnimatedPressable>
              </View>
            )}
          </View>
        </Animated.ScrollView>
      </Pressable>
    </View>
  );
}