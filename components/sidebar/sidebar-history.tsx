"use client";
import * as Icon from 'react-feather';
import HoverDocumentEntry from '../manual_components/hover_document_entry';
import { ScrollArea } from '@/registry/default/ui/scroll-area';
import { Button } from '@/registry/default/ui/button';
import { userDataType, timeWindowType, collectionGroup, toolchain_session, setStateOrCallback } from '@/types/globalTypes';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useContextAction } from "@/app/context-provider";
import { Trash } from 'lucide-react';
import { cn } from '@/lib/utils';

  
export default function SidebarChatHistory({
  scrollClassName,
}:{
  scrollClassName : string,
}) {
  const {
    toolchainSessions,
    setToolchainSessions,
    activeToolchainSession,
    setActiveToolchainSession,
  } = useContextAction();

  const router = useRouter();
  const [internalToolchainSessions, setInternalToolchainSessions] = useState<timeWindowType[]>([]);

  useEffect(() => {

    const timeWindows : timeWindowType[] = [
			{title: "Last 24 Hours", cutoff: 24*3600, entries: []},
			{title: "Last 2 Days", cutoff: 2*24*3600, entries: []},
			{title: "Past Week", cutoff: 7*24*3600, entries: []},
			{title: "Past Month", cutoff: 30*24*3600, entries: []},
      {title: "Past Year", cutoff: 365*24*3600, entries: []},
      {title: "Older", cutoff: Infinity, entries: []}
		];


    const current_time = Math.floor(Date.now() / 1000);

    // const newToolchainSessions = new Map<string, toolchain_session>();

    toolchainSessions.forEach((session : toolchain_session) => {
      const delta_time = current_time - session.time;
      for (let i = 0; i < timeWindows.length; i++) {
        if (delta_time < timeWindows[i].cutoff) {
          timeWindows[i].entries.push(session);
        }
      }
    });

    console.log("Time Windows:", timeWindows);

    setInternalToolchainSessions(timeWindows);
  }, [toolchainSessions])


  const deleteSession = (hash_id : string) => {
    // TODO : Implement delete session with API
    
    // toolchainSessions.delete(hash_id)

    // setToolchainSessions(toolchainSessions);
    toolchainSessions.delete(hash_id);
    setToolchainSessions(toolchainSessions);
  };
  
  return (
    <div className='pb-0'>
      <div className='pb-2'>
        <Link href="/app/create">
          <Button variant={"ghost"} className="w-full flex flex-row rounded-2xl h-9 items-center justify-center">
              <div style={{paddingRight: 5}}>
                <Icon.Plus size={20}/>
              </div>
              <div style={{alignSelf: 'center', justifyContent: 'center'}}>
              <p>{"New Session"}</p>
              </div>
          </Button>
        </Link>
      </div>
      <ScrollArea className={cn("pb-0", scrollClassName)}>
        <div className='space-y-6'>
        {internalToolchainSessions.map((chat_history_window : timeWindowType, chat_history_index : number) => (
          <div key={chat_history_index} className='space-y-8'>
            {(chat_history_window.entries.length > 0) && (
              <div className='space-y-1'>
                <p className="w-full text-left text-base text-gray-700">
                  {chat_history_window.title}
                </p>
                {chat_history_window.entries.map((value : toolchain_session, index : number) => (
                  <div key={index} className='px-4 w-auto flex flex-row justify-between h-8'>
                    {/* <HoverDocumentEntry
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
                    /> */}
                    <p className='text-sm h-auto flex flex-col justify-center'>{value.title}</p>
                    <Button className='h-6 w-6 rounded-full p-0 m-0' variant={"ghost"}>
                      <Trash className='w-3.5 h-3.5 text-primary'/>
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
       </div>
      </ScrollArea>
    </div> 
  );
}