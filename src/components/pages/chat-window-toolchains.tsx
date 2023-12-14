import { useState, useRef, useEffect, useCallback } from "react";
// import EventSource from "./src/react-native-server-sent-events";
// import { useFonts } from "expo-font";
// import {
//   View,
//   Text,
//   StatusBar,
//   Linking,
//   Platform,
//   Animated,
//   Easing,
//   ActivityIndicator
// } from "react-native";
// import Clipboard from "@react-native-clipboard/clipboard";
// import { Feather } from "@expo/vector-icons";
// import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
// import EventSource from "../lib/react-native-server-sent-events";
import EventSource from "@/lib/react-native-server-sent-events";
// import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import toolchainEventCall from "@/hooks/chat-window-hooks.tsx/toolchain-event-call";
import * as Icon from 'react-feather';
// import Icon from "react-native-vector-icons/FontAwesome";
// import ChatBarInputWeb from "../components/ChatBarInputWeb";
// import ChatBarInputMobile from "../components/ChatBarInputMobile";
// import ChatBubble from "../components/ChatBubble";
import ChatBubble from "../manual_components/chat-bubble";
// import { DrawerActions } from "@react-navigation/native";
// import AnimatedPressable from "../components/AnimatedPressable";
import AnimatedPressable from "../manual_components/animated-pressable";
// import ScrollViewBottomStick from "../components/ScrollViewBottomStick";
import ScrollViewBottomStick from "../manual_components/scrollview-bottom-stick";
// import craftUrl from "../hooks/craftUrl";
import craftUrl from "@/hooks/craftUrl";
// import ChatWindowSuggestions from "../components/ChatWindowSuggestions";
// import generateSearchQuery from "../hooks/generateSearchQuery";
// import generateSearchQuery from "@/hooks/generateSearchQuery";
// import searchGoogle from "../hooks/searchGoogle";
// import searchGoogle from "@/hooks/searchGoogle";
// import DropDownSelection from "../components/DropDownSelection";
import { DropDownSelection, formEntryType } from "../manual_components/dropdown-selection";
// import HoverDocumentEntry from "../components/HoverDocumentEntry";
// import HoverDocumentEntry from "../manual_components/hover_document_entry";
import { 
	sourceMetadata, 
	ChatEntry, 
	selectedCollectionsType, 
	userDataType, 
	sessionStateType, 
	toolchainEntry, 
	displayType, 
	buttonCallback,
	genericArrayType,
	genericMapValueType
} from "@/globalTypes";
import { motion, useAnimation } from "framer-motion";
import { Loader } from 'lucide-react';
import uploadDocsToSession from "@/hooks/chat-window-hooks.tsx/upload-docs-to-session";
import ChatBarInput from "../manual_components/chat-input-bar";
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { MessageEvent, ErrorEvent } from "@/lib/react-native-server-sent-events";



// type toolchainEntry = {
//   name: string,
//   id: string,
//   category: string
//   chat_window_settings: {
//     display: displayType[],
//     max_files: number,
//     enable_rag: boolean,
//     events_available: string[]
//   },
// };

// type userDataType = {
//   username: string,
//   password_pre_hash: string,
//   serp_key?: string,
//   available_models?: {
//     default_model: string,
//     local_models: string[],
//     external_models: object
//   },
//   selected_toolchain: toolchainEntry,
// };

type ChatWindowToolchainProps = {
  // navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  userData: userDataType,
  pageNavigateArguments: string,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  selectedCollections: selectedCollectionsType
}

type uploadQueueEntry = {
  fileName: string,
  hash_id: string,
}

function hexToUtf8(s : string)
{
  return decodeURIComponent(
     s.replace(/\s+/g, '') // remove spaces
      .replace(/[0-9a-f]{2}/g, '%$&') // add '%' before each 2 characters
  );
}

