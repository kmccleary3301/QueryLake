'use client';
import {
  Dispatch,
  MutableRefObject,
	PropsWithChildren,
	SetStateAction,
	createContext,
	useContext,
  useRef,
  useState,
} from 'react';
import ToolchainSession, { toolchainStateType } from '@/hooks/toolchain-session';
import { substituteAny } from '@/types/toolchains';

const ToolchainContext = createContext<{
  toolchainStateCounter: number;
  setToolchainStateCounter: Dispatch<SetStateAction<number>>;
	toolchainState: toolchainStateType,
	setToolchainState: Dispatch<SetStateAction<toolchainStateType>>;
  toolchainWebsocket: MutableRefObject<ToolchainSession | undefined> | undefined;
  sessionId: MutableRefObject<string> | undefined;
  callEvent: (auth: string, event: string, event_params: {[key : string]: substituteAny}) => void;
}>({
  toolchainStateCounter: 0,
  setToolchainStateCounter: () => {},
	toolchainState: {},
  setToolchainState: () => {},
  toolchainWebsocket: undefined,
  sessionId: undefined,
  callEvent: () => {},
});

export const ToolchainContextProvider = ({
	children,
}: PropsWithChildren<{}>) => {
  const [toolchain_state_counter, set_toolchain_state_counter] = useState<number>(0);
	const [toolchain_state, set_toolchain_state] = useState<toolchainStateType>({});
  const toolchain_websocket = useRef<ToolchainSession | undefined>();
  const session_id = useRef<string>("");

  const call_event = (
    auth: string,
    event: string, 
    event_params: {[key : string]: substituteAny}
  ) => {
    if (toolchain_websocket?.current && session_id?.current) {
      console.log("Sending Event", event, event_params);
      toolchain_websocket.current.send_message({
        "auth": auth,
        "command" : "toolchain/event",
        "arguments": {
          "session_id": session_id.current,
          "event_node_id": event,
          "event_parameters": event_params
        }
      });
    }
  };


	return (
		<ToolchainContext.Provider value={{ 
      toolchainStateCounter: toolchain_state_counter,
      setToolchainStateCounter: set_toolchain_state_counter,
			toolchainState: toolchain_state,
      setToolchainState: set_toolchain_state,
      toolchainWebsocket: toolchain_websocket,
      sessionId: session_id,
      callEvent: call_event
		}}>
			{children}
		</ToolchainContext.Provider>
	);
};

export const useToolchainContextAction = () => {
	return useContext(ToolchainContext);
};