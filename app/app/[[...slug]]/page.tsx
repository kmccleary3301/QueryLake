"use client";
interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: {s? : string}
}

type app_mode_type = "create" | "session" | "view" | undefined;

/**
 * v0 by Vercel.
 * @see https://v0.dev/t/n2FrFZXZwwu
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useContextAction } from "@/app/context-provider";
import { useRouter } from 'next/navigation';
import { ToolChain, substituteAny } from '@/types/toolchains';
import ToolchainSession, { ToolchainSessionMessage } from "@/hooks/toolchain-session";
import { DivisibleSection } from "../components/section-divisible";
import { useToolchainContextAction } from "../context-provider";

export default function AppPage({ params, searchParams }: DocPageProps) {

  const router = useRouter();
  const app_mode_immediate = (["create", "session", "view"].indexOf(params["slug"][0]) > -1) ? params["slug"][0] as app_mode_type : undefined;
  const [appMode, setAppMode] = useState<app_mode_type>(app_mode_immediate);
  const mounting = useRef(true);

  const { 
    toolchainState,
    setToolchainState,
    toolchainWebsocket,
    setToolchainWebsocket,
    sessionId,
    setSessionId,
  } = useToolchainContextAction();

  const {
    userData,
    selectedToolchain,
    selectedToolchainFull,
  } = useContextAction();
  
  useEffect(() => {
    console.log("Session ID: ", sessionId);
  }, [sessionId]);

  useEffect(() => {
    console.log("Toolchain state updated: ", toolchainState);
  }, [toolchainState]);
  

  const initializeWebsocket = useCallback(() => {
    setToolchainState(new Map());
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
      },
      onOpen: (session: ToolchainSession) => {
        if (mounting.current && toolchainWebsocket !== undefined) {
          if (appMode === "create") {
            console.log("Creating toolchain");
            session.send_message({
              "auth": userData?.auth,
              "command" : "toolchain/create",
              "arguments": {
                // "toolchain_id": "test_chat_session_normal"
                "toolchain_id": selectedToolchain?.id,
              }
            });
          } else if (appMode === "session") {
            if (searchParams.s === undefined) {
              console.error("No session ID provided");
              router.push("/app/create");
              return;
            }
            console.log("Loading toolchain");
            setToolchainState(new Map());
            session.send_message({
              "auth": userData?.auth,
              "command" : "toolchain/createtoolchain/load",
              "arguments": {
                // "toolchain_id": "test_chat_session_normal"
                "session_id": searchParams.s as string,
              }
            });
          }
          mounting.current = false;
        }
      }
    }));
  }, [appMode, selectedToolchainFull, userData]);

  useEffect(() => {
    if (mounting.current) initializeWebsocket();
    mounting.current = false;
  }, [userData, selectedToolchainFull])

  return (
    <div className="h-[calc(100vh-60px)] w-full pr-0 pl-0">
      {(selectedToolchainFull !== undefined && selectedToolchainFull.display_configuration) && 
       (toolchainWebsocket !== undefined) && (
        <DivisibleSection
          section={selectedToolchainFull.display_configuration}
        />
      )}
    </div>
  );
}

