// ThemeProvider.tsx
'use client';
import {
	Dispatch,
	PropsWithChildren,
	SetStateAction,
	createContext,
	useContext,
	useState,
} from 'react';
import { displaySection } from '@/types/toolchain-interface';

const NodeContext = createContext<{
	interfaceConfiguration: displaySection;
	setInterfaceConfiguration: Dispatch<SetStateAction<displaySection>>;
}>({
	interfaceConfiguration: {
		split: "none",
		align: "center",
		tailwind: "",
		mappings: []
	},
	setInterfaceConfiguration: () => {
		return {
			split: "none",
			align: "center",
			tailwind: "",
			mappings: []
		}
	},
});

export const NodeContextProvider = ({
	interfaceConfiguration,
	children,
}: PropsWithChildren<{ 
	interfaceConfiguration : displaySection,
}>) => {
	const [interface_configuration, set_interface_configuration] = useState<displaySection>(interfaceConfiguration);

	return (
		<NodeContext.Provider value={{ 
			interfaceConfiguration: interface_configuration,
			setInterfaceConfiguration: set_interface_configuration,
		}}>
			{children}
		</NodeContext.Provider>
	);
};

export const useNodeContextAction = () => {
	return useContext(NodeContext);
};