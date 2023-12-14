import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  StatusBar,
  Linking,
  Platform,
  Animated,
  Easing,
  ActivityIndicator
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
import searchGoogle from "../hooks/searchGoogle";
import DropDownSelection from "../components/DropDownSelection";
import HoverDocumentEntry from "../components/HoverDocumentEntry";

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
  role: ("user" | "assistant" | "display"),
  // content_392098: ChatContent,
  content: string,
  // status?: ("generating_query" | "searching_google" | "typing"),
  sources?: sourceMetadata[],
  state?: "finished" | "searching_web" | "searching_vector_database" | "crafting_query" | "writing" | undefined
};

type buttonCallback = {
  input_argument : string,
  type: "event_button",
  display_as: "button",
  feather_icon: string,
  button_text: string,
  return_file_response?: boolean
};

type displayType = {
  input_argument : string,
  type: "<<STATE>>" | "event_offer",
  display_as: "chat" | "chat_window_files" | "center_table" | "chat_window_progress_bar" | "markdown"
} | buttonCallback | {
  input_argument : string, // In this case, it is a node id.
  type: "node_stream_temporary_output" | "node_stream_output",
  display_as: "chat_entry" | "markdown"
};

type toolchainEntry = {
  name: string,
  id: string,
  category: string
  chat_window_settings: {
    display: displayType[],
    max_files: number,
    enable_rag: boolean,
    events_available: string[]
  },
};

type userDataType = {
  username: string,
  password_pre_hash: string,
  serp_key?: string,
  available_models?: {
    default_model: string,
    local_models: string[],
    external_models: object
  },
  selected_toolchain: toolchainEntry,
};

