import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  Pressable,
  TextInput,
  StatusBar,
  Modal,
  Button,
  Alert,
  Platform,
  Animated,
  Easing
} from "react-native";
import Clipboard from "@react-native-clipboard/clipboard";
import { Feather } from "@expo/vector-icons";
import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
import EventSource from "../lib/react-native-server-sent-events";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import Icon from "react-native-vector-icons/FontAwesome";
import ChatBarInputWeb from "../components/ChatBarInputWeb";
import ChatBarInputMobile from "../components/ChatBarInputMobile";
import ChatBubble from "../components/ChatBubble";
import { DrawerActions } from "@react-navigation/native";
import AnimatedPressable from "../components/AnimatedPressable";
import ScrollViewBottomStick from "../components/ScrollViewBottomStick";
import craftUrl from "../hooks/craftUrl";
import ChatWindowSuggestions from "../components/ChatWindowSuggestions";
import generateSearchQuery from "../hooks/generateSearchQuery";

type CodeSegmentExcerpt = {
  text: string,
  color: string,
};

type CodeSegment = CodeSegmentExcerpt[];

type ChatContentExcerpt = string | CodeSegment;

type ChatContent = ChatContentExcerpt[];

type sourceMetadata = {
  metadata: {
    "type": "pdf"
    "collection_type": "user" | "organization" | "global",
    "document_id": string,
    "document": string,
    "document_name": string,
    "location_link_chrome": string,
    "location_link_firefox": string,
  } | {
    "type": "web"
    "url": string, 
    "document": string,
    "document_name": string
  },
  img?: any
};

type ChatEntry = {
  origin: ("user" | "server"),
  // content_392098: ChatContent,
  content_raw_string: string,
  sources?: sourceMetadata[],
};

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type ChatWindowProps = {
  navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  userData: userDataType,
  pageNavigateArguments: any,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  selectedCollections: object
}

function hexToUtf8(s : string)
{
  return decodeURIComponent(
     s.replace(/\s+/g, '') // remove spaces
      .replace(/[0-9a-f]{2}/g, '%$&') // add '%' before each 2 characters
  );
}

