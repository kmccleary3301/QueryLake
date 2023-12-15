// import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
// import { useFonts } from "expo-font";
// import {
//   Text,
//   View,
//   Platform,
//   Image,
//   Animated,
//   Easing
// } from "react-native";
// import { Feather } from "@expo/vector-icons";
// import Markdown from "@ronradtke/react-native-markdown-display";
// import MarkdownRenderer from "../markdown/MarkdownRenderer";
// import ChatBubbleSource from "./ChatBubbleSource";
// import { ScrollView } from "react-native-gesture-handler";
// import globalStyleSettings from "../../globalStyleSettings";
import ChatBubbleSource from "./chat-bubble-source";
import queryLakeIcon from "@/assets/favicon.png";
import { userDataType } from "@/globalTypes";
import { sourceMetadata } from "@/globalTypes";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"

import MarkdownRenderer from "../markdown/markdown-renderer";
import { useEffect } from "react";

// type userDataType = {
//   username: string,
//   password_pre_hash: string,
// };

// type sourceMetadata = {
//   "type": "pdf"
//   "collection_type": "user" | "organization" | "global",
//   "document": string,
//   "document_id": string,
//   "document_name": string,
//   "location_link_chrome": string,
//   "location_link_firefox": string,
// } | {
//   "type": "web"
//   "url": string, 
//   "document": string,
//   "document_name": string
// };

type ChatBubbleProps = {
  role: "user" | "assistant" | "display",
  displayCharacter?: string,
  input: string,
  userData: userDataType,
  sources: {
    document: string,
    metadata: sourceMetadata,
    img?: string | ArrayBuffer | Blob
  }[],
  state: "finished" | "searching_web" | "searching_vector_database" | "crafting_query" | "writing" | undefined,
};

