// ThemeProvider.tsx
'use client';
import {
	PropsWithChildren,
	createContext,
	useContext,
	useRef,
} from 'react';
import { displaySection } from '@/types/toolchain-interface';

const NodeContext = createContext<{
	interfaceConfiguration: displaySection;
	setInterfaceConfiguration: (value: displaySection) => void;
	getInterfaceConfiguration: () => displaySection;
}>({
	interfaceConfiguration: {
		split: "none",
		size: 100,
		align: "center",
		tailwind: "",
		mappings: []
	},
	setInterfaceConfiguration: () => {
		return {
			split: "none",
			size: 100,
			align: "center",
			tailwind: "",
			mappings: []
		}
	},
	getInterfaceConfiguration: () => {
		return {
			split: "none",
			size: 100,
			align: "center",
			tailwind: "",
			mappings: []
		}
	}
});

export const NodeContextProvider = ({
	interfaceConfiguration,
	children,
}: PropsWithChildren<{ 
	interfaceConfiguration : displaySection,
}>) => {
	// const [interface_configuration, set_interface_configuration] = useState<displaySection>(interfaceConfiguration);
	const interface_configuration = useRef<displaySection>(interfaceConfiguration);
	const set_interface_configuration = (value: displaySection) => {
		interface_configuration.current = value;
		// console.log(interface_configuration.current);
	};
	const get_interface_configuration : () => displaySection = () => {
		return interface_configuration.current;
	};

	return (
		<NodeContext.Provider value={{ 
			interfaceConfiguration: interface_configuration.current,
			setInterfaceConfiguration: set_interface_configuration,
			getInterfaceConfiguration: get_interface_configuration
		}}>
			{children}
		</NodeContext.Provider>
	);
};

export const useNodeContextAction = () => {
	return useContext(NodeContext);
};