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

const ToolchainContext = createContext<{
  toolchainStateCounter: number;
  setToolchainStateCounter: Dispatch<SetStateAction<number>>;
	toolchainState: toolchainStateType,
	setToolchainState: Dispatch<SetStateAction<toolchainStateType>>;
  toolchainWebsocket: MutableRefObject<ToolchainSession | undefined> | undefined;
  sessionId: MutableRefObject<string> | undefined;
}>({
  toolchainStateCounter: 0,
  setToolchainStateCounter: () => {},
	toolchainState: {},
  setToolchainState: () => {},
  toolchainWebsocket: undefined,
  sessionId: undefined,
});

export const ToolchainContextProvider = ({
	children,
}: PropsWithChildren<{}>) => {
  const [toolchain_state_counter, set_toolchain_state_counter] = useState<number>(0);
	const [toolchain_state, set_toolchain_state] = useState<toolchainStateType>({});
  const toolchain_websocket = useRef<ToolchainSession | undefined>();
  const session_id = useRef<string>("");

	return (
		<ToolchainContext.Provider value={{ 
      toolchainStateCounter: toolchain_state_counter,
      setToolchainStateCounter: set_toolchain_state_counter,
			toolchainState: toolchain_state,
      setToolchainState: set_toolchain_state,
      toolchainWebsocket: toolchain_websocket,
      sessionId: session_id
		}}>
			{children}
		</ToolchainContext.Provider>
	);
};

export const useToolchainContextAction = () => {
	return useContext(ToolchainContext);
};