import { 
  useState, 
  useRef, 
  useEffect,
} from "react";
import { DropDownSelection, formEntryType } from "../../manual_components/dropdown-selection";
import {
	selectedCollectionsType, 
	toolchain_session, 
	userDataType,
  setStateOrCallback
} from "@/typing/globalTypes";
import ChatWindowToolchainScrollSection from "./chat-window-scroll-section";

import { substituteAny } from "@/typing/toolchains";
import ToolchainSession from "./toochain-session";
// import { SERVER_ADDR_HTTP } from "@/config_server_hostnames";
// import ToolchainSession from "./toochain-session";

type ChatWindowToolchainProps = {
  // navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  userData: userDataType,
  pageNavigateArguments: string,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>,
  selectedCollections: selectedCollectionsType,
  active_toolchain_session : toolchain_session | undefined,
  set_active_toolchain_session : setStateOrCallback<toolchain_session>,

}

// type uploadQueueEntry = {
//   fileName: string,
//   hash_id: string,
// }

// function hexToUtf8(s : string)
// {
//   return decodeURIComponent(
//      s.replace(/\s+/g, '') // remove spaces
//       .replace(/[0-9a-f]{2}/g, '%$&') // add '%' before each 2 characters
//   );
// }

export default function ChatWindowToolchain(props : ChatWindowToolchainProps) {
  const [animateScroll, setAnimateScroll] = useState(true);
  const [availableModels, setAvailableModels] = useState<Map<string, {label : string, value : string | string[]}[]>>(new Map());
  const modelInUse = useRef<formEntryType>({label: "Default", value: "Default"});
  
  
  const [toolchainState, setToolchainState] = useState<Map<string, substituteAny>>(new Map());
  const toolchainSession = useRef<ToolchainSession>(new ToolchainSession(
    setToolchainState,
    (new_title : string) => {console.log("New title: ", new_title);},
  ));
  
  



  useEffect(() => {
    if (props.userData.available_models && props.userData.available_models !== undefined) {
      const modelSelections : {label : string, value : string | string[]}[] = [];
      for (let i = 0; i < props.userData.available_models.local_models.length; i++) {
        modelSelections.push({
          label: props.userData.available_models.local_models[i],
          value: props.userData.available_models.local_models[i]
        });
      }

      for (const [key] of Object.entries(props.userData.available_models.external_models)) {
        // console.log(`${key}: ${value}`);
        for (let i = 0; i < props.userData.available_models.external_models[key].length; i++) {
          modelSelections.push({
            label: key+"/"+props.userData.available_models.external_models[key][i],
            value: [key, props.userData.available_models.external_models[key][i]]
          });
        }
      }

      // Push modelSelections to availableModels under 'llm_models' key
      setAvailableModels(prevState => ({
        ...prevState,
        llm_models: modelSelections
      }));

      modelInUse.current = {
        label: props.userData.available_models.default_model, 
        value: props.userData.available_models.default_model
      };
    }
  }, [props.userData]);

  return (
    
      <div style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
      }}>
        <div id="ChatHeader" style={{
          width: "100%",
          height: 50,
          // backgroundColor: "#23232D",
					display: "flex",
          flexDirection: 'row',
          justifyContent: 'space-between',
          alignItems: 'center',
          // paddingBottom: 20,
          // paddingTop: 20,
        }}>
          <div style={{
            paddingLeft: 10,
            width: 200,
            // transform: [{ translateX: translateSidebarButton,},],
            // elevation: -1,
            // zIndex: 0,
            // opacity: opacitySidebarButton,
          }}>
            {/* Decide what to put here */}
          </div>
          <div style={{alignSelf: 'center'}}>
            {(availableModels !== undefined) && (
              <DropDownSelection
								selection={modelInUseState}
                values={availableModels}
                defaultValue={modelInUseState}
                setSelection={(value : formEntryType) => { setModelInUse(value); }}
                // width={400}
              />
            )}
          </div>
          <div
            style={{
              width: 200
            }}
          />
          {/* Decide what to put here */}
        </div>
        <ChatWindowToolchainScrollSection
          userData={props.userData}
          animateScroll={animateScroll}
          setAnimateScroll={setAnimateScroll}
          onMessageSend={onMessageSend}
          buttonCallbacks={buttonCallbacks}
          displayChat={displayChat}
          eventActive={eventActive}
          testEventCall={testEventCall}
          setUploadFiles={setUploadFiles}
          entryFired={entryFired}
        />
      </div>
  );
}
