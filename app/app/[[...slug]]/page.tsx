"use client";
interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: {s? : string}
}

type app_mode_type = "create" | "session" | "view" | undefined;

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { useContextAction } from "@/app/context-provider";
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import ToolchainSession, { CallbackOrValue, ToolchainSessionMessage, toolchainStateType } from "@/hooks/toolchain-session";
import { DivisibleSection } from "../components/section-divisible";
import { useToolchainContextAction } from "../context-provider";
import { set } from "date-fns";
import path from "path";

export default function AppPage({ params, searchParams }: DocPageProps) {
  const [isPending, startTransition] = useTransition();

  const router = useRouter(),
        pathname = usePathname(),
        search_params = useSearchParams();
  
  const app_mode_immediate = (["create", "session", "view"].indexOf(params["slug"][0]) > -1) ? params["slug"][0] as app_mode_type : undefined;
  const appMode = useRef<app_mode_type>(app_mode_immediate);
  const mounting = useRef(true);
  const toolchainStateRef = useRef<toolchainStateType>({});
  const [firstEventRan, setFirstEventRan] = useState<boolean[]>([false, false]);

  const {
    toolchainState,
    setToolchainState,
    toolchainWebsocket,
    sessionId
  } = useToolchainContextAction();

  const {
    userData,
    selectedToolchainFull,
    toolchainSessions,
    setToolchainSessions,
  } = useContextAction();

  useEffect(() => {
    let newFirstEventRan = firstEventRan;
    if (!newFirstEventRan[0] && newFirstEventRan[1]) {
      newFirstEventRan = [false, false];
      setFirstEventRan(newFirstEventRan);
    }

    if (appMode.current === "create" && newFirstEventRan[0] && newFirstEventRan[1] && sessionId?.current !== undefined) {
      console.log("FIRST EVENT RAN; PUSHING TO SESSION");
      startTransition(() => {
        window.history.pushState(null, '', `/app/session?s=${sessionId?.current}`);
      });
      setFirstEventRan([false, false]);
    }
  }, [firstEventRan]);

  const updateState = useCallback((state: CallbackOrValue<toolchainStateType>) => {
    const value = (typeof state === "function") ? state(toolchainStateRef.current) : state;
    toolchainStateRef.current = value;
    const value_copied = JSON.parse(JSON.stringify(value));
    setToolchainState(value_copied);
  }, [toolchainState, setToolchainState]);

  const initializeWebsocket = () => {
    if (toolchainWebsocket === undefined || sessionId === undefined) return;
    setToolchainState({});
    toolchainWebsocket.current = new ToolchainSession({
      onStateChange: updateState,
      onCallEnd: () => {
        setFirstEventRan((prevState) => [prevState[0], true]);
      },
      onMessage: (message : ToolchainSessionMessage) => {
        if (message.toolchain_session_id !== undefined) {
          sessionId.current = message.toolchain_session_id;
        }
      },
      onSend: (message : {command?: string}) => {
        if (message.command && message.command === "toolchain/event" && pathname === "/app/create") {
          setFirstEventRan((prevState) => [true, prevState[1]]);
          if (sessionId.current !== undefined) {
            const new_sessions = toolchainSessions;
            const new_session = {
              time: Math.floor(Date.now() / 1000),
              toolchain: selectedToolchainFull?.id as string,
              id: sessionId?.current as string,
              title: toolchainState.title as string || "Untitled Session"
            };
            new_sessions.set(sessionId.current as string, new_session);
            setToolchainSessions(new_sessions);
          }
        }
      },
      onOpen: (session: ToolchainSession) => {
        if (true) {
          if (appMode.current === "create") {
            session.send_message({
              "auth": userData?.auth,
              "command" : "toolchain/create",
              "arguments": {
                // "toolchain_id": "test_chat_session_normal"
                "toolchain_id": selectedToolchainFull?.id,
              }
            });
          } else if (appMode.current === "session") {
            if (sessionId.current === undefined) {
              console.error("No session ID provided");
              router.push("/app/create");
              return;
            }
            console.log("Loading toolchain");
            setToolchainState({});
            session.send_message({
              "auth": userData?.auth,
              "command" : "toolchain/load",
              "arguments": {
                // "toolchain_id": "test_chat_session_normal"
                "session_id": sessionId.current as string,
              }
            });
          }
          mounting.current = false;
        }
      }
    });
  };

  useEffect(() => {
    if (selectedToolchainFull === undefined) return;
    if (mounting.current) initializeWebsocket();
    mounting.current = false;
  }, [userData, selectedToolchainFull, initializeWebsocket]);

  // This is a URL change monitor to refresh content.
  useEffect(() => {
    console.log("URL Change", pathname, search_params?.get("s"));
    const url_mode = pathname?.replace(/^\/app\//, "").split("/")[0] as string;
    const new_mode = (["create", "session", "view"].indexOf(url_mode) > -1) ? url_mode as app_mode_type : undefined;
    
    console.log((new_mode === "session" ));
    console.log((sessionId !== undefined));
    console.log((search_params?.get("s") !== sessionId?.current));
    
    if (new_mode === "session" && (sessionId !== undefined) && search_params?.get("s") !== sessionId?.current) {
      console.log("Session ID Change", search_params?.get("s"), sessionId?.current);
      sessionId.current = search_params?.get("s") as string;
      initializeWebsocket();
      return;
    }

    if (new_mode === "session" && search_params?.get("s") !== undefined && sessionId !== undefined) {
      sessionId.current = search_params?.get("s") as string;
    }

    if (new_mode === "create" && appMode.current !== "create") {
      initializeWebsocket();
      setFirstEventRan([false, false]);
    }

    
    appMode.current = new_mode;
  }, [pathname, search_params]);

  return (
    <div className="h-[calc(100vh-60px)] w-full pr-0 pl-0">
      {(selectedToolchainFull !== undefined && selectedToolchainFull.display_configuration) && (
        <DivisibleSection
          section={selectedToolchainFull.display_configuration}
        />
      )}
    </div>
  );
}

