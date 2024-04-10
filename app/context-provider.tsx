// ThemeProvider.tsx
'use client';
import {
	Dispatch,
	PropsWithChildren,
	SetStateAction,
	createContext,
	useContext,
	useEffect,
	useState,
} from 'react';
import { 
	selectedCollectionsType, 
	userDataType,
	setStateOrCallback,
	toolchain_session,
	toolchain_type,
	collectionGroup
} from '@/types/globalTypes';
import { deleteCookie, getCookie, setCookie } from '@/hooks/cookies';
import { useRouter } from 'next/navigation';
import { usePathname } from "next/navigation";
import craftUrl from '@/hooks/craftUrl';
import { getUserCollections } from '@/hooks/querylakeAPI';

export type breakpointType = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';

const Context = createContext<{
	userData: userDataType | undefined;
	setUserData: Dispatch<SetStateAction<userDataType | undefined>>;

	collectionGroups: collectionGroup[];
	setCollectionGroups: Dispatch<SetStateAction<collectionGroup[]>>;
	refreshCollectionGroups: () => void;

	selectedCollections: selectedCollectionsType;
	setSelectedCollections: Dispatch<SetStateAction<selectedCollectionsType>>;

	toolchainSessions : Map<string, toolchain_session>,
	setToolchainSessions : setStateOrCallback<Map<string, toolchain_session>>

	activeToolchainSession : toolchain_session | undefined,
	setActiveToolchainSession : setStateOrCallback<toolchain_session>,

	selectedToolchain : toolchain_type | undefined,
	setSelectedToolchain : setStateOrCallback<toolchain_type>,

	authReviewed : boolean,
	setAuthReviewed : setStateOrCallback<boolean>,

	loginValid : boolean,
	setLoginValid : setStateOrCallback<boolean>,

	getUserData : (user_data_input : userDataType | undefined, onFinish : () => void) => void,

	breakpoint : breakpointType,
}>({
	userData: undefined,
	setUserData: () => undefined,

	collectionGroups: [],
	setCollectionGroups: () => [],
	refreshCollectionGroups: () => {},

	selectedCollections: new Map(),
	setSelectedCollections: () => new Map(),

	toolchainSessions: new Map(),
	setToolchainSessions: () => new Map(),

	activeToolchainSession: undefined,
	setActiveToolchainSession: () => undefined,

	selectedToolchain: undefined,
	setSelectedToolchain: () => undefined,

	authReviewed: false,
	setAuthReviewed: () => false,

	loginValid: false,
	setLoginValid: () => false,

	getUserData: () => undefined,

	breakpoint: '2xl',
});


type login_results = {
  success: false,
  error: string
} | {
  success: true,
  result: userDataType
};


export const ContextProvider = ({
	userData,
	selectedCollections,
	toolchainSessions,
	children,
}: PropsWithChildren<{ 
	userData : userDataType | undefined , 
	selectedCollections : selectedCollectionsType,
	toolchainSessions : Map<string, toolchain_session>
}>) => {
	const pathname = usePathname();
	const router = useRouter();

	const [user_data, set_user_data] = useState<userDataType | undefined>(userData);
	const [collection_groups, set_collection_groups] = useState<collectionGroup[]>([]);
	const [selected_collections, set_selected_collections] = useState<selectedCollectionsType>(selectedCollections);
	const [toolchain_sessions, set_toolchain_sessions] = useState<Map<string, toolchain_session>>(toolchainSessions);
	const [active_toolchain_session, set_active_toolchain_session] = useState<toolchain_session | undefined>(undefined);
	const [selected_toolchain, set_selected_toolchain] = useState<toolchain_type | undefined>(undefined);
	const [auth_reviewed, set_auth_reviewed] = useState<boolean>(false);
	const [login_valid, set_login_valid] = useState<boolean>(false);
	const [break_point, set_breakpoint] = useState<breakpointType>('2xl');


	useEffect(() => {
    if (process.env.NODE_ENV === "production") return;

    const breakpoints : breakpointType[] = ['xs', 'sm', 'md', 'lg', 'xl', '2xl'];
    const widths = [0, 640, 768, 1024, 1280, 1536];

		const updateBreakpoint = () => {
			const width = window.innerWidth;
			let index = widths.findIndex(w => width < w);
			if (index !== -1) {
				index = index === 0 ? 0 : index - 1;
			} else {
				index = breakpoints.length - 1;
			}
			set_breakpoint(breakpoints[index]);
		};

    window.addEventListener('resize', updateBreakpoint);

    updateBreakpoint();

    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

	// useEffect(() => {console.log("BREAKPOINT:", break_point)}, [break_point]);


	const get_user_data = async (user_data_input : userDataType | undefined, onFinish : () => void) => {
		if (user_data_input !== undefined) {
			const url = craftUrl(`/api/login`, {
				"auth": user_data_input.auth
			});

			fetch(url).then((response) => {
				// console.log("Fetching");
				// console.log(response);
				response.json().then((data : login_results) => {
					// console.log("Got data:", data);
					if (data.success) {
						setCookie({ key: "UD", value: data.result })
						set_user_data(user_data_input);

						set_login_valid(true);
						set_auth_reviewed(true);

						onFinish();
					} else {
						deleteCookie({ key: 'UD' });
						set_user_data(undefined);

						set_login_valid(false);
						set_auth_reviewed(true);

						onFinish();
					}
				});
			});
		} else {
			set_login_valid(false);
			set_auth_reviewed(true);

			onFinish();
		}
	};


	const refresh_collection_groups = () => {
		getUserCollections({
			auth: user_data?.auth as string, 
			set_value: set_collection_groups
		});
	}

	
	return (
		<Context.Provider value={{ 
			userData : user_data, 
			setUserData : set_user_data,
			collectionGroups : collection_groups,
			setCollectionGroups : set_collection_groups,
			refreshCollectionGroups : refresh_collection_groups,
			selectedCollections : selected_collections,
			setSelectedCollections : set_selected_collections,
			toolchainSessions : toolchain_sessions,
			setToolchainSessions : set_toolchain_sessions,
			activeToolchainSession : active_toolchain_session,
			setActiveToolchainSession : set_active_toolchain_session,
			selectedToolchain : selected_toolchain,
			setSelectedToolchain : set_selected_toolchain,
			authReviewed : auth_reviewed,
			setAuthReviewed : set_auth_reviewed,
			loginValid : login_valid,
			setLoginValid : set_login_valid,
			getUserData : get_user_data,
			breakpoint : break_point,
		}}>
			{children}
		</Context.Provider>
	);
};

export const useContextAction = () => {
	return useContext(Context);
};