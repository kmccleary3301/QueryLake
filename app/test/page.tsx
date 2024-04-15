"use client";
// import React from "react";
import { use, useCallback, useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Button } from "@/registry/default/ui/button";
import ToolchainSession, { ToolchainSessionMessage, toolchainStateType } from "@/hooks/toolchain-session";
import { useContextAction } from "@/app/context-provider";
import { substituteAny } from "@/types/toolchains";
import ChatBarInput from "@/components/manual_components/chat-input-bar";
import FileDropzone from "@/registry/default/ui/file-dropzone";
import { Textarea } from "@/registry/default/ui/textarea";



interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

export default function TestPage() {
  const {
    userData,
  } = useContextAction();

  const toolchainWebsocket = useRef<ToolchainSession | undefined>();
  const [sessionId, setSessionId] = useState<string>();
  const [toolchainState, setToolchainState] = useState<toolchainStateType>({});
  const toolchainStateRef = useRef<toolchainStateType>({});

  const [toolchainStateCounter, setToolchainStateCounter] = useState<number>(0);

  const model_params_static = {
    "model_choice": "mistral-7b-instruct-v0.1",
    "max_tokens": 1000, 
    "temperature": 0.1, 
    "top_p": 0.1, 
    "repetition_penalty": 1.15,
    "stop": ["<|im_end|>"],
    "include_stop_str_in_output": true
  }


  // useEffect(() => {
  //   console.log("Session ID: ", sessionId);
  // }, [sessionId]);

  useEffect(() => {
    console.log("Toolchain state updated: ", toolchainState);
  }, [toolchainState]);


  const state_change_callback = useCallback((state : toolchainStateType) => {
    // console.log("State change", toolchainStateCounter, counter_value, state);
    setToolchainState(JSON.parse(JSON.stringify(state)));
  }, [toolchainState, setToolchainStateCounter, toolchainStateCounter, setToolchainState])

  const get_state_callback = useCallback(() => {
    return toolchainState;
  }, [toolchainState]);

  const set_state_callback = (value : toolchainStateType) => {
    toolchainStateRef.current = value;
  }

  // useEffect(() => {
  //   if (toolchainWebsocket.current) {
  //     toolchainWebsocket.current.getState = get_state_callback;
  //   }
  // }, [get_state_callback]);

  // useEffect(() => {
  //   console.log("Toolchain state updated: ", toolchainState);
  // }, [toolchainStateCounter])

  const testWebsocket = () => {
    toolchainWebsocket.current = new ToolchainSession({
      onStateChange: setToolchainState,
      onTitleChange: () => {},
      onMessage: (message : ToolchainSessionMessage) => {
        // console.log(message);
        if (message.toolchain_session_id !== undefined) {
          setSessionId(message.toolchain_session_id);
        }
      }
    });
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
    if (toolchainWebsocket.current && sessionId) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId,
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
    if (toolchainWebsocket.current && sessionId) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId,
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
    if (toolchainWebsocket.current && sessionId) {
      toolchainWebsocket.current.send_message({
        "auth": userData?.auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": sessionId,
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
    <div className="flex flex-col space-y-2">
      <Button onClick={testWebsocket}>
        Test websocket.
      </Button>
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
  );
}