import { useState, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
// import { useFonts } from "expo-font";

// import {
//   View,
//   Text,
//   Pressable,
//   TextInput,
//   StatusBar,
//   Modal,
//   Button,
//   Alert,
//   Platform,
//   Animated,
//   Easing
// } from "react-native";
// import Clipboard from "@react-native-clipboard/clipboard";
// import { Feather } from "@expo/vector-icons";
// import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
// import EventSource from "../lib/react-native-server-sent-events";
import * as Icon from 'react-feather';
import EventSource from "@/lib/react-native-server-sent-events";
// import EventSource from "@/lib/react-native-server-sent-events/src/EventSource.js";
// import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
// import Icon from "react-native-vector-icons/FontAwesome";
// import ChatBarInputWeb from "../components/ChatBarInputWeb";
// import ChatBarInputMobile from "../components/ChatBarInputMobile";
// import ChatBubble from "../components/ChatBubble";
import ChatBubble from "../manual_components/chat-bubble";
// import { DrawerActions } from "@react-navigation/native";
// import AnimatedPressable from "../components/AnimatedPressable";
// import ScrollViewBottomStick from "../components/ScrollViewBottomStick";
import ScrollViewBottomStick from "../manual_components/scrollview-bottom-stick";
// import craftUrl from "@//hooks/craftUrl";
import craftUrl from "@/hooks/craftUrl";
// import ChatWindowSuggestions from "../components/ChatWindowSuggestions";
import generateSearchQuery from "@/hooks/generateSearchQuery";
// import searchGoogle from "../hooks/searchGoogle";
// import DropDownSelection from "../components/DropDownSelection";
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { DropDownSelection } from "@/components/manual_components/dropdown-selection";
import ChatBarInput from "@/components/manual_components/chat-input-bar";
import { userDataType } from "@/globalTypes";
import { sourceMetadata, ChatEntry, selectedCollectionsType } from "@/globalTypes";
import { formEntryType } from "@/components/manual_components/dropdown-selection";
import { Button } from "../ui/button";

type ChatWindowProps = {
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  userData: userDataType,
  pageNavigateArguments: string,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  selectedCollections: selectedCollectionsType
}

function hexToUtf8(s : string)
{
  return decodeURIComponent(
     s.replace(/\s+/g, '') // remove spaces
      .replace(/[0-9a-f]{2}/g, '%$&') // add '%' before each 2 characters
  );
}

export default function ChatWindow(props : ChatWindowProps) {
  // const [inputText, setInputText] = useState("");
  // const [webSearchIsEnabled, setWebSearchIsEnabled] = useState(false);
  const [sseOpened, setSseOpened] = useState(false);
  // const [submitInput, setSubmitInput] = useState(false);
  const [newChat, setNewChat] = useState<ChatEntry[]>([]);
  // const [inputLineCount, setInputLineCount] = useState(1);
  const [sessionHash, setSessionHash] = useState<string | undefined>();
  const [displaySuggestions, setDisplaySuggestions] = useState(false);
  const [displaySuggestionsDelayed, setDisplaySuggestionsDelayed] = useState(false);
  const [animateScroll, setAnimateScroll] = useState(false);
  const [modelInUse, setModelInUse] = useState<formEntryType>({label: "Default", value: "Default"});
  const [availableModels, setAvailableModels] = useState<formEntryType[] | undefined>(undefined);

  useEffect(() => {
		console.log(displaySuggestions);
    if (props.userData.available_models && props.userData.available_models !== undefined) {
      const modelSelections : formEntryType[] = [];
      for (let i = 0; i < props.userData.available_models.local_models.length; i++) {
        modelSelections.push({
          label: props.userData.available_models.local_models[i],
          value: props.userData.available_models.local_models[i]
        });
      }
      for (const [key, value] of Object.entries(props.userData.available_models.external_models)) {
        for (let i = 0; i < value.length; i++) {
          modelSelections.push({
            label: key+"/"+value[i],
            value: [key, value[i]]
          });
        }
      }
      setAvailableModels(modelSelections);
      setModelInUse({
        label: props.userData.available_models.default_model, 
        value: props.userData.available_models.default_model
      });
    }
  }, [props.userData, displaySuggestions]);


  useEffect(() => {
    console.log("PageNavigateChanged");
    const navigate_args = props.pageNavigateArguments.split("-");
    if (props.pageNavigateArguments.length > 0 && navigate_args[0] === "chatSession") {
      setDisplaySuggestions(false);
      setDisplaySuggestionsDelayed(false);
      // Animated.timing(opacityChatWindow, {
      //   toValue: 0,
      //   // toValue: opened?Math.min(300,(children.length*50+60)):50,
      //   duration: 150,
      //   easing: Easing.elastic(0),
      //   useNativeDriver: false,
      // }).start();
      
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
            const new_entries : ChatEntry[] = [];
            for (let i = 0; i < data.result.length; i++) {
              console.log("Pushing response", data.result[i]);
              if (data.result[i].sources) {
                // let sources_tmp = data.result[i].sources.map((value) => { metadata: value});
                console.log("Got sources:", data.result[i].sources);
                new_entries.push({
                  content: hexToUtf8(data.result[i].content),
                  origin: (data.result[i].type === "user")?"user":"assistant",
                  sources: data.result[i].sources
                }); //Add sources if they were provided
              } else {
                new_entries.push({
                  content: hexToUtf8(data.result[i].content),
                  origin: (data.result[i].type === "user")?"user":"assistant"
                }); //Add sources if they were provided
              }
            }
            setNewChat(new_entries);
            // setTimeout(() => {
            //   Animated.timing(opacityChatWindow, {
            //     toValue: 1,
            //     // toValue: opened?Math.min(300,(children.length*50+60)):50,
            //     duration: 150,
            //     easing: Easing.elastic(0),
            //     useNativeDriver: false,
            //   }).start();
            // }, 100);
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
          console.log("create_chat_session:", data);
            if (data["success"]) {
              setSessionHash(data.result);
            } else {
              console.error("Session hash failed", data["note"]);
            }
        });
      });
    }
  }, [props.pageNavigateArguments, props.userData.username, props.userData.password_pre_hash]);

  // const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  // const PlatformIsWeb = Platform.select({web: true, default: false});


  let genString = "";
  // let termLet: string[] = [];

  const sse_fetch = async function(message : string) {
    const user_entry : ChatEntry = {
      origin: "user",
      content: message,
    };
    
    const bot_entry : ChatEntry = {
      origin: "assistant",
      // content_392098: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
      content: "",
      sources: []
    }
    const new_chat = [...newChat, user_entry];
    setNewChat(newChat => [...newChat, user_entry, bot_entry]);
    
    const collection_hash_ids : string[] = [];
    const col_keys : string[] = Object.keys(props.selectedCollections);
    for (let i = 0; i < col_keys.length; i++) {
      if (props.selectedCollections.get(col_keys[i]) === true) {
        collection_hash_ids.push(col_keys[i]);
      }
    }
    if (collection_hash_ids.length === 0) {

      initiate_chat_response(message, []);
      return;
    }
    generateSearchQuery(props.userData, new_chat, (query : string) => {
      setDisplaySuggestions(false);
  
      const bot_response_sources : sourceMetadata[] = [];
  
      const url_vector_query = craftUrl("http://localhost:5000/api/query_vector_db", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
        "query": query+". "+message,
        "collection_hash_ids": collection_hash_ids,
        "k": 10,
        "use_rerank": true,
      });

      fetch(url_vector_query, {method: "POST"}).then((response) => {
        console.log(response);
        response.json().then((data) => {
            if (data["success"]) {
              console.log("Vector db recieved");
              console.log(data["result"]);
              for (let i = 0; i < data["result"].length; i++) {
                try {
                  bot_response_sources.push({
                    metadata: {...data["result"][i]["metadata"], "document": data["result"][i]["document"], "type" : "pdf"}
                  })
                } catch {
									undefined;
								}
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

    const refresh_chat_history = (newChat.length === 0);
    
    // let chat_history_all = newChat.map((x) => {
    //   role: (x.origin === "user")?"user":"assistant", 
    //   content: x.content_raw_string
    // });

    const chat_history_all = [...newChat].map((value) => ({ 
      role: (value.origin === "user")?"user":"assistant", 
      content: value.content
    }));
    chat_history_all.push({
      role: "user",
      content: message
    });

    console.log("Chat history all:", chat_history_all);

    const url = craftUrl("http://localhost:5000/api/async/llm_call_chat_session", {
      "session_hash": sessionHash,
      "history": chat_history_all,
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "context": bot_response_sources.map((value : sourceMetadata) => value.metadata),
      "model_choice": modelInUse.value
    });
    setNewChat(prevChat => [...prevChat.slice(0, prevChat.length-1), {...prevChat[prevChat.length-1], "sources": bot_response_sources, state: 'writing'}]);

    console.log("New sources:", bot_response_sources);
    

    console.log(url.toString());
    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", () => {
      console.log("Open SSE connection.");
      setSseOpened(true);
    });

    es.addEventListener("message", (event : {data : object}) => {
      // console.log("New message event:", event);
      if (event === undefined || event.data === undefined) return;
      let decoded = event.data.toString();
      decoded = hexToUtf8(decoded);
      if (decoded == "<<CLOSE>>") {
        console.log("Completed response:");
        console.log(genString);
        es.close();
        if (refresh_chat_history) {
          props.setRefreshSidePanel(["chat-history"]);
        }
      } else if (decoded == "<<<FAILURE>>> | Model Context Length Exceeded") {
        console.error("Maximum Context Length Exceeded");
        es.close();
        setNewChat(newChat => [...newChat.slice(0, newChat.length-1), {
          ...newChat[newChat.length-1],
          state: 'finished'
        }])
      } else {
        if (genString.length == 0) {
          decoded = decoded.replace(/(?<=^\s*)\s/gm, ""); //Strip leading whitespace
        }
				console.log("Decoded active string:", [decoded]);
        genString += decoded;
        setNewChat(newChat => [...newChat.slice(0, newChat.length-1), {
          ...newChat[newChat.length-1],
          content: genString,
        }])
      }
    });

    es.addEventListener("error", (event : object) => {
			console.log("EventSource Error:", event);
    });

    es.addEventListener("close", () => {
      console.log("Close SSE connection.");
      setSseOpened(false);
      setNewChat(newChat => [...newChat.slice(0, newChat.length-1), {
        ...newChat[newChat.length-1],
        state: 'finished'
      }])
    });
  };


  // const toggleSwitch = () => {console.log("toggled switch to:", !webSearchIsEnabled); setWebSearchIsEnabled((previousState) => !previousState); };

  // const handleDrop = (event: CustomEvent & { dataTransfer: DataTransfer }) => {
  //   const url = craftUrl("http://localhost:5000/api/uploadfile", {
  //     "name": props.userData.username,
  //     "password_prehashed": props.userData.password_pre_hash
  //   });
  //   event.preventDefault();
  //   console.log("Set files to:", event.dataTransfer.files);
  //   const formData = new FormData();
  //   formData.append("file", event.dataTransfer.files[0]);
  //   const uploader = createUploader({
  //     destination: {
  //       method: "POST",
  //       url: url,
  //       filesParamName: "file",
  //     },
  //     autoUpload: false,
  //     grouped: true,
  //     //...
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
  //     console.log(`item ${item.id} started uploading`);
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
  //     console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
  //     console.log(`item ${item.id} response:`, item.uploadResponse);
  //   });

  //   uploader.add(event.dataTransfer.files[0]);
  // };


  const onMessageSend = (message : string) => {
    sse_fetch(message);
  };

  
  // const inputBoxHeight = useRef(new Animated.Value(26)).current;
  
  // useEffect(() => {
  //   if (submitInput && inputText !== "") {
  //     setSubmitInput(false);
  //     setInputText("");
  //     inputBoxHeight.setValue(26);
  //     setInputLineCount(1);
  //   }
  // }, [inputText]);


	// useEffect(() => {
  //   Animated.timing(inputBoxHeight, {
  //     toValue: (24*inputLineCount+6),
  //     // toValue: opened?Math.min(300,(children.length*50+60)):50,
  //     duration: 200,
	// 		easing: Easing.elastic(0),
  //     useNativeDriver: false,
  //   }).start();
  // }, [inputLineCount]);

  
  useEffect(() => {
    // console.log("Change detected in sidebar:", props.sidebarOpened);
		// translate
    // Animated.timing(translateSidebarButton, {
    //   toValue: props.sidebarOpened?-320:0,
    //   // toValue: opened?Math.min(300,(children.length*50+60)):50,
    //   duration: 400,
		// 	easing: Easing.elastic(0),
    //   useNativeDriver: false,
    // }).start();
    // setTimeout(() => {
    //   Animated.timing(opacitySidebarButton, {
    //     toValue: props.sidebarOpened?0:1,
    //     // toValue: opened?Math.min(300,(children.length*50+60)):50,
    //     duration: props.sidebarOpened?50:300,
    //     easing: Easing.elastic(0),
    //     useNativeDriver: false,
    //   }).start();
    // }, props.sidebarOpened?0:300);
  }, [props.sidebarOpened]);

  // useEffect(() => {
    
  //   setTimeout(() => {
  //     Animated.timing(opacityChatWindow, {
  //       toValue: displaySuggestions?0:1,
  //       // toValue: opened?Math.min(300,(children.length*50+60)):50,
  //       duration: 150,
  //       easing: Easing.elastic(0),
  //       useNativeDriver: false,
  //     }).start();
  //   }, displaySuggestions?0:150);
  //   setTimeout(() => {
  //     Animated.timing(opacitySuggestions, {
  //       toValue: displaySuggestions?1:0,
  //       // toValue: opened?Math.min(300,(children.length*50+60)):50,
  //       duration: 150,
  //       easing: Easing.elastic(0),
  //       useNativeDriver: false,
  //     }).start();
  //   }, displaySuggestions?150:0);
  //   setTimeout(() => { setDisplaySuggestionsDelayed(displaySuggestions)}, 150);
  // }, [displaySuggestions]);

	const [chatBarHeightString, setChatBarHeightString] = useState(40);

	// useEffect(() => {
	// 	console.log("Chat bar height:", chatBarHeight, "h-[calc(100vh-180px)]");
	// }, [chatBarHeight]);


	// const testArray = Array(200).fill("Test message Test message Test message Test message Test message Test message ");
	// const testArray = [...Array(200).keys()];
  return (
    <div style={{
			display: "flex",
      flex: 1,
      flexDirection: "row",
      // backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <div style={{display: "flex", flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <div id="ChatHeader" style={{
					display: "flex",
          width: "100%",
          height: 40,
					paddingTop: 8,
          // backgroundColor: "#23232D",
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          
					<div style={{width: 200, display: "flex", flexDirection: "row", justifyContent: "flex-start"}}>
						{(!props.sidebarOpened) && (
							<div style={{paddingLeft: 20}}>
							<Button variant="ghost" style={{paddingLeft: 6, paddingRight: 6}} onClick={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
								<Icon.Sidebar size={24} color="#E8E3E3" />
							</Button> 
							</div>
						)}
					</div>
          <div style={{alignSelf: 'center'}}>
            {(availableModels !== undefined) && (
              <DropDownSelection
                values={availableModels}
                defaultValue={modelInUse}
                setSelection={setModelInUse}
								selection={modelInUse}
              />
            )}
          </div>
          <div
            style={{
              width: 200
            }}
          />
          {/* Decide what to put here */}
        </div>
        <div style={{
					display: "flex",
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          // width: "88%",
          width: "100%",
          paddingRight: 0,
					paddingLeft: 0,
          // paddingVertical: 24,
        }}>
          {(!displaySuggestionsDelayed) && (
						<ScrollViewBottomStick
							showsVerticalScrollIndicator={false}
							animateScroll={animateScroll}
							height_string={"empty"}
						>
							<div style={{
								display: "flex",
								flexDirection: "row",
								justifyContent: "center",
								width: "100%",
							}}>
								<div style={{
									display: "flex",
									flexDirection: "column",
									width: "60vw"
								}}>
									{newChat.map((v_2 : ChatEntry, k_2 : number) => (
										<ChatBubble
											displayCharacter={props.userData.username[0]}
											state={v_2.state}
											key={k_2} 
											role={v_2.origin} 
											input={v_2.content}
											userData={props.userData}
											// sources={(v_2.sources)?v_2.sources:[]}
											sources={[]}
										/>
									))}
								</div>
								<div style={{height: chatBarHeightString + 77, width: 20}}/>
								{/* {temporaryBotEntry && (
									<ChatBubble origin={temporaryBotEntry.origin} input={temporaryBotEntry.content_raw_string}/>
								)} */}
							</div>
						</ScrollViewBottomStick>
          )}
          {/* {(displaySuggestionsDelayed) && (
            <div style={{
              flex: 5,
              opacity: 0
            }}>
              <div style={{
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
              </div>
            </div>
          )}
           */}

          <div id="InputBox" style={{
						display: "flex",
            flexDirection: 'row',
            justifyContent: 'center',
            // flex: 1,
            // height: 200,
            width: '100%',
						paddingBottom: 0,
          }}>
						<div className="bg-background" style={{
							display: "flex",
							flexDirection: 'column',
							justifyContent: 'space-around',
							// flex: 1,
							// height: 200,
							paddingTop: 10,
							paddingBottom: 0,
							zIndex: 2,
						}}>
						
							<div style={{paddingBottom: 0, paddingLeft: 12, display: "flex", flexDirection: "row"}}>
								<div id="Switch" style={{
									// width: 200,
									// width: 140,
									height: 28,
									borderRadius: 14,
									// backgroundColor: '#4D4D56',
									display: "flex",
									borderWidth: 1,
									borderColor: '#4D4D56',
									flexDirection: 'row',
									justifyContent: 'center',
									alignItems: 'center',
								}}>
									<div style={{paddingLeft: 10, paddingRight: 10}}>
										{/* <Switch
											trackColor={{ false: "#4D4D56", true: "#7968D9" }}
											// thumbColor={isEnabled ? "#D9D9D9" : "#D9D9D9"}
											thumbColor={"#D9D9D9"}
											
											
											onValueChange={toggleSwitch}
											value={webSearchIsEnabled}
										/> */}
										<div className="flex items-center space-x-2">
											<Switch id="airplane-mode" />
											<Label htmlFor="airplane-mode">Search Web</Label>
										</div>
									</div>
								</div>
								<div style={{display: "flex", flex: 1}}>

								</div>
							</div>
							
							
							<ChatBarInput
								onMessageSend={onMessageSend}
								onHeightChange={(height : number) => { 
									// setChatBarHeight(height); 
									setChatBarHeightString(height);
								}}
								// handleDrop={handleDrop}
							/>
						</div>

            {/* {Platform.select({
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
            })} */}
            
            
            {/* {PlatformIsWeb && (
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
            )} */}
          </div> 
        </div>
      </div>
      {/* <StatusBar style="auto" /> */}
    </div>
  );
}
