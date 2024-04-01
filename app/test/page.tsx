"use client";
// import React from "react";
import { use, useEffect, useState } from "react";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Button } from "@/registry/default/ui/button";
import ToolchainSession, { ToolchainSessionMessage } from "@/hooks/toolchain-session";
import { useContextAction } from "@/app/context-provider";
import { substituteAny } from "@/types/toolchains";



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

  const [toolchainWebsocket, setToolchainWebsocket] = useState<ToolchainSession | undefined>();
  const [sessionId, setSessionId] = useState<string>();
  const [toolchainState, setToolchainState] = useState<Map<string, substituteAny>>(new Map());

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

  const testWebsocket = () => {
    setToolchainWebsocket(new ToolchainSession({
      onStateChange: (state : Map<string, substituteAny>) => {
        console.log("State change: ", state);
        setToolchainState(state);
      },
      onTitleChange: () => {},
      onMessage: (message : ToolchainSessionMessage) => {
        // console.log(message);
        if (message.toolchain_session_id !== undefined) {
          setSessionId(message.toolchain_session_id);
        }
      }
    }));
  }
  
  const sendMessage1 = () => {
    if (toolchainWebsocket) {
      toolchainWebsocket.send_message({
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
    if (toolchainWebsocket && sessionId) {
      toolchainWebsocket.send_message({
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
    if (toolchainWebsocket && sessionId) {
      toolchainWebsocket.send_message({
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
    if (toolchainWebsocket && sessionId) {
      toolchainWebsocket.send_message({
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
    </div>
  );
}