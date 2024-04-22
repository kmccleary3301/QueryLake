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


function SessionEntry({
  session,
  selected = false,
  onDelete = () => {},
}:{
  session: toolchain_session,
  selected?: boolean,
  onDelete?: () => void,
}) {
  return (
    <>
      {selected ? (
        <div className={cn(
          "bg-secondary text-secondary-foreground hover:bg-accent active:bg-secondary/60",
          'p-0 w-full flex flex-row-reverse justify-between h-8 rounded-lg'
        )}>
          <div className='w-full text-left flex flex-col justify-center rounded-[inherit]'>
            <p className='relative px-2 overflow-hidden text-sm whitespace-nowrap'>{session.title}</p>
          </div>
          <div className='h-8 absolute flex flex-col justify-center bg-accent opacity-0 hover:opacity-100 rounded-r-[inherit]'>
            <div className='h-auto flex flex-row pointer-events-none'>
              <Button className='h-6 w-6 rounded-full p-0 m-0' variant={"ghost"} onClick={onDelete}>
                <Trash className='w-3.5 h-3.5 text-primary'/>
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className={cn(
          "hover:bg-accent active:bg-accent/70 hover:text-accent-foreground hover:text-accent-foreground/",
          'p-0 w-full flex flex-row-reverse justify-between h-8 rounded-lg'
        )}>
          <Link href={`/app/session?s=${session.id}`} className='w-full flex flex-col justify-center rounded-[inherit]'>
            <p className='relative px-2 overflow-hidden overflow-ellipsis text-sm whitespace-nowrap'>{session.title}</p>
          </Link>
          <div className='h-8 absolute flex flex-col justify-center bg-accent opacity-0 hover:opacity-100 rounded-r-[inherit]'>
            <div className='h-auto flex flex-row pointer-events-none'>
              <Button className='h-6 w-6 rounded-full p-0 m-0' variant={"ghost"} onClick={onDelete}>
                <Trash className='w-3.5 h-3.5 text-primary'/>
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


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
          break;
        }
      }
    });

    for (let i = 0; i < timeWindows.length; i++) {
      timeWindows[i].entries.sort((a : toolchain_session, b : toolchain_session) => (b.time - a.time));
    }

    console.log("Time Windows:", timeWindows);

    setInternalToolchainSessions(timeWindows);
  }, [toolchainSessions])


  const deleteSession = (hash_id : string) => {
    // TODO : Implement delete session with API
    
    // setToolchainSessions(toolchainSessions);
    // toolchainSessions.delete(hash_id);
    setToolchainSessions((prevSessions) => {
      // Create a new Map from the previous one
      const newMap = new Map(prevSessions);
      // Update the new Map
      newMap.delete(hash_id);
      // Return the new Map to update the state
      return newMap;
    });
    // setToolchainSessions(toolchainSessions.filter((session : toolchain_session) => (session.id !== hash_id)));
  };
  
  return (
    <div className='pb-0 overflow-hidden'>
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
      <ScrollArea className={cn("pb-0 -mr-4", scrollClassName)}>
        <div className='space-y-6 pr-4'>
        {internalToolchainSessions.map((chat_history_window : timeWindowType, chat_history_index : number) => (
          <div key={chat_history_index} className='space-y-8'>
            {(chat_history_window.entries.length > 0) && (
              <div className='space-y-1 w-[280px]'>
                <p className="w-full text-left text-sm text-primary/80">
                  {chat_history_window.title}
                </p>
                {chat_history_window.entries.map((value : toolchain_session, index : number) => (
                  <SessionEntry key={index} session={value} selected={(value.id === activeToolchainSession)}/>
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