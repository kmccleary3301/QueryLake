import { useState, useRef, useEffect, useCallback } from "react";
import EventSource from "@/lib/react-native-server-sent-events";
import toolchainEventCall from "@/hooks/chat-window-hooks.tsx/toolchain-event-call";
import * as Icon from 'react-feather';
import ChatBubble from "../manual_components/chat-bubble";
import AnimatedPressable from "../manual_components/animated-pressable";
import ScrollViewBottomStick from "../manual_components/scrollview-bottom-stick";
import craftUrl from "@/hooks/craftUrl";
import { DropDownSelection, formEntryType } from "../manual_components/dropdown-selection";
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
// import { Loader2 } from 'lucide-react';
import uploadDocsToSession from "@/hooks/chat-window-hooks.tsx/upload-docs-to-session";
import ChatBarInput from "../manual_components/chat-input-bar";
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { MessageEvent, ErrorEvent } from "@/lib/react-native-server-sent-events";
import getStreamNodeGenerator from "@/hooks/chat-window-hooks.tsx/get-stream-node-generator";
import ClipLoader from "react-spinners/ClipLoader";

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
  const [sessionState, setSessionState] = useState<sessionStateType>(new Map<string, genericMapValueType>([]));
  const [displayMappings, setDisplayMappings] = useState<displayType[]>([]);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [userQuestionEventEnabled, setUserQuestionEventEnabled] = useState(false);
  const [userFileEventEnabled, setUserFileEventEnabled] = useState(false);
  const [uploadEventQueue, setUploadEventQueue] = useState<uploadQueueEntry[]>([])
  const [uploadEventActive, setUploadEventActive] = useState(false);
  const [eventActive, setEventActive] = useState<string | undefined>();
  const [buttonCallbacks, setButtonCallbacks] = useState<buttonCallback[]>([]);
  const [entryFired, setEntryFired] = useState(false);
  const [globalGenerator, setGlobalGenerator] = useState<EventSource | undefined>();
  const [sessionHash, setSessionHash] = useState<string | undefined>();
  const [displaySuggestions, setDisplaySuggestions] = useState(true);
  const [displaySuggestionsDelayed, setDisplaySuggestionsDelayed] = useState(true);
  const [animateScroll, setAnimateScroll] = useState(false);
  const [modelInUseState, setModelInUse] = useState<formEntryType>({label: "Default", value: "Default"});
	const modelInUse = useRef<formEntryType>({label: "Default", value: "Default"});
  const [availableModels, setAvailableModels] = useState<{label : string, value : string | string[]}[]>([]);
	const [selectedToolchain, setSelectedToolchain] = useState<toolchainEntry>(props.userData.selected_toolchain);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [enableRAG, setEnableRag] = useState(false);
  const [maxFiles, setMaxFiles] = useState(0);
  // const [hooksEnabled, setHooksEnabled] = useState<{[key : string] : boolean}>({});
  
  // const [displayFiles, setDisplayFiles] = useState<any[] | undefined>();
  // const [nodeStreamOutputQueue, setNodeStreamOutputQueue] = useState<string[]>([]);
  // const [webSearchIsEnabled, setWebSearchIsEnabled] = useState(false);

  useEffect(() => {modelInUse.current = modelInUseState}, [modelInUseState]);
  useEffect(() => { if (modelInUse.current.label === "Default" && props.userData.available_models?.default_model !== undefined) setModelInUse({label: props.userData.available_models?.default_model, value: props.userData.available_models?.default_model})}, [props.userData]);
	useEffect(() => { console.log(displaySuggestions, displaySuggestionsDelayed, animateScroll, enableRAG, maxFiles, availableEvents)}, [enableRAG, maxFiles, availableEvents, displaySuggestions, displaySuggestionsDelayed, animateScroll]);

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
    setMaxFiles(chat_config.max_files);
    setEnableRag(chat_config.enable_rag);
    setAvailableEvents(chat_config.events_available);
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
    // setHooksEnabled(hooks_enabled);
    return hooks_enabled
  }, []);

  useEffect(() => {
    console.log("user_file:", userFileEventEnabled);
    console.log("user_chat:", userQuestionEventEnabled);
  }, [userFileEventEnabled, userQuestionEventEnabled]);

  useEffect(() => {
		if (props.userData.selected_toolchain !== selectedToolchain) {
			setSelectedToolchain(props.userData.selected_toolchain);
      setSessionHash(undefined);
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

	const get_stream_node_generator = useCallback(async ( node_id : string, 
                                                        stream_argument_id : string, 
                                                        session_id : string) => {
    getStreamNodeGenerator({
      node_id : node_id, 
      stream_argument_id : stream_argument_id, 
      session_id : session_id,
      user_data : props.userData,
      display_mappings : displayMappings,
      set_chat : setTemporaryChat,
    })
  }, [props.userData, displayMappings]);

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

          get_stream_node_generator(decoded.node_id, decoded.stream_argument, session_id);
          break
        case "state_update":
          if (decoded.content_subset === "append") {
            setSessionState((previousState) => {
							const newState = new Map(previousState);
							newState.set(decoded.state_arg_id, [...(newState.get(decoded.state_arg_id) as genericArrayType), decoded.content]);
							return newState;
						});
					} else if (decoded.content_subset === "full") {
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
      console.log("Hooks enabled:", hooks_enabled);

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

  useEffect(() => {
    console.log("uploadFiles Main:", uploadFiles)
  }, [uploadFiles]);

  const onMessageSend = useCallback((message : string) => {
    console.log("Got session hash:", sessionHash);
    if (displayChat === undefined || sessionHash === undefined) { return; }
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
      console.log("Running uploadDocsToSession");
      uploadDocsToSession({
        userData: props.userData,
				session_hash: sessionHash,
				collection_hash_id: sessionHash,
				on_finish: on_finish,
				setUploadFiles: setUploadFiles,
				uploadFiles: uploadFiles,
				model_in_use: modelInUse.current.value,
      })
    } else {
      console.log("Running onFinish");
      on_finish();
    }

  }, [
    sessionHash, 
    displayChat, 
    props.selectedCollections, 
    uploadFiles, 
    props.userData,
    userQuestionEventEnabled,
    testEventCall,
    // hooksEnabled
  ]);

  return (
    
      <div style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
      }}>
        <div id="ChatHeader" style={{
          width: "100%",
          height: 40,
          // backgroundColor: "#23232D",
					display: "flex",
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{
            paddingLeft: 10,
            width: 200,
            // transform: [{ translateX: translateSidebarButton,},],
            // elevation: -1,
            // zIndex: 0,
            // opacity: opacitySidebarButton,
          }}>
            {/* Decide what to put here */}
          </div>
          <div style={{alignSelf: 'center'}}>
            {(availableModels !== undefined) && (
              <DropDownSelection
								selection={modelInUseState}
                values={availableModels}
                defaultValue={modelInUseState}
                setSelection={(value : formEntryType) => { setModelInUse(value); }}
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
        {/* <div id="Chat Window Scrollable" className="scrollbar-custom mr-1 h-full overflow-y-auto" style={{
          // margin: 1,
          width: "100%",
          height: "full",
          overflowY: "auto",
        }}>
          <div className="mx-auto flex h-full max-w-3xl flex-col gap-6 px-5 pt-6 sm:gap-8 xl:max-w-4xl" style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            flex: 1,
          }}>
            <div className="group relative flex items-start justify-start gap-4 max-sm:text-sm" style={{
              display: "flex",
              flexDirection: "column",
              justifyContent: "flex-start"
            }}> */}
        <div className="scrollbar-custom mr-1 h-full overflow-y-auto" style={{
          // margin: 1,
          width: "100%",
          // height: "full",
          overflowY: "auto",
        }}>
          <ScrollViewBottomStick bottomMargin={chatBarHeightString+70}>
            <div style={{
              width: "60vw",
              flexDirection: "column",
              justifyContent: "center"
            }}>
              {(displayChat !== undefined) && (
                // <ScrollViewBottomStick
                // 	height_string=""
                // 	animateScroll={false}
                //   // showsVerticalScrollIndicator={false}
                //   // animateScroll={animateScroll}
                // >
                <>
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
                  {(eventActive !== undefined) && (
                    <div style={{width: "100%", flexDirection: "row", justifyContent: "center", paddingTop: 10, paddingBottom: 10}}>
                      <div style={{display: "flex", flexDirection: "row", justifyContent: "center"}}>
                        {/* <ActivityIndicator size={20} color="#E8E3E3"/> */}
                        <ClipLoader size={20} color="#E8E3E3"/>
                        <p style={{
                          // fontFamily: 'Inter-Regular',
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
                    <div style={{width: "100%", display: "flex", flexDirection: "row", justifyContent: "center"}}>
                      <div style={{maxWidth: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap"}}>
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
                            <div style={{padding: 10, display: "flex", flexDirection: "row", justifyContent: "center"}}>
                              <Icon.Download size={16} color="#E8E3E3" />
                              <p style={{
                                // fontFamily: 'Inter-Regular',
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
                
                </>
              )}
            </div>
          </ScrollViewBottomStick>
          <div id="InputBox" style={{
            // position: "absolute",
            // height: 0,
						display: "flex",
            flexDirection: 'row',
            justifyContent: 'center',
            // flex: 1,
            // height: 200,
            width: '100%',
            height: 0,
						paddingBottom: 0,
            // zIndex: 3,
          }}>
            <div style={{
              position: "absolute",
              height: 0,
              display: "flex",
              flexDirection: 'column',
              justifyContent: "flex-end",
              width: "60vw"
            }}>
              <div className="bg-background" style={{
                display: "flex",
                flexDirection: 'column',
                justifyContent: 'space-around',
                // flex: 1,
                // height: 200,
                paddingTop: 10,
                paddingBottom: 0,
                // zIndex: 2,
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
                  handleDrop={(files: File[]) => {
                    setUploadFiles(files);
                  }}
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
      </div>
  );
}
