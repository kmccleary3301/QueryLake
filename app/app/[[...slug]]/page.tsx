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
        if (message.command && message.command === "toolchain/event") {
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
    const url_mode = pathname?.replace(/^\/app\//, "").split("/")[0] as string;
    const new_mode = (["create", "session", "view"].indexOf(url_mode) > -1) ? url_mode as app_mode_type : undefined;
    
    if (new_mode === "session" && search_params?.get("s") !== undefined && sessionId !== undefined) {
      sessionId.current = search_params?.get("s") as string;
    }

    if (new_mode === "create" && appMode.current !== "create") {
      initializeWebsocket();
    }
    
    appMode.current = new_mode;
  }, [pathname]);

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

