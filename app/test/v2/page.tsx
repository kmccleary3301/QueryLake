"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@/registry/default/ui/button";
import ToolchainSession, { CallbackOrValue, ToolchainSessionMessage, toolchainStateType } from "@/hooks/toolchain-session";
import { useContextAction } from "@/app/context-provider";
import ChatBarInput from "@/components/manual_components/chat-input-bar";
import FileDropzone from "@/registry/default/ui/file-dropzone";
import { ScrollArea } from "@radix-ui/react-scroll-area";
import { Textarea } from "@/registry/default/ui/textarea";
// import { produce } from 'immer';

export default function TestPage() {
  const {
    userData,
  } = useContextAction();

  // const [toolchainWebsocket, setToolchainWebsocket] = useState<ToolchainSession | undefined>();
  const toolchainWebsocket = useRef<ToolchainSession | undefined>();
  const sessionId = useRef<string>();
  const toolchainStateRef = useRef<toolchainStateType>({});
  const [toolchainState, setToolchainState] = useState<toolchainStateType>({});
  const [toolchainStateCounter, setToolchainStateCounter] = useState<number>(0);
  const toolchainStreamMappings = useRef<Map<string, (string | number)[][]>>(new Map());
  

  const updateState = useCallback((state: CallbackOrValue<toolchainStateType>) => {
    // console.log("update state called with", toolchainStateCounter);
    setToolchainStateCounter(toolchainStateCounter + 1);

    const value = (typeof state === "function") ? state(toolchainStateRef.current) : state;
    toolchainStateRef.current = value;
    const value_copied = JSON.parse(JSON.stringify(value));
    setToolchainState(value_copied);
    console.log(value);
  }, [toolchainState, setToolchainStateCounter, toolchainStateCounter, setToolchainState]);

  // const updateState = useCallback((state: CallbackOrValue<toolchainStateType>) => {
  //   console.log("update state called with", toolchainStateCounter);
  //   setToolchainStateCounter(toolchainStateCounter + 1);

  //   const nextState = produce(toolchainState, (draftState : toolchainStateType) => {
  //     const value = (typeof state === "function") ? state(toolchainStateRef.current) : state;
  //     return Object.assign(draftState, value);
  //   });

  //   toolchainStateRef.current = nextState;
  //   setToolchainState(nextState);
  //   console.log(nextState);
  // }, [toolchainState, setToolchainStateCounter, toolchainStateCounter, setToolchainState]);

  
  const updateStateRef = useRef(updateState);
  updateStateRef.current = updateState;
  
  useEffect(() => {
    if (toolchainWebsocket.current) { return; }

    const ws = new ToolchainSession({
      onStateChange: updateState,
      onTitleChange: () => {},
      onMessage: (message : ToolchainSessionMessage) => {
        // console.log(message);
        if (message.toolchain_session_id !== undefined) {
          sessionId.current = message.toolchain_session_id;
        }
      }
    });
    toolchainWebsocket.current = ws;


    return () => { toolchainWebsocket.current?.socket.close(); toolchainWebsocket.current = undefined;}
  }, []);

  useEffect(() => {
    console.log("Toolchain state updated: ", toolchainState);
  }, [toolchainState])


  const model_params_static = {
    "model_choice": "mistral-7b-instruct-v0.1",
    "max_tokens": 1000, 
    "temperature": 0.1, 
    "top_p": 0.1, 
    "repetition_penalty": 1.15,
    "stop": ["<|im_end|>"],
    "include_stop_str_in_output": true
  }


  useEffect(() => {
    console.log("Session ID: ", sessionId);
  }, [sessionId]);

  useEffect(() => {
    console.log("Toolchain state updated: ", toolchainState);
  }, [toolchainState]);


  const state_change_callback = useCallback((state : toolchainStateType, counter_value : number) => {
    console.log("State change", toolchainStateCounter, counter_value, state);
    setToolchainState(state);
    setToolchainStateCounter(counter_value);
  }, [toolchainState, setToolchainStateCounter, toolchainStateCounter, setToolchainState])

  useEffect(() => {
    console.log("Toolchain state updated: ", toolchainState);
  }, [toolchainStateCounter])

  const testWebsocket = () => {
    // setToolchainWebsocket(new ToolchainSession({
    //   onStateChange: state_change_callback,
    //   onTitleChange: () => {},
    //   onMessage: (message : ToolchainSessionMessage) => {
    //     // console.log(message);
    //     if (message.toolchain_session_id !== undefined) {
    //       setSessionId(message.toolchain_session_id);
    //     }
    //   }
    // }));
  }
  
  const sendMessage1 = () => {
    if (toolchainWebsocket.current) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/create",
        "arguments": {
          // "toolchain_id": "test_chat_session_normal"
          "toolchain_id": "test_chat_session_normal_streaming"
        }
      });
    }
  }

  const sendMessage2 = () => {
    if (toolchainWebsocket.current) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId.current,
          "event_node_id": "user_question_event",
          "event_parameters": {
            "model_parameters": model_params_static,
            "question": "What is the Riemann-Roch theorem?"
          }
        }
      });
    }
  }

  const sendMessage3 = () => {
    if (toolchainWebsocket.current) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId.current,
          "event_node_id": "user_question_event",
          "event_parameters": {
            "model_parameters": model_params_static,
            "question": "Who are the two people the Riemann-Roch Theorem is named after?"
          }
        }
      });
    }
  }

  const sendMessage4 = () => {
    if (toolchainWebsocket.current) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId.current,
          "event_node_id": "user_question_event",
          "event_parameters": {
            "model_parameters": model_params_static,
            "question": "You're wrong. It was named after Gustav Roch."
          }
        }
      });
    }
  }


  
  return (
    <div className="w-full h-[calc(100vh)] flex flex-row justify-center">
      <ScrollArea className="w-full">
        <div className="flex flex-row justify-center pt-10">
          <div className="max-w-[85vw] md:max-w-[70vw] lg:max-w-[45vw]">
            
            <div className="flex flex-col space-y-2">
              {/* <Button onClick={testWebsocket}>
                Test websocket.
              </Button> */}
              <Button onClick={sendMessage1}>
                Send message 1.
              </Button>
              <Button onClick={sendMessage2}>
                Question 1
              </Button>
              <Button onClick={sendMessage3}>
                Question 2
              </Button>
              <Button onClick={sendMessage4}>
                Question 3
              </Button>

              <ChatBarInput/>

              <FileDropzone onFile={(file) => console.log(file)} />

              <ScrollArea className="w-auto h-[200px] rounded-md border-[2px] border-secondary">
                <Textarea 
                  className="w-full h-full scrollbar-hide"
                  value={JSON.stringify(toolchainState, null, "\t")} 
                  onChange={() => {}}
                />
                {/* <p>{JSON.stringify(toolchainState, null, "\t")}</p> */}
              </ScrollArea>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}