export default function ChatWindow(props : ChatWindowProps) {
  const [inputText, setInputText] = useState("");
  const [isEnabled, setIsEnabled] = useState(false);
  const [sseOpened, setSseOpened] = useState(false);
  const [submitInput, setSubmitInput] = useState(false);
  const [newChat, setNewChat] = useState<ChatEntry[]>([]);
  const [inputLineCount, setInputLineCount] = useState(1);
  const [sessionHash, setSessionHash] = useState();
  const [displaySuggestions, setDisplaySuggestions] = useState(true);
  const [displaySuggestionsDelayed, setDisplaySuggestionsDelayed] = useState(true);
  const [animateScroll, setAnimateScroll] = useState(false);
  
  useEffect(() => {
    console.log("PageNavigateChanged");
    const navigate_args = props.pageNavigateArguments.split("-");
    if (props.pageNavigateArguments.length > 0 && navigate_args[0] === "chatSession") {
      setDisplaySuggestions(false);
      setDisplaySuggestionsDelayed(false);
      Animated.timing(opacityChatWindow, {
        toValue: 0,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: 150,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
      
      setTimeout(() => {
        setAnimateScroll(false);
        setNewChat([]);
        setSessionHash(navigate_args[1]);
        const url = craftUrl("http://localhost:5000/api/fetch_session", {
          "username": props.userData.username,
          "password_prehash": props.userData.password_pre_hash,
          "hash_id": navigate_args[1],
        });
        fetch(url, {method: "POST"}).then((response) => {
          console.log(response);
          response.json().then((data) => {
            if (!data["success"]) {
              console.error("Failed to retrieve session");
              return;
            }
            console.log(data);
            let new_entries : ChatEntry[] = [];
            for (let i = 0; i < data.result.length; i++) {
              console.log("Pushing response", data.result[i]);
              if (data.result[i].sources) {
                // let sources_tmp = data.result[i].sources.map((value) => { metadata: value});
                console.log("Got sources:", data.result[i].sources);
                new_entries.push({
                  content_raw_string: hexToUtf8(data.result[i].content).replace(/(?<=^\s*)\s/gm, ""),
                  origin: (data.result[i].type === "user")?"user":"server",
                  sources: data.result[i].sources
                }); //Add sources if they were provided
              } else {
                new_entries.push({
                  content_raw_string: hexToUtf8(data.result[i].content).replace(/(?<=^\s*)\s/gm, ""),
                  origin: (data.result[i].type === "user")?"user":"server"
                }); //Add sources if they were provided
              }
            }
            setNewChat(new_entries);
            setTimeout(() => {
              Animated.timing(opacityChatWindow, {
                toValue: 1,
                // toValue: opened?Math.min(300,(children.length*50+60)):50,
                duration: 150,
                easing: Easing.elastic(0),
                useNativeDriver: false,
              }).start();
            }, 100);
          });
        });
      }, 150);
      // setTimeout(() => {
        
      // }, 250)
      } else {
        setDisplaySuggestions(true);
        setNewChat([]);
      const url = craftUrl("http://localhost:5000/api/create_chat_session", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
      });
      fetch(url, {method: "POST"}).then((response) => {
        console.log(response);
        response.json().then((data) => {
            if (data["success"]) {
              setSessionHash(data["session_hash"]);
            } else {
              console.error("Session hash failed", data["note"]);
            }
        });
      });
    }
  }, [props.pageNavigateArguments]);

  // const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  const PlatformIsWeb = Platform.select({web: true, default: false});


  let genString = "";
  // let termLet: string[] = [];

  const sse_fetch = async function(message : string) {
    let user_entry : ChatEntry = {
      origin: "user",
      content_raw_string: message,
    };
    
    let bot_entry : ChatEntry = {
      origin: "server",
      // content_392098: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
      content_raw_string: "",
      sources: []
    }
    let new_chat = [...newChat, user_entry];
    setNewChat(newChat => [...newChat, user_entry, bot_entry]);
    
    let collection_hash_ids = [];
    let col_keys = Object.keys(props.selectedCollections);
    for (let i = 0; i < col_keys.length; i++) {
      if (props.selectedCollections[col_keys[i]] === true) {
        collection_hash_ids.push(col_keys[i]);
      }
    }
    if (collection_hash_ids.length === 0) {

      initiate_chat_response(message, []);
      return;
    }
    generateSearchQuery(props.userData, new_chat, (query : string) => {
      setDisplaySuggestions(false);
  
      let bot_response_sources : sourceMetadata[] = [];
  
      const url_vector_query = craftUrl("http://localhost:5000/api/query_vector_db", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
        "query": message,
        "collection_hash_ids": collection_hash_ids,
        "k": 10,
        "use_rerank": true
      });
      fetch(url_vector_query, {method: "POST"}).then((response) => {
        console.log(response);
        response.json().then((data) => {
            if (data["success"]) {
              console.log("Vector db recieved");
              console.log(data["results"]);
              for (let i = 0; i < data["results"].length; i++) {
                try {
                  bot_response_sources.push({
                    metadata: {...data["results"][i]["metadata"], "document": data["results"][i]["document"], "type" : "pdf"}
                  })
                } catch {}
              }
              initiate_chat_response(message, bot_response_sources);
            } else {
              console.error("Session hash failed", data["note"]);
              initiate_chat_response(message, []);
            }
        });
      });
    });
  };

  const initiate_chat_response = async function (message : string, bot_response_sources : sourceMetadata[]) {
    
    // setAnimateScroll(true);
    if (sseOpened === true) {
      return;
    }
    // console.log("Starting SSE");
    if (sessionHash === undefined) {
      console.error("Session Hash is null!");
      return;
    }

    let refresh_chat_history = (newChat.length === 0);
    
    setNewChat(prevChat => [...prevChat.slice(0, prevChat.length-1), {...prevChat[prevChat.length-1], "sources": bot_response_sources}]);

    console.log("New sources:", bot_response_sources);

    const url = craftUrl("http://localhost:5000/api/async/chat", {
      "session_hash": sessionHash,
      "query": message,
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "sources": bot_response_sources.map((value : sourceMetadata) => value.metadata)
    });

    console.log("new url:", url.toString())

    // let user_entry : ChatEntry = {
    //   origin: "user",
    //   content_raw_string: message,
    // };
    
    // let bot_entry : ChatEntry = {
    //   origin: "server",
    //   // content_392098: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
    //   content_raw_string: "",
    //   sources: bot_response_sources
    // }
    
    // setActiveBotEntryIndex(newChat.length+1);
    // let active_bot_entry_index = newChat.length+1;
    // setNewChat(newChat => [...newChat, user_entry, bot_entry]);
    // setTemporaryBotEntry(bot_entry);
    // setInputText("");

    console.log(url.toString());
    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", (event) => {
      console.log("Open SSE connection.");
      setSseOpened(true);
    });

    es.addEventListener("message", (event) => {
      // console.log("New message event:", event);
      if (event === undefined || event.data === undefined) return;
      let decoded = event.data.toString();
      decoded = hexToUtf8(decoded);
      // console.log("Decoded SSE String:", [decoded]);
      // decoded = decoded.replace("�", "");
      if (decoded == "-DONE-") {
        // setNewChat(newChat => [...newChat, bot_entry])
        // setTemporaryBotEntry(null);
        console.log("Completed response:");
        console.log(genString);
        es.close();
        if (refresh_chat_history) {
          props.setRefreshSidePanel(["chat-history"]);
        }
      } else if (decoded == "<<<FAILURE>>> | Model Context Length Exceeded") {
        console.error("Maximum Context Length Exceeded");
        es.close();
      } else {
        // for (let key in Object.keys(uri_decode_map)) {
        //   decoded = decoded.replace(key, uri_decode_map[key]);
        // }
        // decoded = decodeURI(decoded);
        // console.log([decoded]);
        if (genString.length == 0) {
          decoded = decoded.replace(/(?<=^\s*)\s/gm, ""); //Strip leading whitespace
        }
        genString += decoded;
        // setChat(genString);
        // bot_entry["content"][0] = genString; //Needs to be cahnged for syntax highlighting.
      
        // bot_entry["content_raw_string"] = genString;
        setNewChat(newChat => [...newChat.slice(0, newChat.length-1), {
          ...newChat[newChat.length-1],
          "content_raw_string": genString
        }])
        // setTemporaryBotEntry(bot_entry);
      }

      // setLog(chat+" HELLOOOOOOOOOOOO"+chat+chat);
    });

    es.addEventListener("error", (event) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", (event) => {
      console.log("Close SSE connection.");
      setSseOpened(false);
    });
  };

  const handleSwitch = (event: any) => {
    setIsEnabled(true);
    event.preventDefault();
    console.log("switch on");
  };

  const toggleSwitch = () => setIsEnabled((previousState) => !previousState);

  const handleDrop = (event: any) => {
    const url = craftUrl("http://localhost:5000/api/uploadfile", {
      "name": props.userData.username,
      "password_prehashed": props.userData.password_pre_hash
    });
    setFileDragHover(false);
    event.preventDefault();
    setFilesPrepared(event.dataTransfer.files);
    console.log("Set files to:", event.dataTransfer.files);
    let formData = new FormData();
    formData.append("file", event.dataTransfer.files[0]);
    const uploader = createUploader({
      destination: {
        method: "POST",
        url: url,
        filesParamName: "file",
      },
      autoUpload: false,
      grouped: true,
      //...
    });

    uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
      console.log(`item ${item.id} started uploading`);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
      console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
      console.log(`item ${item.id} response:`, item.uploadResponse);
    });

    uploader.add(event.dataTransfer.files[0]);
  };


  const onMessageSend = (message : string) => {
    sse_fetch(message);
  };

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
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [inputLineCount]);

  const translateSidebarButton = useRef(new Animated.Value(0)).current;
  const opacitySidebarButton = useRef(new Animated.Value(0)).current;
  const opacityChatWindow = useRef(new Animated.Value(0)).current;
  const opacitySuggestions = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    console.log("Change detected in sidebar:", props.sidebarOpened);
    Animated.timing(translateSidebarButton, {
      toValue: props.sidebarOpened?-320:0,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
    setTimeout(() => {
      Animated.timing(opacitySidebarButton, {
        toValue: props.sidebarOpened?0:1,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: props.sidebarOpened?50:300,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }, props.sidebarOpened?0:300);
  }, [props.sidebarOpened]);

  useEffect(() => {
    
    setTimeout(() => {
      Animated.timing(opacityChatWindow, {
        toValue: displaySuggestions?0:1,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: 150,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }, displaySuggestions?0:150);
    setTimeout(() => {
      Animated.timing(opacitySuggestions, {
        toValue: displaySuggestions?1:0,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: 150,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }, displaySuggestions?150:0);
    setTimeout(() => { setDisplaySuggestionsDelayed(displaySuggestions)}, 150);
  }, [displaySuggestions]);


  return (
    <View style={{
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <View style={{flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <View id="ChatHeader" style={{
          width: "100%",
          height: 40,
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
          <Animated.View style={{
            paddingLeft: 10,
            transform: [{ translateX: translateSidebarButton,},],
            elevation: -1,
            zIndex: -1,
            opacity: opacitySidebarButton,
          }}>
            {props.sidebarOpened?(
              <Feather name="sidebar" size={24} color="#E8E3E3" />
            ):(
              <AnimatedPressable style={{padding: 0}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </AnimatedPressable> 
            )}
          </Animated.View>
          {/* Decide what to put here */}
        </View>
        <View style={{
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          // width: "88%",
          width: "60vw",
          paddingHorizontal: 0,
          // paddingVertical: 24,
        }}>
          {(!displaySuggestionsDelayed) && (

            <Animated.View style={{
              flex: 5,
              opacity: opacityChatWindow
            }}>
              <ScrollViewBottomStick
                showsVerticalScrollIndicator={false}
                animateScroll={animateScroll}
              >
                {newChat.map((v_2 : ChatEntry, k_2 : number) => (
                  <ChatBubble 
                    key={k_2} 
                    origin={v_2.origin} 
                    input={v_2.content_raw_string}
                    userData={props.userData}
                    sources={(v_2.sources)?v_2.sources:[]}
                  />
                ))}
                {/* {temporaryBotEntry && (
                  <ChatBubble origin={temporaryBotEntry.origin} input={temporaryBotEntry.content_raw_string}/>
                )} */}
              </ScrollViewBottomStick>
            </Animated.View>
          )}
          {(displaySuggestionsDelayed) && (
            <Animated.View style={{
              flex: 5,
              opacity: opacitySuggestions
            }}>
              <View style={{
                height: '100%',
                width: '100%',
                flexDirection: 'column',
                justifyContent: 'flex-end'
              }}>
                <ChatWindowSuggestions
                  onSelectSuggestion={(newInput : string) => {
                    setDisplaySuggestions(false);
                    sse_fetch(newInput);
                    // setDefaultInput(newInput);
                  }}
                />
              </View>
            </Animated.View>
          )}
          

          <View id="InputBox" style={{
            flexDirection: 'column',
            justifyContent: 'space-around',
            // flex: 1,
            // height: 200,
            width: '100%',
            paddingVertical: 10,
          }}>
            <View style={{paddingBottom: 5, paddingLeft: 12, flexDirection: "row"}}>
              <View id="Switch" style={{
                // width: 200,
                // width: 140,
                height: 28,
                borderRadius: 14,
                // backgroundColor: '#4D4D56',
                borderWidth: 1,
                borderColor: '#4D4D56',
                flexDirection: 'row',
                justifyContent: 'center',
                alignItems: 'center',
              }}>
                <View style={{paddingLeft: 10}}>
                  <Switch
                    trackColor={{ false: "#4D4D56", true: "#7968D9" }}
                    // thumbColor={isEnabled ? "#D9D9D9" : "#D9D9D9"}
                    thumbColor={"#D9D9D9"}
                    
                    
                    onValueChange={toggleSwitch}
                    value={isEnabled}
                  />
                </View>
                <Text
                  style={{
                    fontFamily: 'Inter-Regular',
                    color: "#4D4D56",
                    fontSize: 12,
                    paddingLeft: 10,
                    paddingRight: 10,
                    // flex: 1,
                    // flexDirection: "column",
                    // alignContent: "space-between",
                    // left: "5%",
                    // bottom: "50%",
                  }}
                >
                  Search web
                </Text>
              </View>
              <View style={{flex: 1}}>

              </View>
            </View>
            {Platform.select({
              web: (
                <ChatBarInputWeb
                  onMessageSend={onMessageSend}
                  handleDrop={handleDrop}
                />
              ),
              default: (
                <ChatBarInputMobile
                  onMessageSend={onMessageSend}
                />
              )
            })}
            
            
            {PlatformIsWeb && (
              <Text style={{
                  fontFamily: "Inter-Regular",
                  color: "#4D4D56",
                  fontSize: 12,
                  fontStyle: "italic",
                  textAlignVertical: 'center',
                  paddingLeft: 12,
                  // backgroundColor: '#4D4D56',
              }}>
                <i>
                Model:{" "}
                  <a href="https://huggingface.co/meta-llama/Llama-2-70b-chat-hf" target="_blank">
                    meta-llama/Llama-2-70b-chat-hf
                  </a>
                {" · "}Generated content may be inaccurate or false.
                </i>
              </Text>
            )}
          </View> 
        </View>
      </View>
      <StatusBar style="auto" />
    </View>
  );
}
