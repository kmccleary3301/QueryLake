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
import { toolchain_session } from "@/types/globalTypes";
import { toast } from "sonner";

export default function AppPage({ params, searchParams }: DocPageProps) {
  const [isPending, startTransition] = useTransition();

  const router = useRouter(),
        pathname = usePathname(),
        search_params = useSearchParams();
  
  const app_mode_immediate = (["create", "session", "view"].indexOf(params["slug"][0]) > -1) ? params["slug"][0] as app_mode_type : undefined;
  const appMode = useRef<app_mode_type>(app_mode_immediate);
  const [appModeState, setAppModeState] = useState(app_mode_immediate);
  const mounting = useRef(true);
  const toolchainStateRef = useRef<toolchainStateType>({});
  const [firstEventRan, setFirstEventRan] = useState<boolean[]>([false, false]);
  const [toolchainSelectedBySession, setToolchainSelectedBySession] = useState<string | undefined>(undefined);

  const {
    toolchainState,
    setToolchainState,
    toolchainWebsocket,
    sessionId,
    callEvent,
    setCurrentEvent,
  } = useToolchainContextAction();

  const {
    userData,
    setSelectedToolchain,
    selectedToolchainFull,
    toolchainSessions,
    setToolchainSessions,
    activeToolchainSession,
    setActiveToolchainSession,
  } = useContextAction();
  
  const setCurrentToolchainSession = (title: string) => {
    console.log("Setting toolchain session with", sessionId?.current, title, search_params?.get("s"), appMode.current, pathname, activeToolchainSession);

    const new_session_make : toolchain_session = {
      time: toolchainSessions.has(sessionId?.current as string) ? 
            toolchainSessions.get(sessionId?.current as string)?.time as number :
            Math.floor(Date.now() / 1000),
      toolchain: selectedToolchainFull?.id as string,
      id: sessionId?.current as string,
      title: title || "Untitled Session"
    };

    setToolchainSessions((prevSessions) => {
      // Create a new Map from the previous one
      const newMap = new Map(prevSessions);
      // Update the new Map
      newMap.set(sessionId?.current as string, new_session_make);
      // Return the new Map to update the state
      return newMap;
    });
    setActiveToolchainSession(sessionId?.current);
  }

  useEffect(() => {
    console.log("TITLE CHANGED, UPDATING WITH", toolchainState.title);
    // if (sessionId !== undefined) sessionId.current = searchParams?.s as string;
    if (sessionId === undefined || 
        sessionId.current === "" || 
        sessionId.current === "undefined" || 
        !toolchainState.title ||
        !toolchainSessions.has(sessionId.current) ||
        toolchainSessions.get(sessionId.current)?.title === toolchainState.title
      ) return;
    console.log("FOLLOWING THROUGH");
    setCurrentToolchainSession(toolchainState.title as string || "Untitled Session");
  }, [toolchainState?.title]);

  useEffect(() => {
    let newFirstEventRan = firstEventRan;
    // if (sessionId !== undefined) sessionId.current = searchParams?.s as string;
    if (sessionId && sessionId.current && newFirstEventRan[0] && !newFirstEventRan[1] && !toolchainSessions.has(sessionId.current)) {
      
      console.log("FIRST EVENT RAN; PUSHING SESSION TO HISTORY");
      setCurrentToolchainSession(toolchainStateRef.current.title as string);
    }


    if (!newFirstEventRan[0] && newFirstEventRan[1]) {
      newFirstEventRan = [false, false];
      setFirstEventRan(newFirstEventRan);
    }

    if (appMode.current === "create" && newFirstEventRan[0] && newFirstEventRan[1] && sessionId?.current !== undefined) {
      console.log("FIRST EVENT RAN; PUSHING TO SESSION");
      startTransition(() => {
        window.history.pushState(null, '', `/app/session?s=${sessionId?.current}`);
      });

      setToolchainSelectedBySession(selectedToolchainFull?.id);

      setFirstEventRan([false, false]);
      if (selectedToolchainFull?.first_event_follow_up)
        callEvent(userData?.auth as string, selectedToolchainFull.first_event_follow_up, {})
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
      onStateChange: (state) => {
        // toolchainStateRef.current = state;
        updateState(state);
      },
      onCallEnd: () => {
        setFirstEventRan((prevState) => [prevState[0], true]);
      },
      onMessage: (message : ToolchainSessionMessage) => {
        if (message.toolchain_session_id !== undefined) {
          sessionId.current = message.toolchain_session_id;
        }
        if (message.toolchain_id !== undefined) {
          console.log("Toolchain ID from loaded Toolchain:", [message.toolchain_id]);
          setSelectedToolchain(message.toolchain_id);
          // setToolchainSelectedBySession(message.toolchain_id);
        }

        if (message.error) {
          toast(message.error);
        }
      },
      onSend: (message : {command?: string}) => {
        if (message.command && message.command === "toolchain/event" && appMode) {
          setFirstEventRan((prevState) => [true, prevState[1]]);
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
            setToolchainState({});
            session.send_message({
              "auth": userData?.auth,
              "command" : "toolchain/load",
              "arguments": {
                "session_id": sessionId.current as string,
              }
            });
          }
          mounting.current = false;
        }
      },
      onCurrentEventChange: (event: string | undefined) => { setCurrentEvent(event); }
    });
  };

  // This is a URL change monitor to refresh content.
  useEffect(() => {
    if (selectedToolchainFull === undefined) return;
    console.log("URL Change", pathname, search_params?.get("s"));
    const url_mode = pathname?.replace(/^\/app\//, "").split("/")[0] as string;
    const new_mode = (["create", "session", "view"].indexOf(url_mode) > -1) ? url_mode as app_mode_type : undefined;
    setAppModeState(new_mode);

    if (new_mode === "create") {
      setToolchainSelectedBySession(selectedToolchainFull.id);
    }

    if (new_mode === "session" && (sessionId !== undefined) && search_params?.get("s") !== sessionId?.current) {
      console.log("Session ID Change", search_params?.get("s"), sessionId?.current);
      sessionId.current = search_params?.get("s") as string;
      setActiveToolchainSession(sessionId.current);
      initializeWebsocket();
    }

    else if (new_mode === "create" && appMode.current !== "create") {
      initializeWebsocket();
      setFirstEventRan([false, false]);
      setCurrentToolchainSession(toolchainState.title as string || "Untitled Session");
      setActiveToolchainSession(undefined);
    } else if (new_mode === "create") {
      initializeWebsocket();
      setActiveToolchainSession(undefined);
    }
    appMode.current = new_mode;
  }, [pathname, search_params, selectedToolchainFull]);

  return (
    <div className="h-[100vh] w-full pr-0 pl-0">
      {(selectedToolchainFull !== undefined && selectedToolchainFull.display_configuration) &&
      //  ((toolchainSelectedBySession === selectedToolchainFull.id) || 
      //   (appModeState === "create")) && 
        (
        <DivisibleSection
          section={selectedToolchainFull.display_configuration}
        />
      )}
    </div>
  );
}

