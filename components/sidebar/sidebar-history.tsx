"use client";
import * as Icon from 'react-feather';
import HoverDocumentEntry from '../manual_components/hover_document_entry';
import { ScrollArea } from '@/registry/default/ui/scroll-area';
import { Button } from '@/registry/default/ui/button';
import { userDataType, timeWindowType, collectionGroup, toolchain_session, setStateOrCallback } from '@/types/globalTypes';
import { useState, useEffect } from 'react';

type SidebarChatHistoryProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  toolchain_sessions : Map<string, toolchain_session>,
  set_toolchain_sessions : setStateOrCallback<Map<string, toolchain_session>>,
  active_toolchain_session : toolchain_session | undefined,
  set_active_toolchain_session : setStateOrCallback<toolchain_session>,
  scrollClassName : string,
}
  
export default function SidebarChatHistory(props: SidebarChatHistoryProps) {
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
      <ScrollArea className={props.scrollClassName}
      >
        <div className='pb-10'>
          <Button variant={"ghost"} className="w-full flex flex-row rounded-2xl h-9 items-center justify-center"
            onClick={() => {
              // TODO : Implement new chat
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
              <p className="w-full text-left text-base text-gray-700 pb-8 pt-8">
                {chat_history_window.title}
              </p>
              {chat_history_window.entries.map((value : toolchain_session, index : number) => (
                <div className="pt-0 pb-0" key={index}>
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
                      // TODO : Implement chat history navigation
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