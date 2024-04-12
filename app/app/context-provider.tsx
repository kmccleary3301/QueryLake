// ThemeProvider.tsx
'use client';
import {
	PropsWithChildren,
	createContext,
	useContext,
  useState,
} from 'react';
import { substituteAny } from '@/types/toolchains';
import ToolchainSession from '@/hooks/toolchain-session';

const ToolchainContext = createContext<{
	toolchainState: Map<string, substituteAny>,
	setToolchainState: (value: Map<string, substituteAny>) => void;
  toolchainWebsocket: ToolchainSession | undefined;
  setToolchainWebsocket: (value: ToolchainSession | undefined) => void;
  sessionId: string;
  setSessionId: (value: string) => void;
}>({
	toolchainState: new Map(),
  setToolchainState: () => {},
  toolchainWebsocket: undefined,
  setToolchainWebsocket: () => {},
  sessionId: "",
  setSessionId: () => {},
});

export const ToolchainContextProvider = ({
	children,
}: PropsWithChildren<{}>) => {
	const [toolchain_state, set_toolchain_state] = useState<Map<string, substituteAny>>(new Map());
  const [toolchain_websocket, set_toolchain_websocket] = useState<ToolchainSession | undefined>();
  const [session_id, set_session_id] = useState<string>("");

	return (
		<ToolchainContext.Provider value={{ 
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