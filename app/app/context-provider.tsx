// ThemeProvider.tsx
'use client';
import {
	PropsWithChildren,
	createContext,
	useContext,
  useState,
} from 'react';
import { substituteAny } from '@/types/toolchains';
import ToolchainSession, { toolchainStateType } from '@/hooks/toolchain-session';

const ToolchainContext = createContext<{
  toolchainStateCounter: number;
  setToolchainStateCounter: (value: number) => void;
	toolchainState: toolchainStateType,
	setToolchainState: (value: toolchainStateType) => void;
  toolchainWebsocket: ToolchainSession | undefined;
  setToolchainWebsocket: (value: ToolchainSession | undefined) => void;
  sessionId: string;
  setSessionId: (value: string) => void;
}>({
  toolchainStateCounter: 0,
  setToolchainStateCounter: () => {},
	toolchainState: {},
  setToolchainState: () => {},
  toolchainWebsocket: undefined,
  setToolchainWebsocket: () => {},
  sessionId: "",
  setSessionId: () => {},
});

export const ToolchainContextProvider = ({
	children,
}: PropsWithChildren<{}>) => {
  const [toolchain_state_counter, set_toolchain_state_counter] = useState<number>(0);
	const [toolchain_state, set_toolchain_state] = useState<toolchainStateType>({});
  const [toolchain_websocket, set_toolchain_websocket] = useState<ToolchainSession | undefined>();
  const [session_id, set_session_id] = useState<string>("");

	return (
		<ToolchainContext.Provider value={{ 
      toolchainStateCounter: toolchain_state_counter,
      setToolchainStateCounter: set_toolchain_state_counter,
			toolchainState: toolchain_state,
      setToolchainState: set_toolchain_state,
      toolchainWebsocket: toolchain_websocket,
      setToolchainWebsocket: set_toolchain_websocket,
      sessionId: session_id,
      setSessionId: set_session_id,
		}}>
			{children}
		</ToolchainContext.Provider>
	);
};

export const useToolchainContextAction = () => {
	return useContext(ToolchainContext);
};