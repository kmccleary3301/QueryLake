
// import { Feather } from '@expo/vector-icons';
import * as Icon from 'react-feather';
// import AnimatedPressable from './AnimatedPressable';
// import HoverDocumentEntry from './HoverDocumentEntry';
import HoverDocumentEntry from '../manual_components/hover_document_entry';
// import craftUrl from '@/hooks/craftUrl';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import { userDataType, timeWindowType, collectionGroup, toolchain_session, setStateOrCallback } from '@/typing/globalTypes';
import { useNavigate } from 'react-router-dom';
// import { SERVER_ADDR_HTTP } from '@/config_server_hostnames';
import { useState, useEffect } from 'react';

type SidebarChatHistoryProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  pageNavigateArguments: string,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
  refreshSidePanel: string[],
  toolchain_sessions : Map<string, toolchain_session>,
  set_toolchain_sessions : setStateOrCallback<Map<string, toolchain_session>>,
  active_toolchain_session : toolchain_session | undefined,
  set_active_toolchain_session : setStateOrCallback<toolchain_session>,
}
  
export default function SidebarChatHistory(props: SidebarChatHistoryProps) {
	const navigate = useNavigate();
  const [internalToolchainSessions, setInternalToolchainSessions] = useState<timeWindowType[]>([]);

  useEffect(() => {
    const timeWindows : timeWindowType[] = [
			{title: "Last 24 Hours", cutoff: 24*3600, entries: []},
			{title: "Last 2 Days", cutoff: 2*24*3600, entries: []},
			{title: "Past Week", cutoff: 7*24*3600, entries: []},
			{title: "Past Month", cutoff: 30*24*3600, entries: []},
		];

    const newToolchainSessions = new Map<string, toolchain_session>();
    props.toolchain_sessions.forEach((session : toolchain_session) => {
      newToolchainSessions.set(session.id, session);
      const time = Math.floor((new Date().getTime() - session.time)/1000);
      for (let i = 0; i < timeWindows.length; i++) {
        if (time < timeWindows[i].cutoff) {
          timeWindows[i].entries.push(session);
        }
      }
    });
    setInternalToolchainSessions(timeWindows);
  }, [props.toolchain_sessions])


  const deleteSession = (hash_id : string) => {
    // TODO : Implement delete session with API
    
    props.toolchain_sessions.delete(hash_id)

    props.set_toolchain_sessions(props.toolchain_sessions);
  };
  
  return (
    <>
      <ScrollArea className="h-[calc(100vh-262px)]" style={{
          width: '100%',
          paddingLeft: 22,
					paddingRight: 22,
          paddingTop: 0,
        }}
      >
        <div style={{paddingBottom: 10}}>
          <Button variant={"ghost"} style={{
            width: '100%',
            // backgroundColor: '#39393C',
						display: 'flex',
            flexDirection: 'row',
            borderRadius: 20,
            // justifyContent: 'space-around',
            height: 36,
            alignItems: 'center',
            justifyContent: 'center'}}
            onClick={() => {
              if (props.pageNavigateArguments === "NEW") {
                props.setPageNavigateArguments(" NEW");
              } else {
                props.setPageNavigateArguments("NEW");
              }
              navigate("/chat");
            }}>
              <div style={{paddingRight: 5}}>
                <Icon.Plus size={20} color="#E8E3E3" />
              </div>
              <div style={{alignSelf: 'center', justifyContent: 'center'}}>
              <p style={{
                // width: '100%',
                // height: '100%',
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#E8E3E3',
                paddingTop: 1
              }}>{"New Chat"}</p>
              </div>
          </Button>
        </div>
        {internalToolchainSessions.map((chat_history_window : timeWindowType, chat_history_index : number) => (
          <div key={chat_history_index}>
            {(chat_history_window.entries.length > 0) && (
              <>
              <p style={{
                width: "100%",
                textAlign: 'left',
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#74748B',
                paddingBottom: 8,
                paddingTop: 8
              }}>
                {chat_history_window.title}
              </p>
              {chat_history_window.entries.map((value : toolchain_session, index : number) => (
                <div style={{paddingTop: 0, paddingBottom: 0}} key={index}>
                  <HoverDocumentEntry
                    key={index}
                    title={(value.title !== null)?value.title:"Test"}
                    deleteIndex={() => {
                      deleteSession(value.id);
                    }}
                    textStyle={{
                      width: "100%",
                      textAlign: 'left',
                      paddingLeft: 10,
                      // fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      color: '#E8E3E3',
											// height: "100%",
                    }}
										style={{
											width: "100%"
										}}
                    onPress={() => {
                      props.set_active_toolchain_session(value);
                      props.setPageNavigateArguments("chatSession-"+value.id);
                      navigate("/chat");
                    }}
                  />
                </div>
              ))}
              </>
            )}
          </div>
        ))}
       
      </ScrollArea>
    </> 
  );
}