export default function ChatBubble(props: ChatBubbleProps) {
  // const normalTextFont = "Inter-Regular";
  // const [maxWidth, setMaxWidth] = useState(40);
  // const [currentWidth, setCurrentWidth] = useState(40);
  // const [bubbleWidth, setBubbleWidth] = useState(10);
  const transparentDisplay = (props.role === "user" || props.role === "display");
  // const queryLakeIcon = require("../../assets/favicon.png");
  // const bubbleHeight = useRef(new Animated.Value(40)).current;
  // const sourceBarWidth = useRef(new Animated.Value(10)).current;
  // const [targetBubbleHeight, setTargetBubbleHeight] = useState(40);
  const sourcesDividerColor = "#969696";
  const bubbleState = (props.state === undefined)?"finished":props.state
  
  useEffect(() => {
    console.log("ChatBubble props changed:", props.role, props.input);
  }, [props.role, props.input])

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        width: "60vw",
        justifyContent: 'flex-start',
        paddingBottom: 20,
        paddingRight: 10
      }}
    >
      {(props.role !== "display") && (
        <div style={{paddingRight: 10}}>
          {(props.role === "user")?(
            <Avatar>
              <AvatarFallback>
                <p style={{fontSize: 28, textAlign: "center", display: "flex", padding: 0, height: "100%", flexDirection: "column", justifyContent: "center", paddingBottom: 6}}>
                  {props.userData.username[props.userData.username.length-1]}
                </p>
              </AvatarFallback>
            </Avatar>
          ):(
            <Avatar>
              <AvatarImage src={queryLakeIcon} alt="@shadcn" />
              <AvatarFallback>CN</AvatarFallback>
            </Avatar>
          )}
        </div>
      )}
      <div 
        style={{
          // flex: 1,
          display: "flex",
          flexDirection: 'row',
          justifyContent: 'flex-start'
        }}
      >
        <div>
          <div style={{
            maxWidth: "60vw",
            minWidth: 40,
            minHeight: 40,
            // width: "80svw",
            paddingRight: 50
          }}>
            <div style={{
              paddingLeft: 14,
              paddingRight: 14,
              paddingTop: transparentDisplay?0:6,
              paddingBottom: transparentDisplay?0:6,
              backgroundColor: transparentDisplay?"none":"#39393C",
              // backgroundColor: "#1E1E1E",
              borderRadius: 10,
              alignSelf: "center",
              minHeight: 40,
              display: "flex",
              flexDirection: 'column',
              justifyContent: 'center',
              ...(props.role === "display")?{width: "60vw"}:{maxWidth: "100%"}
            }}>
              {(props.state === "finished" || props.state === "writing" || props.state === undefined)?(
                <>
                  <div style={{
                    // height: bubbleHeight,
                    // justifyContent: transparentDisplay?"center":"flex-start",
                    // alignContent: 'center'
                    maxWidth: "100%",
                  }}>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        justifyContent: transparentDisplay?"center":"flex-start",
                        alignContent: 'center',
                        minHeight: 40,
                        maxWidth: '100%',
                      }}
                    >
                      {props.input && props.input.length > 0 && (
                        <MarkdownRenderer 
                          finished={(props.state === "finished")}
                          // maxWidth={maxWidth} 
                          input={props.input} 
                          // bubbleWidth={bubbleWidth}
                          disableRender={(props.role === "user")}
                        />
                      )}
                    </div>
                  </div>
                  {(props.sources.length > 0 && props.role === "assistant" && bubbleState === "finished") && (
                    <div style={{
                      display: "flex",
                      flexDirection: 'column',
                      justifyContent: 'center',
                      // width: sourceBarWidth,
                    }}>
                      {(true) && (
                        <div style={{
                          flexDirection: 'row',
                          maxWidth: '100%'
                        }}>
                          <div style={{height: 20, flex: 1, flexDirection: 'column', justifyContent: 'center'}}>
                            <div style={{
                              backgroundColor: sourcesDividerColor,
                              borderRadius: 1,
                              height: 2,
                              width: '100%'
                            }}/>
                          </div>
                          
                          <p style={{
                            // fontFamily: 'Inter-Light',
                            fontSize: 14,
                            color: sourcesDividerColor,
                            // textAlignVertical: 'center',
                            fontStyle: 'italic',
                            paddingLeft: 10,
                            paddingRight: 10,
                          }}>
                            {"Sources"}
                          </p>
                          <div style={{height: 20, flex: 1, flexDirection: 'column', justifyContent: 'center'}}>
                            <div style={{
                              backgroundColor: sourcesDividerColor,
                              borderRadius: 1,
                              height: 2,
                              width: '100%'
                            }}/>
                          </div>
                        </div>
                      )}
                      <div style={{ // Horizontal Scroll Area
                        // width: sourceBarWidth
                        display: "flex",
                        flexGrow: 1,
                      }}>
                        <div style={{
                          maxWidth: '100%',
                          display: "flex",
                          flexDirection: 'row',
                          flexWrap: 'wrap',
                          justifyContent: 'center'
                        }}>
                          {props.sources.map((value, index : number) => (
                            <ChatBubbleSource
                              key={index}
                              userData={props.userData}
                              metadata={value.metadata.metadata}
                              document={value.document}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ):(
                (props.state === "crafting_query")?(
                  <div>
                    <p style={{
                      // fontFamily: globalStyleSettings.chatRegularFont,
                      fontSize: 14,
                      color: "#E8E3E3"
                    }}>
                      {"Crafting Google Query"}
                    </p>
                  </div>
                ):(
                  (props.state === "searching_web")?(
                    <div>
                      <p style={{
                        fontSize: 14,
                        color: "#E8E3E3"
                      }}>
                        {"Searching The Web"}
                      </p>
                    </div>
                  ):(
                    <div>
                      <p style={{
                        fontSize: 14,
                        color: "#E8E3E3"
                      }}>
                        {"Searching Vector Database"}
                      </p>
                    </div>
                  )
                )

              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}