export default function ChatWindowToolchain(props : ChatWindowToolchainProps) {
  const [displayChat, setDisplayChat] = useState<ChatEntry[]>([]);
  const [temporaryChat, setTemporaryChat] = useState<ChatEntry | undefined>();
  // const [displayFiles, setDisplayFiles] = useState<any[] | undefined>();
  const [sessionState, setSessionState] = useState<sessionStateType>(new Map<string, genericMapValueType>([]));
  const [displayMappings, setDisplayMappings] = useState<displayType[]>([]);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  // const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [userQuestionEventEnabled, setUserQuestionEventEnabled] = useState(false);
  const [userFileEventEnabled, setUserFileEventEnabled] = useState(false);

  const [uploadEventQueue, setUploadEventQueue] = useState<uploadQueueEntry[]>([])
  const [uploadEventActive, setUploadEventActive] = useState(false);
  const [eventActive, setEventActive] = useState<string | undefined>();
  const [buttonCallbacks, setButtonCallbacks] = useState<buttonCallback[]>([]);
  const [entryFired, setEntryFired] = useState(false);
  // const [nodeStreamOutputQueue, setNodeStreamOutputQueue] = useState<string[]>([]);


  // const [enableRAG, setEnableRag] = useState(false);
  // const [maxFiles, setMaxFiles] = useState(0);

  // const [webSearchIsEnabled, setWebSearchIsEnabled] = useState(false);
  const [globalGenerator, setGlobalGenerator] = useState<EventSource | undefined>();
  
  // const [inputText, setInputText] = useState("");
  // const [sseOpened, setSseOpened] = useState(false);
  // const [submitInput, setSubmitInput] = useState(false);
  // const [inputLineCount, setInputLineCount] = useState(1);
  const [sessionHash, setSessionHash] = useState<string | undefined>();
  const [displaySuggestions, setDisplaySuggestions] = useState(true);
  const [displaySuggestionsDelayed, setDisplaySuggestionsDelayed] = useState(true);
  const [animateScroll, setAnimateScroll] = useState(false);
  // const [modelInUse, setModelInUse] = useState({label: "Default", value: "Default"});
	const modelInUse = useRef<formEntryType>({label: "Default", value: "Default"});
  const [availableModels, setAvailableModels] = useState<{label : string, value : string | string[]}[]>([]);

	const [selectedToolchain, setSelectedToolchain] = useState<toolchainEntry>(props.userData.selected_toolchain);


	useEffect(() => { console.log(displaySuggestions, displaySuggestionsDelayed, animateScroll)}, [displaySuggestions, displaySuggestionsDelayed, animateScroll]);

  const configureChatWindowAccordingToToolchain = useCallback((toolchain : toolchainEntry) => {
    const chat_config = toolchain.chat_window_settings;
    console.log("Configuring chat window with config:", chat_config);
    setDisplayMappings(chat_config.display);
    const button_callbacks : buttonCallback[] = [];
    for (let i = 0; i < chat_config.display.length; i++) {
      const display_entry = chat_config.display[i];
      if (display_entry.display_as === "chat") {
        setDisplayChat([]);
      } else if (display_entry.display_as === "button") {
        button_callbacks.push(display_entry)
      }
    }
    setButtonCallbacks(button_callbacks);
    // setMaxFiles(chat_config.max_files);
    // setEnableRag(chat_config.enable_rag);
    // setAvailableEvents(chat_config.events_available);
    const hooks_enabled = {
      "file_event": false,
      "question_event": false
    }

    for (let i = 0; i < chat_config.events_available.length; i++) {
      const event_id = chat_config.events_available[i];
      if (event_id === "user_file_upload_event") { hooks_enabled["file_event"] = true; }
      else if (event_id === "user_question_event") { hooks_enabled["question_event"] = true; }
    }
    setUserFileEventEnabled(hooks_enabled["file_event"]);
    setUserQuestionEventEnabled(hooks_enabled["question_event"])
    return hooks_enabled
  }, []);

  useEffect(() => {
    console.log("user_file:", userFileEventEnabled);
    console.log("user_chat:", userQuestionEventEnabled);
  }, [userFileEventEnabled, userQuestionEventEnabled]);

  useEffect(() => {
		if (props.userData.selected_toolchain !== selectedToolchain) {
			setSelectedToolchain(props.userData.selected_toolchain);
		}

    if (props.userData.available_models && props.userData.available_models !== undefined) {
      const modelSelections = [];
      for (let i = 0; i < props.userData.available_models.local_models.length; i++) {
        modelSelections.push({
          label: props.userData.available_models.local_models[i],
          value: props.userData.available_models.local_models[i]
        });
      }
      for (const [key] of Object.entries(props.userData.available_models.external_models)) {

        // console.log(`${key}: ${value}`);
        for (let i = 0; i < props.userData.available_models.external_models[key].length; i++) {
          modelSelections.push({
            label: key+"/"+props.userData.available_models.external_models[key][i],
            value: [key, props.userData.available_models.external_models[key][i]]
          });
        }
      }
      setAvailableModels(modelSelections);
      modelInUse.current = {
        label: props.userData.available_models.default_model, 
        value: props.userData.available_models.default_model
      };
    }
  }, [props.userData, selectedToolchain]);


  
  
  // useEffect(() => {
  //   console.log("Modified session hash:", sessionHash);
  // }, [sessionHash]);
  // const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  // const PlatformIsWeb = Platform.select({web: true, default: false});
	// const PlatformIsWeb = true;

  // let genString = "";
  // let termLet: string[] = [];

  // const sse_fetch = async function(message : string) {
  //   const user_entry : ChatEntry = {
  //     role: "user",
  //     content: message,
  //   };
    
  //   const bot_entry : ChatEntry = {
  //     role: "assistant",
  //     // content_392098: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
  //     content: "",
  //     sources: []
  //   }
	// 	const display_chat_get : ChatEntry[] = (displayChat !== undefined)?displayChat:[];

  //   const new_chat = [...display_chat_get, user_entry];
  //   setDisplayChat([...new_chat, user_entry, bot_entry]);
    
  //   const collection_hash_ids : string[] = [];
  //   const col_keys = Object.keys(props.selectedCollections);
  //   for (let i = 0; i < col_keys.length; i++) {
  //     if (props.selectedCollections.get(col_keys[i]) === true) {
  //       collection_hash_ids.push(col_keys[i]);
  //     }
  //   }
  //   if (collection_hash_ids.length === 0) {

  //     initiate_chat_response(message, []);
  //     return;
  //   }
  //   generateSearchQuery(props.userData, new_chat, (query : string) => {
  //     setDisplaySuggestions(false);
  
  //     const bot_response_sources : sourceMetadata[] = [];
  
  //     const url_vector_query = craftUrl("http://localhost:5000/api/query_vector_db", {
  //       "username": props.userData.username,
  //       "password_prehash": props.userData.password_pre_hash,
  //       "query": query+". "+message,
  //       "collection_hash_ids": collection_hash_ids,
  //       "k": 10,
  //       "use_rerank": true,
  //     });

  //     fetch(url_vector_query, {method: "POST"}).then((response) => {
  //       console.log(response);
  //       response.json().then((data) => {
  //         if (data["success"]) {
  //           console.log("Vector db recieved");
  //           console.log(data["result"]);
  //           for (let i = 0; i < data["result"].length; i++) {
  //             try {
  //               bot_response_sources.push({
  //                 metadata: {...data["result"][i]["metadata"], "document": data["result"][i]["document"], "type" : "pdf"}
  //               })
  //             } catch {
	// 							true;
	// 						}
  //           }
  //           initiate_chat_response(message, bot_response_sources);
  //         } else {
  //           console.error("Session hash failed", data["note"]);
  //           initiate_chat_response(message, []);
  //         }
  //       });
  //     });
  //   });
  // };
  
  // const initiate_chat_response = async function (message : string, bot_response_sources : sourceMetadata[]) {
  //   // if 
  //   // setAnimateScroll(true);
  //   if (sseOpened === true) {
  //     return;
  //   }
  //   // console.log("Starting SSE");
  //   if (sessionHash === undefined) {
  //     console.error("Session Hash is null!");
  //     return;
  //   }

  //   const refresh_chat_history = (displayChat.length === 0);

  //   const chat_history_all = [...displayChat].map((value) => ({ 
  //     role: (value.origin === "user")?"user":"assistant", 
  //     content: value.content
  //   }));
  //   chat_history_all.push({
  //     role: "user",
  //     content: message
  //   });

  //   console.log("Chat history all:", chat_history_all);

  //   const url = craftUrl("http://localhost:5000/api/async/llm_call_chat_session", {
  //     "session_hash": sessionHash,
  //     "history": chat_history_all,
  //     "username": props.userData.username,
  //     "password_prehash": props.userData.password_pre_hash,
  //     "context": bot_response_sources.map((value : sourceMetadata) => value.metadata),
  //     "model_choice": modelInUse.current.value
  //   });
  //   setDisplayChat(prevChat => [...prevChat.slice(0, prevChat.length-1), {...prevChat[prevChat.length-1], "sources": bot_response_sources, state: 'writing'}]);

  //   console.log("New sources:", bot_response_sources);
  //   let genString = "";

  //   console.log(url.toString());
  //   const es = new EventSource(url, {
  //     method: "GET",
  //   });

  //   es.addEventListener("open", () => {
  //     console.log("Open SSE connection.");
  //     setSseOpened(true);
  //   });

  //   es.addEventListener("message", (event : MessageEvent) => {
  //     // console.log("New message event:", event);
  //     if (event === undefined || event.data === undefined) return;
  //     let decoded = event.data.toString();
  //     decoded = hexToUtf8(decoded);
  //     // console.log("Decoded SSE String:", [decoded]);
  //     // decoded = decoded.replace("�", "");
  //     if (decoded == "-DONE-") {
  //       // setNewChat(newChat => [...newChat, bot_entry])
  //       // setTemporaryBotEntry(null);
  //       console.log("Completed response:");
  //       console.log(genString);
  //       es.close();
  //       if (refresh_chat_history) {
  //         props.setRefreshSidePanel(["chat-history"]);
  //       }
  //     } else if (decoded == "<<<FAILURE>>> | Model Context Length Exceeded") {
  //       console.error("Maximum Context Length Exceeded");
  //       es.close();
  //       setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
  //         ...newChat[newChat.length-1],
  //         state: 'finished'
  //       }])
  //     } else {
  //       // for (let key in Object.keys(uri_decode_map)) {
  //       //   decoded = decoded.replace(key, uri_decode_map[key]);
  //       // }
  //       // decoded = decodeURI(decoded);
  //       // console.log([decoded]);
  //       if (genString.length == 0) {
  //         decoded = decoded.replace(/(?<=^\s*)\s/gm, ""); //Strip leading whitespace
  //       }
  //       genString += decoded;
  //       // setChat(genString);
  //       // bot_entry["content"][0] = genString; //Needs to be cahnged for syntax highlighting.
      
  //       // bot_entry["content_raw_string"] = genString;
  //       setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
  //         ...newChat[newChat.length-1],
  //         "content_raw_string": genString,
  //       }])
  //       // setTemporaryBotEntry(bot_entry);
  //     }

  //     // setLog(chat+" HELLOOOOOOOOOOOO"+chat+chat);
  //   });

  //   es.addEventListener("error", (event : ErrorEvent) => {
  //     if (event.type === "error") {
  //       console.error("Connection error:", event.message);
  //     } else if (event.type === "exception") {
  //       console.error("Error:", event.message, event.error);
  //     }
  //   });

  //   es.addEventListener("close", () => {
  //     console.log("Close SSE connection.");
  //     setSseOpened(false);
  //     setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
  //       ...newChat[newChat.length-1],
  //       state: 'finished'
  //     }])
  //   });
  // };

  // const toggleSwitch = () => {console.log("toggled switch to:", !webSearchIsEnabled); setWebSearchIsEnabled((previousState) => !previousState); };

  // const handleDrop = (event: any) => {
  //   event.preventDefault();
  //   const new_files = [...uploadFiles, ...event.dataTransfer.files];
  //   setUploadFiles(new_files);
  // };

  const upload_docs_to_session = useCallback((session_hash_id : string, on_finish : () => void) => {
		if (sessionHash !== undefined) {
			uploadDocsToSession({
				userData: props.userData,
				session_hash: sessionHash,
				collection_hash_id: session_hash_id,
				on_finish: on_finish,
				setUploadFiles: setUploadFiles,
				uploadFiles: uploadFiles,
				model_in_use: modelInUse.current.value,
			})
		}
  }, [props.userData, sessionHash, uploadFiles]);

  const onMessageSend = (message : string, session_hash_id : string) => {
    console.log("Got session hash:", session_hash_id);
    if (displayChat === undefined || session_hash_id === undefined) { return; }
    // if 


    // setUploadFiles([]);
    const on_finish = () => {
      if (userQuestionEventEnabled) {
        // let empty : ChatEntry[] = [];
        setDisplayChat((prevChat) => ([...prevChat, {
          role: "user",
          content: message
        },{
          role: "assistant",
          content: "",
        }]));
        const collection_hash_ids : string[] = [];
        const col_keys = Object.keys(props.selectedCollections);
        for (let i = 0; i < col_keys.length; i++) {
          if (props.selectedCollections.get(col_keys[i]) === true) {
            collection_hash_ids.push(col_keys[i]);
          }
        }
        const event_args = {
          ...{
            "user_question": message,
            "model_choice": modelInUse.current.value
          },
          ...(collection_hash_ids.length > 0)?{
            "collection_hash_ids": collection_hash_ids
          }:{}
        }
        testEventCall("user_question_event", event_args, false);
      }
    };
    if (uploadFiles.length > 0) {
      upload_docs_to_session(session_hash_id, on_finish);
    } else {
      on_finish();
    }

    // setDisplayChat(prevChat => [...prevChat.slice(0, prevChat.length), {...prevChat[prevChat.length-1], state: 'writing'}]);
    // sse_fetch(message);
  };

  // const log_key_press = (e: {
  //   nativeEvent: { key: string; shiftKey: boolean };
  // }) => {
  //   if (e.nativeEvent.key === "Enter" && e.nativeEvent.shiftKey === false) {
  //     setSubmitInput(true);
  //   }
  // };
  
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

  // const translateSidebarButton = useRef(new Animated.Value(0)).current;
  // const opacitySidebarButton = useRef(new Animated.Value(0)).current;
  // const opacityChatWindow = useAnimation();
  // const opacitySuggestions = useRef(new Animated.Value(1)).current;

	const controlSidebarButtonOffset = useAnimation();
	// const controlSidebarButtonOpacity = useAnimation();

  useEffect(() => {
		controlSidebarButtonOffset.start({
			translateX: props.sidebarOpened?-320:0,
			transition: { duration: 0.4 }
		});
    setTimeout(() => {
			controlSidebarButtonOffset.start({
				opacity: props.sidebarOpened?0:1,
				transition: { duration: 0.4 }
			});
    }, props.sidebarOpened?0:300);
  }, [props.sidebarOpened, controlSidebarButtonOffset]);


  // const [toolchainSessionHashId, setToolchainSessionHashId] = useState<string | undefined>();

  useEffect(() => {
    console.log("Updated session state:", sessionState);
    const new_chat_display : ChatEntry[] = [];
    for (let i = 0; i < displayMappings.length; i++) {
      if (displayMappings[i].display_as === "chat" && displayMappings[i].type === "<<STATE>>") {
			
				console.log(sessionState);
				const sessionStateArray = sessionState.get(displayMappings[i].input_argument);
				if (sessionStateArray && Array.isArray(sessionStateArray)) {
					for (let j = 0; j < sessionStateArray.length; j++) {
						new_chat_display.push({
							...sessionStateArray[j],
							state: "finished"
						})
					}
				}
          
      } else if (displayMappings[i].display_as === "markdown" && displayMappings[i].type === "<<STATE>>") {
				const sessionStateValue = sessionState.get(displayMappings[i].input_argument) as string;
        // console.log("Pushing to display:", sessionState[displayMappings[i].input_argument]);
				if (sessionStateValue) {
					new_chat_display.push({
						content: sessionStateValue,
						state: "finished",
						role: "display"
					})
				}
      }
    }
    if (temporaryChat !== undefined) { new_chat_display.push( temporaryChat )}
    console.log("new display chat:", new_chat_display);
    setDisplayChat(new_chat_display);
  }, [sessionState, temporaryChat, displayMappings]);

	const get_stream_node_generator = useCallback(async (node_id : string, 
                                                    stream_argument_id : string, 
                                                    session_id : string) => {
    console.log("stream node prop call:", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": session_id,
      "event_node_id": node_id,
      "stream_variable_id": stream_argument_id
    });
    const url = craftUrl("http://localhost:5000/api/async/toolchain_stream_node_propagation_call", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": session_id,
      "event_node_id": node_id,
      "stream_variable_id": stream_argument_id
    });


    // setNodeStreamOutputQueue((prevQueue) => ([...prevQueue, node_id]));
    console.log("Created url:", url);
    // return;
    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", () => {
      console.log("Open stream node SSE connection.", node_id);
      
    });

    console.log("GLOBAL DISPLAY MAPPINGS:", displayMappings);

    const relevant_display_mappings : displayType[] = [];
    for (let i = 0; i < displayMappings.length; i++) {
      console.log("Parsing displayMap for relevance:", displayMappings[i]);
      if (displayMappings[i].input_argument === node_id && (displayMappings[i].type === "node_stream_temporary_output" || displayMappings[i].type === "node_stream_output")) {
        console.log("Pushing");
        relevant_display_mappings.push(displayMappings[i]);
      }
    }
    console.log("Using relevant mappings:", relevant_display_mappings);



    let recieved_string = "";

    es.addEventListener("message", (event : MessageEvent) => {
      let decoded = event.data.toString();
      decoded = hexToUtf8(decoded);
      // decoded = JSON.parse(decoded);
      if (decoded === "<<CLOSE>>") {
        es.close();
        return;
      }
      recieved_string += decoded;
      for (let i = 0; i < relevant_display_mappings.length; i++) {
        const mapping = relevant_display_mappings[i];
        if (mapping.display_as === "chat_entry") {
          setTemporaryChat({
            role: 'assistant',
            state: 'writing',
            content: recieved_string
          });
        }
      }
    });

    es.addEventListener("error", (event : ErrorEvent) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", () => {
      console.log("Close stream node SSE connection.");
      setTemporaryChat(undefined);
    });
  }, [props.userData.username, props.userData.password_pre_hash, displayMappings]);

  const get_session_global_generator = useCallback(async function (session_id : string, hooks_enabled : {file_event : boolean, question_event : boolean}) {
    const url = craftUrl("http://localhost:5000/api/async/get_session_global_generator", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": session_id
    });

    const es = new EventSource(url, {
      method: "GET",
    });

    if (globalGenerator !== undefined) { globalGenerator.close(); }
    setGlobalGenerator(es);

    es.addEventListener("open", () => {
      console.log("Open Global State SSE connection.");
    });

    es.addEventListener("message", (event : MessageEvent) => {
      let decoded = event.data.toString();
      decoded = hexToUtf8(decoded);
      if (decoded === "<<CLOSE>>") {
        es.close();
        return;
      }
      decoded = JSON.parse(decoded);
      console.log("Got Global State SSE message:", Date.now(), decoded);
      switch (decoded.type) {
        case "stream_output_pause":
          // let mapping_indices : number[] = [];
          console.log("STREAM MAPPING:", decoded.mapping);
          // for (let i = 0; i < decoded.mapping.length; i++) {
          //   if (decoded.mapping[i].action === "append_dict" || decoded.mapping[i].action === "append") {
          //     mapping_indices.push(sessionState[decoded.mapping[i].target_value].length);
          //   }
          // }

          get_stream_node_generator(decoded.node_id, decoded.stream_argument, session_id);
          break
        case "state_update":
          if (decoded.content_subset === "append") {
            // setSessionState((previousState) => (previousState.set(decoded.state_arg_id, [...(previousState.get(decoded.state_arg_id) as genericArrayType), decoded.content])));
						setSessionState((previousState) => {
							const newState = new Map(previousState);
							newState.set(decoded.state_arg_id, [...(newState.get(decoded.state_arg_id) as genericArrayType), decoded.content]);
							return newState;
						});
					} else if (decoded.content_subset === "full") {
            // setSessionState((previousState) => (previousState.set(decoded.state_arg_id, decoded.content)));
						setSessionState((previousState) => {
							const newState = new Map(previousState);
							newState.set(decoded.state_arg_id, decoded.content);
							return newState;
						});
          }
          break
        case "file_uploaded":
          if (eventActive === "file_upload") { setEventActive(undefined); }
          console.log("File upload notified, event enabled:", hooks_enabled.file_event);
          if (hooks_enabled.file_event) {
            console.log("Calling upload event");
            setUploadEventQueue((prevQueue) => ([...prevQueue, {fileName: decoded.file_name, hash_id: decoded.hash_id}]));
          }
          break
        case "finished_event_prop":
          setEventActive(undefined);
          if (decoded.node_id === "user_file_upload_event") {
            setUploadEventActive(false);
          }
          break
        case "node_execution_start":
          // console.log("NODE EXECUTION START:", Date.now(), decoded.node_id);
          setEventActive(decoded.node_id);
          break
      }
    });

    es.addEventListener("error", (event : ErrorEvent) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", () => {
      console.log("Close SSE connection.");
    });
  }, [props.userData.username, props.userData.password_pre_hash, eventActive, globalGenerator, get_stream_node_generator]);

  useEffect(() => {
    console.log("PageNavigateChanged");
    const navigate_args = props.pageNavigateArguments.split("-");
    if (props.pageNavigateArguments.length > 0 && navigate_args[0] === "chatSession") {
      setEntryFired(true);
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
        setDisplayChat([]);
        setSessionHash(navigate_args[1]);
        const url = craftUrl("http://localhost:5000/api/fetch_toolchain_session", {
          "username": props.userData.username,
          "password_prehash": props.userData.password_pre_hash,
          "session_id": navigate_args[1],
        });
        fetch(url, {method: "POST"}).then((response) => {
          console.log(response);
          response.json().then((data) => {
            if (!data["success"]) {
              console.error("Failed to retrieve session");
              return;
            }
            console.log("Retrieved session data:", data);
            // const session_data = data.result;
            // Add in code to reconfigure the window settings to the provided toolchain.

            // setSessionHash(data.result.session_hash_id);
						const newSessionState : sessionStateType = new Map([]);
						for (const [key, value] of Object.entries(data.result.state_arguments)) {
							const temp_value = value as genericMapValueType;
							newSessionState.set(key, temp_value)	;
						}

            setSessionState(newSessionState);
            get_session_global_generator(data.result.session_hash_id, {file_event: true, question_event: false});
						
            setTimeout(() => {
              // Animated.timing(opacityChatWindow, {
              //   toValue: 1,
              //   // toValue: opened?Math.min(300,(children.length*50+60)):50,
              //   duration: 150,
              //   easing: Easing.elastic(0),
              //   useNativeDriver: false,
              // }).start();
            }, 100);
          });
        });
      }, 150);
      // setTimeout(() => {
        
      // }, 250)
    } else if (sessionHash === undefined) {
      setEntryFired(false);
      const hooks_enabled = configureChatWindowAccordingToToolchain(selectedToolchain);
      setDisplaySuggestions(true);
      setDisplayChat([]);
      const url = craftUrl("http://localhost:5000/api/create_toolchain_session", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
        "toolchain_id": selectedToolchain.id
      });
      fetch(url, {method: "POST"}).then((response) => {
        console.log(response);
        response.json().then((data) => {
            if (data["success"]) {
              console.log("Successfully created toolchain session with hash:", data.result.session_hash);
              // console.log("Toolchain used:", props.userData.selected_toolchain);
							const newSessionState : sessionStateType = new Map([]);
							for (const [key, value] of Object.entries(data.result.state)) {
								const temp_value = value as genericMapValueType;
								newSessionState.set(key, temp_value)	;
							}

              setSessionState(newSessionState);
							console.log("Setting session hash created:", data.result.session_hash);
              setSessionHash(data.result.session_hash);
              get_session_global_generator(data.result.session_hash, hooks_enabled);
            } else {
              console.error("Failed to create toolchain session", data["note"]);
            }
        });
      });
    }
  }, [
		props.pageNavigateArguments, 
		selectedToolchain, 
		get_session_global_generator, 
		props.userData.username, 
		props.userData.password_pre_hash, 
		configureChatWindowAccordingToToolchain,
		sessionHash
	]);


  // const createToolchainSession = useCallback(() => {
  //   const url = craftUrl("http://localhost:5000/api/create_toolchain_session", {
  //     "username": props.userData.username,
  //     "password_prehash": props.userData.password_pre_hash,
  //     "toolchain_id": props.userData.selected_toolchain.id
  //   });

  //   fetch(url, {method: "POST"}).then((response) => {
  //     console.log(response);
  //     response.json().then((data) => {
  //       console.log(data);
  //       if (!data["success"]) {
  //         console.error("Failed to create toolchain:", data.note);
  //         // onFinish({});
  //         return;
  //       }
  //       // console.log("Available models:", data.result);
  //       // onFinish(data.result);
  //       console.log("Successfully created toolchain. Result:", data);
  //       setSessionHash(data.result.session_hash);
  //     });
  //   });
  // }, [props.userData.password_pre_hash, props.userData.selected_toolchain.id, props.userData.username]);

  // const testEntryCall = () => {
  //   console.log("Calling entry");
  //   const url = craftUrl("http://localhost:5000/api/async/toolchain_entry_call", {
  //     "username": props.userData.username,
  //     "password_prehash": props.userData.password_pre_hash,
  //     "session_id": sessionHash,
  //     "entry_parameters": {
  //       "user_provided_document": "hello"
  //     }
  //   });

  //   fetch(url, {method: "GET"}).then((response) => {
  //     console.log(response);
  //     response.json().then((data) => {
  //       console.log(data);
  //       if (!data["success"]) {
  //         console.error("Failed to call toolchain entry:", data.note);
  //         return;
  //       }
  //       console.log("Successfully called toolchain entry. Result:", data);
  //     });
  //   });
  // };

  const testEventCall = useCallback((event_node_id : string, event_parameters : object, file_response : boolean) => {
    if (sessionHash !== undefined) {
			setEntryFired(true);
			setEventActive(event_node_id);
			toolchainEventCall({
				session_hash: sessionHash,
				event_node_id: event_node_id,
				event_parameters: event_parameters,
				user_data: props.userData,
				file_response: file_response,
			});
		}
  }, [sessionHash, props.userData]);	


	useEffect(() => {
    if (uploadEventQueue.length > 0) { setEventActive("user_file_upload_event")}
    if (!uploadEventActive && uploadEventQueue.length > 0 && sessionHash !== undefined) {
      console.log("Activating upload event:", uploadEventQueue[0]);
      setUploadEventActive(true);
      testEventCall("user_file_upload_event", {
        "hash_id": uploadEventQueue[0].hash_id,
        "file_name": uploadEventQueue[0].fileName,
        "model_choice": modelInUse.current.value
      }, false);
      setUploadEventQueue((prevQueue) => (prevQueue.slice(1)));
    }
  }, [uploadEventActive, uploadEventQueue, sessionHash, testEventCall]);

	const [chatBarHeightString, setChatBarHeightString] = useState(40);

  return (
    <div style={{
      flex: 1,
			display: "flex",
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <div style={{display: "flex", flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <div id="ChatHeader" style={{
          width: "100%",
          height: 40,
          backgroundColor: "#23232D",
					display: "flex",
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <motion.div style={{
            paddingLeft: 10,
            width: 200,
            // transform: [{ translateX: translateSidebarButton,},],
            // elevation: -1,
            zIndex: 0,
            // opacity: opacitySidebarButton,
          }} animate={controlSidebarButtonOffset}>
            {props.sidebarOpened?(
              <Icon.Sidebar size={24} color="#E8E3E3" />
            ):(
              <AnimatedPressable style={{padding: 0, width: 30}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Icon.Sidebar size={24} color="#E8E3E3" />
              </AnimatedPressable> 
            )}
          </motion.div>
          <div style={{alignSelf: 'center'}}>
            {(availableModels !== undefined) && (
              <DropDownSelection
								selection={modelInUse.current}
                values={availableModels}
                defaultValue={modelInUse.current}
                setSelection={(value : formEntryType) => { modelInUse.current = value; }}
                // width={400}
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
          width: "60vw",
          paddingLeft: 0,
					paddingRight: 0,
          // paddingVertical: 24,
        }}>

          <div style={{
            flex: 5,
            opacity: 1
          }}>
            {(displayChat !== undefined) && (
              <ScrollViewBottomStick
								height_string=""
								animateScroll={false}
                // showsVerticalScrollIndicator={false}
                // animateScroll={animateScroll}
              >
                {displayChat.map((v_2 : ChatEntry, k_2 : number) => (
                  <div key={k_2}>
                    {(v_2 !== undefined) && (
                      <ChatBubble
                        displayCharacter={props.userData.username[0]}
                        state={(v_2.state)?v_2.state:"finished"}
                        key={k_2} 
                        role={v_2.role} 
                        input={v_2.content}
                        userData={props.userData}
                        sources={(v_2.sources)?v_2.sources.map((value : sourceMetadata) => ({document: value.metadata.document, metadata: value})):[]}
                      />
                    )}
                  </div>
                ))}
                {/* {temporaryBotEntry && (
                  <ChatBubble origin={temporaryBotEntry.origin} input={temporaryBotEntry.content_raw_string}/>
                )} */}
                {(eventActive !== undefined) && (
                  <div style={{width: "100%", flexDirection: "row", justifyContent: "center", paddingTop: 10, paddingBottom: 10}}>
                    <div style={{flexDirection: "row", justifyContent: "center"}}>
                      {/* <ActivityIndicator size={20} color="#E8E3E3"/> */}
											<Loader size={20} color="#E8E3E3"/>
                      <p style={{
                        fontFamily: 'Inter-Regular',
                        color: "#E8E3E3",
                        fontSize: 16,
                        paddingLeft: 10,
                        paddingRight: 10,
                      }}>
                        {"Running node: "+eventActive}
                      </p>
                    </div>
                  </div>
                )}
                {(buttonCallbacks.length > 0 && eventActive === undefined && entryFired) && (
                  <div style={{width: "100%", flexDirection: "row", justifyContent: "center"}}>
                    <div style={{maxWidth: "100%", flexDirection: "row", flexWrap: "wrap"}}>
                    {buttonCallbacks.map((v_2 : buttonCallback, k_2 : number) => (
                      <div style={{padding: 10}} key={k_2}>
                        <AnimatedPressable style={{
                          borderRadius: 10,
                          borderColor: "#E8E3E3",
                          borderWidth: 2,
                          flexDirection: "row" 
                        }} onPress={() => {
                          testEventCall(v_2.input_argument, {}, (v_2.return_file_response)?v_2.return_file_response:false)
                          // testEventCall()
                        }}>
                          <div style={{padding: 10, flexDirection: "row", justifyContent: "center"}}>
                            <Icon.Download size={16} color="#E8E3E3" />
                            <p style={{
                              fontFamily: 'Inter-Regular',
                              color: "#E8E3E3",
                              fontSize: 16,
                              paddingLeft: 10,
                              paddingRight: 10,
                            }}>
                              {v_2.button_text}
                            </p>
                          </div>
                        </AnimatedPressable>
                      </div>
                    ))}
                    </div>
                  </div>
                )}
								<div style={{height: chatBarHeightString + 77, width: 20}}/>
              </ScrollViewBottomStick>
            )}
          </div>

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
								onMessageSend={(msg : string) => {if (sessionHash !== undefined) { onMessageSend(msg, sessionHash); }}}
								onHeightChange={(height : number) => { 
									// setChatBarHeight(height); 
									setChatBarHeightString(height);
								}}
								// handleDrop={handleDrop}
							/>
						</div>
          </div> 
        </div>
      </div>
      {/* <StatusBar style="auto" /> */}
    </div>
  );
}