type ChatWindowToolchainProps = {
  navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  userData: userDataType,
  pageNavigateArguments: any,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  selectedCollections: object
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
  const [displayChat, setDisplayChat] = useState<ChatEntry[]>();
  const [temporaryChat, setTemporaryChat] = useState<ChatEntry | undefined>();
  const [displayFiles, setDisplayFiles] = useState<any[] | undefined>();
  const [sessionState, setSessionState] = useState<Object>({});
  const [displayMappings, setDisplayMappings] = useState<displayType[]>(props.userData.selected_toolchain.chat_window_settings.display);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [userQuestionEventEnabled, setUserQuestionEventEnabled] = useState(false);
  const [userFileEventEnabled, setUserFileEventEnabled] = useState(false);

  const [uploadEventQueue, setUploadEventQueue] = useState<uploadQueueEntry[]>([])
  const [uploadEventActive, setUploadEventActive] = useState(false);
  const [eventActive, setEventActive] = useState<string | undefined>();
  const [buttonCallbacks, setButtonCallbacks] = useState<buttonCallback[]>([]);
  const [entryFired, setEntryFired] = useState(false);
  const [nodeStreamOutputQueue, setNodeStreamOutputQueue] = useState<string[]>([]);


  const [enableRAG, setEnableRag] = useState(false);
  const [maxFiles, setMaxFiles] = useState(0);

  const [webSearchIsEnabled, setWebSearchIsEnabled] = useState(false);
  const [globalGenerator, setGlobalGenerator] = useState<EventSource | undefined>();
  
  const [inputText, setInputText] = useState("");
  const [sseOpened, setSseOpened] = useState(false);
  const [submitInput, setSubmitInput] = useState(false);
  const [inputLineCount, setInputLineCount] = useState(1);
  const [sessionHash, setSessionHash] = useState();
  const [displaySuggestions, setDisplaySuggestions] = useState(true);
  const [displaySuggestionsDelayed, setDisplaySuggestionsDelayed] = useState(true);
  const [animateScroll, setAnimateScroll] = useState(false);
  const [modelInUse, setModelInUse] = useState({label: "Default", value: "Default"});
  const [availableModels, setAvailableModels] = useState(undefined);
  
  useEffect(() => {
    if (uploadEventQueue.length > 0) { setEventActive("user_file_upload_event")}
    if (!uploadEventActive && uploadEventQueue.length > 0) {
      console.log("Activating upload event:", uploadEventQueue[0]);
      setUploadEventActive(true);
      testEventCall("user_file_upload_event", {
        "hash_id": uploadEventQueue[0].hash_id,
        "file_name": uploadEventQueue[0].fileName,
        "model_choice": modelInUse.value
      }, sessionHash, false);
      setUploadEventQueue((prevQueue) => (prevQueue.slice(1)));
    }
  }, [uploadEventActive, uploadEventQueue]);

  const configureChatWindowAccordingToToolchain = (toolchain : toolchainEntry) => {
    const chat_config = toolchain.chat_window_settings;
    console.log("Configuring chat window with config:", chat_config);
    setDisplayMappings(chat_config.display);
    let button_callbacks : buttonCallback[] = [];
    for (let i = 0; i < chat_config.display.length; i++) {
      const display_entry = chat_config.display[i];
      if (display_entry.display_as === "chat") {
        setDisplayChat([]);
      } else if (display_entry.display_as === "button") {
        button_callbacks.push(display_entry)
      }
    }
    setButtonCallbacks(button_callbacks);
    setMaxFiles(chat_config.max_files);
    setEnableRag(chat_config.enable_rag);
    setAvailableEvents(chat_config.events_available);
    let hooks_enabled = {
      "file_event": false,
      "question_event": false
    }

    for (let i = 0; i < chat_config.events_available.length; i++) {
      let event_id = chat_config.events_available[i];
      if (event_id === "user_file_upload_event") { hooks_enabled["file_event"] = true; }
      else if (event_id === "user_question_event") { hooks_enabled["question_event"] = true; }
    }
    setUserFileEventEnabled(hooks_enabled["file_event"]);
    setUserQuestionEventEnabled(hooks_enabled["question_event"])
    return hooks_enabled
  }

  useEffect(() => {
    console.log("user_file:", userFileEventEnabled);
    console.log("user_chat:", userQuestionEventEnabled);
  }, [userFileEventEnabled, userQuestionEventEnabled]);

  useEffect(() => {
    if (props.userData.available_models && props.userData.available_models !== undefined) {
      let modelSelections = [];
      for (let i = 0; i < props.userData.available_models.local_models.length; i++) {
        modelSelections.push({
          label: props.userData.available_models.local_models[i],
          value: props.userData.available_models.local_models[i]
        });
      }
      for (const [key, value] of Object.entries(props.userData.available_models.external_models)) {

        // console.log(`${key}: ${value}`);
        for (let i = 0; i < props.userData.available_models.external_models[key].length; i++) {
          modelSelections.push({
            label: key+"/"+props.userData.available_models.external_models[key][i],
            value: [key, props.userData.available_models.external_models[key][i]]
          });
        }
      }
      setAvailableModels(modelSelections);
      setModelInUse({
        label: props.userData.available_models.default_model, 
        value: props.userData.available_models.default_model
      });
    }
  }, [props.userData]);


  useEffect(() => {
    console.log("PageNavigateChanged");
    const navigate_args = props.pageNavigateArguments.split("-");
    if (props.pageNavigateArguments.length > 0 && navigate_args[0] === "chatSession") {
      setEntryFired(true);
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
            const session_data = data.result;
            // Add in code to reconfigure the window settings to the provided toolchain.

            setSessionHash(data.result.session_hash_id);
            setSessionState(data.result.state_arguments);
            get_session_global_generator(data.result.session_hash_id, {file_event: true, question_event: false});

            // let new_entries : ChatEntry[] = [];
            // for (let i = 0; i < data.result.length; i++) {
            //   console.log("Pushing response", data.result[i]);
            //   if (data.result[i].sources) {
            //     // let sources_tmp = data.result[i].sources.map((value) => { metadata: value});
            //     console.log("Got sources:", data.result[i].sources);
            //     new_entries.push({
            //       content: hexToUtf8(data.result[i].content),
            //       role: (data.result[i].type === "user")?"user":"server",
            //       sources: data.result[i].sources
            //     }); //Add sources if they were provided
            //   } else {
            //     new_entries.push({
            //       content: hexToUtf8(data.result[i].content),
            //       role: (data.result[i].type === "user")?"user":"server"
            //     }); //Add sources if they were provided
            //   }
            // }
            // setDisplayChat(new_entries);
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
      setEntryFired(false);
      let hooks_enabled = configureChatWindowAccordingToToolchain(props.userData.selected_toolchain);
      setDisplaySuggestions(true);
      setDisplayChat([]);
      const url = craftUrl("http://localhost:5000/api/create_toolchain_session", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
        "toolchain_id": props.userData.selected_toolchain.id
      });
      fetch(url, {method: "POST"}).then((response) => {
        console.log(response);
        response.json().then((data) => {
            if (data["success"]) {
              console.log("Successfully created toolchain session with hash:", data.result.session_hash);
              console.log("Toolchain used:", props.userData.selected_toolchain);
              setSessionState(data.result.state);
              setSessionHash(data.result.session_hash);
              get_session_global_generator(data.result.session_hash, hooks_enabled);
            } else {
              console.error("Failed to create toolchain session", data["note"]);
            }
        });
      });
    }
  }, [props.pageNavigateArguments, props.userData.selected_toolchain]);

  
  useEffect(() => {
    console.log("Modified session hash:", sessionHash);
  }, [sessionHash]);
  // const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  const PlatformIsWeb = Platform.select({web: true, default: false});


  let genString = "";
  // let termLet: string[] = [];

  const sse_fetch = async function(message : string) {
    let user_entry : ChatEntry = {
      role: "user",
      content_raw_string: message,
    };
    
    let bot_entry : ChatEntry = {
      role: "server",
      // content_392098: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
      content_raw_string: "",
      sources: []
    }
    let new_chat = [...displayChat, user_entry];
    setDisplayChat(newChat => [...newChat, user_entry, bot_entry]);
    
    let collection_hash_ids : string[] = [];
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

    let refresh_chat_history = (displayChat.length === 0);
    
    // let chat_history_all = newChat.map((x) => {
    //   role: (x.origin === "user")?"user":"assistant", 
    //   content: x.content_raw_string
    // });

    let chat_history_all = [...displayChat].map((value) => ({ 
      role: (value.origin === "user")?"user":"assistant", 
      content: value.content_raw_string
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
    setDisplayChat(prevChat => [...prevChat.slice(0, prevChat.length-1), {...prevChat[prevChat.length-1], "sources": bot_response_sources, state: 'writing'}]);

    console.log("New sources:", bot_response_sources);
    

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
        setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
          ...newChat[newChat.length-1],
          state: 'finished'
        }])
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
        setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
          ...newChat[newChat.length-1],
          "content_raw_string": genString,
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
      setDisplayChat(newChat => [...newChat.slice(0, newChat.length-1), {
        ...newChat[newChat.length-1],
        state: 'finished'
      }])
    });
  };

  const toggleSwitch = () => {console.log("toggled switch to:", !webSearchIsEnabled); setWebSearchIsEnabled((previousState) => !previousState); };

  const handleDrop = (event: any) => {
    event.preventDefault();
    let new_files = [...uploadFiles, ...event.dataTransfer.files];
    setUploadFiles(new_files);
  };

  const upload_docs_to_session = (session_hash_id : string, on_finish : () => void) => {
    console.log("Got session hash:", session_hash_id);
    let url_2 = craftUrl("http://localhost:5000/api/async/upload_document_to_session", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "collection_hash_id": session_hash_id,
      "session_id": sessionHash,
      "collection_type": "toolchain_session",
      "event_parameters": {
        "model_choice": modelInUse.value
      }
    });
    
    const uploader = createUploader({
      destination: {
        method: "POST",
        url: url_2.toString(),
        filesParamName: "file",
      },
      autoUpload: true,
    });
    setUploadFiles([]);
    let finished_uploads = 0;

    uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
      console.log(`item ${item.id} started uploading`);
      // setFinishedUploads(finishedUploads => finishedUploads+1);
      // setCurrentUploadProgress(0);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
      console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
      // setCurrentUploadProgress(item.completed);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
      console.log(`item ${item.id} response:`, item.uploadResponse);

      finished_uploads += 1;

      // if (uploadFiles.length === 1) {
      //   on_finish();
      //   setUploadFiles([]);
      // } else {
      //   setUploadFiles(uploadFiles.slice(1, uploadFiles.length));
      // }
      
      // if (uploadFiles.length) {
        // setUploadFiles([]);
      //   props.setRefreshSidePanel(["collections"]);
      //   if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
      //   if (props.navigation) { props.navigation.navigate("ChatWindow"); }
      // }
    });
    // let formData = new FormData();
    for (let i = 0; i < uploadFiles.length; i++) {
      // formData.append("file", event.dataTransfer.files[i]);
      uploader.add(uploadFiles[i]);
      console.log(uploadFiles[i]);
    }
    // setPublishStarted(true);

    if (uploadFiles.length === 0) {
      // props.setRefreshSidePanel(["collections"]);
      // if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
      // if (props.navigation) { props.navigation.navigate("ChatWindow"); }
    }
    setEventActive("file_upload");
  };

  const onMessageSend = (message : string, session_hash_id : string) => {
    console.log("Got session hash:", session_hash_id);
    if (displayChat === undefined || session_hash_id === undefined) { return; }
    // if 


    // setUploadFiles([]);
    const on_finish = () => {
      if (userQuestionEventEnabled) {
        let empty : ChatEntry[] = []
        setDisplayChat((prevChat) => ([...prevChat, {
          role: "user",
          content: message
        },{
          role: "server",
          content: "",
        }]));
        let collection_hash_ids : string[] = [];
        let col_keys = Object.keys(props.selectedCollections);
        for (let i = 0; i < col_keys.length; i++) {
          if (props.selectedCollections[col_keys[i]] === true) {
            collection_hash_ids.push(col_keys[i]);
          }
        }
        const event_args = {
          ...{
            "user_question": message,
            "model_choice": modelInUse.value
          },
          ...(collection_hash_ids.length > 0)?{
            "collection_hash_ids": collection_hash_ids
          }:{}
        }
        testEventCall("user_question_event", event_args, sessionHash, false);
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
  // const opacitySuggestions = useRef(new Animated.Value(1)).current;

  useEffect(() => {
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


  // const [toolchainSessionHashId, setToolchainSessionHashId] = useState<string | undefined>();

  useEffect(() => {
    console.log("Updated session state:", sessionState);
    let new_chat_display : ChatEntry[] = [];
    for (let i = 0; i < displayMappings.length; i++) {
      if (displayMappings[i].display_as === "chat" && displayMappings[i].type === "<<STATE>>" && sessionState.hasOwnProperty(displayMappings[i].input_argument)) {
        for (let j = 0; j < sessionState[displayMappings[i].input_argument].length; j++) {
          new_chat_display.push({
            ...sessionState[displayMappings[i].input_argument][j],
            state: "finished"
          })
        }
      } else if (displayMappings[i].display_as === "markdown" && displayMappings[i].type === "<<STATE>>" && sessionState.hasOwnProperty(displayMappings[i].input_argument)) {
        console.log("Pushing to display:", sessionState[displayMappings[i].input_argument]);
        new_chat_display.push({
          content: sessionState[displayMappings[i].input_argument],
          state: "finished",
          role: "display"
        })
      }
    }
    if (temporaryChat !== undefined) { new_chat_display.push( temporaryChat )}
    console.log("new display chat:", new_chat_display);
    setDisplayChat(new_chat_display);
  }, [sessionState, temporaryChat]);

  const get_session_global_generator = async function (session_id : string, hooks_enabled : {file_event : boolean, question_event : boolean}) {
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

    es.addEventListener("open", (event) => {
      console.log("Open Global State SSE connection.");
    });

    es.addEventListener("message", (event) => {
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
          console.log("STREAM MAPPING:", decoded.mapping);
          let mapping_indices : number[] = [];
          // for (let i = 0; i < decoded.mapping.length; i++) {
          //   if (decoded.mapping[i].action === "append_dict" || decoded.mapping[i].action === "append") {
          //     mapping_indices.push(sessionState[decoded.mapping[i].target_value].length);
          //   }
          // }

          get_stream_node_generator(decoded.node_id, decoded.stream_argument, session_id, decoded.mapping, mapping_indices);
          break
        case "state_update":
          if (decoded.content_subset === "append") {
            setSessionState((previousState) => ({...previousState, [decoded.state_arg_id] : [...previousState[decoded.state_arg_id], decoded.content]}));
          } else if (decoded.content_subset === "full") {
            setSessionState((previousState) => ({...previousState, [decoded.state_arg_id] : decoded.content}));
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

    es.addEventListener("error", (event) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", (event) => {
      console.log("Close SSE connection.");
    });
  };

  const get_stream_node_generator = async function (node_id : string, 
                                                    stream_argument_id : string, 
                                                    session_id : string,
                                                    mappings: object[],
                                                    state_index: number[] | undefined) {
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


    setNodeStreamOutputQueue((prevQueue) => ([...prevQueue, node_id]));
    console.log("Created url:", url);
    // return;
    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", (event) => {
      console.log("Open stream node SSE connection.", node_id);
      
    });
    console.log("GLOBAL DISPLAY MAPPINGS:", displayMappings);

    let relevant_display_mappings : displayType[] = [];
    for (let i = 0; i < displayMappings.length; i++) {
      console.log("Parsing displayMap for relevance:", displayMappings[i]);
      if (displayMappings[i].input_argument === node_id && (displayMappings[i].type === "node_stream_temporary_output" || displayMappings[i].type === "node_stream_output")) {
        console.log("Pushing");
        relevant_display_mappings.push(displayMappings[i]);
      }
    }
    console.log("Using relevant mappings:", relevant_display_mappings);



    let recieved_string = "";

    es.addEventListener("message", (event) => {
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
          // console.log("Setting temporary chat");
          setTemporaryChat({
            role: 'server',
            state: 'writing',
            content: recieved_string
          });
          // if (displayChat !== undefined) {
          //   console.log("")
          //   setDisplayChat(displayChat => [...displayChat.slice(0, displayChat.length-1), {
          //     ...displayChat[displayChat.length-1],
          //     "content_raw_string": recieved_string,
          //   }])
          // }
        }
      }
      // console.log("Got stream node SSE message:", [node_id, decoded])
    });

    es.addEventListener("error", (event) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", (event) => {
      console.log("Close stream node SSE connection.");
      setTemporaryChat(undefined);
    });
  };

  const createToolchainSession = () => {
    const url = craftUrl("http://localhost:5000/api/create_toolchain_session", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "toolchain_id": props.userData.selected_toolchain.id
    });

    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to create toolchain:", data.note);
          // onFinish({});
          return;
        }
        // console.log("Available models:", data.result);
        // onFinish(data.result);
        console.log("Successfully created toolchain. Result:", data);
        setSessionHash(data.result.session_hash);
      });
    });
  };

  const testEntryCall = () => {
    console.log("Calling entry");
    const url = craftUrl("http://localhost:5000/api/async/toolchain_entry_call", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": sessionHash,
      "entry_parameters": {
        "user_provided_document": "hello"
      }
    });

    fetch(url, {method: "GET"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to call toolchain entry:", data.note);
          // onFinish({});
          return;
        }
        // console.log("Available models:", data.result);
        // onFinish(data.result);
        console.log("Successfully called toolchain entry. Result:", data);
        // setToolchainSessionHashId(data.session_id);
      });
    });
  };

  const testEventCall = (event_node_id : string, event_parameters : object, session_hash : string, file_response : boolean) => {
    setEntryFired(true);
    setEventActive(event_node_id);
    console.log("Calling event", event_node_id);
    if (session_hash === undefined) {
      console.log("Toolchain Id is undefined!");
      return;
    }

    console.log("urls used:", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": session_hash,
      "event_node_id": event_node_id,
      "event_parameters": event_parameters
    });

    const url = craftUrl("http://localhost:5000/api/async/toolchain_event_call", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "session_id": session_hash,
      "event_node_id": event_node_id,
      "event_parameters": event_parameters,
      "return_file_response": file_response
    });

    fetch(url, {method: "GET"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to call toolchain event:", data.note);
          // onFinish({});
          return;
        }
        // console.log("Available models:", data.result);
        // onFinish(data.result);
        console.log("Successfully called toolchain event. Result:", data);
        const response = data.result;
        if (data.result.flag && data.result.flag === "file_response") {
          const url_doc_access = craftUrl("http://localhost:5000/api/async/get_toolchain_output_file_response/"+data.result.file_name, {
            "server_zip_hash": data.result.server_zip_hash,
            "document_password": data.result.password
          });
          Linking.openURL(url_doc_access.toString());
        }
        // setToolchainSessionHashId(data.session_id);
      });
    });
  };


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
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Animated.View style={{
            paddingLeft: 10,
            width: 200,
            transform: [{ translateX: translateSidebarButton,},],
            elevation: -1,
            zIndex: -1,
            opacity: opacitySidebarButton,
          }}>
            {props.sidebarOpened?(
              <Feather name="sidebar" size={24} color="#E8E3E3" />
            ):(
              <AnimatedPressable style={{padding: 0, width: 30}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </AnimatedPressable> 
            )}
          </Animated.View>
          <View style={{alignSelf: 'center'}}>
            {(availableModels !== undefined) && (
              <DropDownSelection
                values={availableModels}
                defaultValue={modelInUse}
                setSelection={setModelInUse}
                width={400}
              />
            )}
          </View>
          <View
            style={{
              width: 200
            }}
          />
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

          <Animated.View style={{
            flex: 5,
            opacity: 1
          }}>
            {(displayChat !== undefined) && (
              <ScrollViewBottomStick
                showsVerticalScrollIndicator={false}
                animateScroll={animateScroll}
              >
                {displayChat.map((v_2 : ChatEntry, k_2 : number) => (
                  <View key={k_2}>
                    {(v_2 !== undefined) && (
                      <ChatBubble
                        displayCharacter={props.userData.username[0]}
                        state={(v_2.hasOwnProperty('state'))?v_2.state:"finished"}
                        key={k_2} 
                        role={v_2.role} 
                        input={v_2.content}
                        userData={props.userData}
                        sources={(v_2["sources"])?v_2["sources"]:[]}
                      />
                    )}
                  </View>
                ))}
                {/* {temporaryBotEntry && (
                  <ChatBubble origin={temporaryBotEntry.origin} input={temporaryBotEntry.content_raw_string}/>
                )} */}
                {(eventActive !== undefined) && (
                  <View style={{width: "100%", flexDirection: "row", justifyContent: "center", paddingVertical: 10}}>
                    <View style={{flexDirection: "row", justifyContent: "center"}}>
                      <ActivityIndicator size={20} color="#E8E3E3"/>
                      <Text style={{
                        fontFamily: 'Inter-Regular',
                        color: "#E8E3E3",
                        fontSize: 16,
                        paddingLeft: 10,
                        paddingRight: 10,
                      }}>
                        {"Running node: "+eventActive}
                      </Text>
                    </View>
                  </View>
                )}
                {(buttonCallbacks.length > 0 && eventActive === undefined && entryFired) && (
                  <View style={{width: "100%", flexDirection: "row", justifyContent: "center"}}>
                    <View style={{maxWidth: "100%", flexDirection: "row", flexWrap: "wrap"}}>
                    {buttonCallbacks.map((v_2 : buttonCallback, k_2 : number) => (
                      <View style={{padding: 10}}>
                        <AnimatedPressable style={{
                          borderRadius: 10,
                          borderColor: "#E8E3E3",
                          borderWidth: 2,
                          flexDirection: "row" 
                        }} onPress={() => {
                          testEventCall(v_2.input_argument, {}, sessionHash, (v_2.return_file_response)?v_2.return_file_response:false)
                          // testEventCall()
                        }}>
                          <View style={{padding: 10, flexDirection: "row", justifyContent: "center"}}>
                            <Feather name={v_2.feather_icon} size={16} color="#E8E3E3" />
                            <Text style={{
                              fontFamily: 'Inter-Regular',
                              color: "#E8E3E3",
                              fontSize: 16,
                              paddingLeft: 10,
                              paddingRight: 10,
                            }}>
                              {v_2.button_text}
                            </Text>
                          </View>
                        </AnimatedPressable>
                      </View>
                    ))}
                    </View>
                  </View>
                )}
              </ScrollViewBottomStick>
            )}
          </Animated.View>

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
                paddingRight: 10,
              }}>
                <View style={{paddingLeft: 10}}>
                  <Switch
                    trackColor={{ false: "#4D4D56", true: "#7968D9" }}
                    // thumbColor={isEnabled ? "#D9D9D9" : "#D9D9D9"}
                    thumbColor={"#D9D9D9"}
                    
                    
                    onValueChange={toggleSwitch}
                    value={webSearchIsEnabled}
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
              <View style={{paddingLeft: 10, flex: 1, flexDirection: "row", justifyContent: 'flex-start'}}>
                <ScrollView style={{
                  maxWidth: '100%',
                  height: 30,
                  // transform: [{ scaleX: -1 }],
                  // paddingLeft: 10,
                  flexShrink: 1,
                  borderRadius: 15, 
                  // borderWidth: 2, 
                  // borderColor: '#FF0000'
                }} showsHorizontalScrollIndicator={false} horizontal={true}>
                  <View style={{
                    flexDirection: 'row-reverse',
                    // flexDirection: 'row',
                    // justifyContent: 'flex-end'
                    // transform: [{ scaleX: -1 }]
                  }}>
                    {uploadFiles.map((value : {name : string}, index : number) => (
                      <View key={index} style={{
                        maxWidth: 200,
                        // paddingLeft: (index > 0)?10:0,
                        paddingLeft: (index < uploadFiles.length - 1)?10:0,
                      }}>
                        <HoverDocumentEntry title={value.name} deleteIndex={() => {
                            setUploadFiles([...uploadFiles.slice(0, index), ...uploadFiles.slice(index+1, uploadFiles.length)]);
                          }}
                          disableOpacity={true}
                          style={{
                            backgroundColor: "#7968D9",
                            borderRadius: 20,
                            height: 28,
                            paddingLeft: 10,
                            paddingRight: 10,
                          }}
                          iconColor={"#000000"}
                          textStyle={{
                            color: "#000000",
                            fontSize: 14,
                            fontFamily: "Inter-Regular",
                            // height: 28,
                            // textAlignVertical: 'center',
                            // paddingLeft: 10,
                            // paddingRight: 10,
                          }}
                        />
                      </View>
                    ))}
                  </View>
                </ScrollView>
              </View>
            </View>
            {Platform.select({
              web: (
                <ChatBarInputWeb
                  onMessageSend={(message : string) => {
                    onMessageSend(message, sessionHash);
                  }}
                  handleDrop={handleDrop}
                  chatEnabled={userQuestionEventEnabled}
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
