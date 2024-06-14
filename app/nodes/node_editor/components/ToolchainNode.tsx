"use client";
import { Button } from '@/registry/default/ui/button';
import { Input } from '@/registry/default/ui/input';
import { feedMapping, nodeInputArgument, toolchainNode } from '@/types/toolchains';
import { ChevronRight, Plus, Settings } from 'lucide-react';
import React, { memo, ReactNode, useEffect } from 'react';
import { Handle, NodeProps, Position, XYPosition } from 'reactflow';
import AddFeedMapSheet, { ModifyFeedMapSheet } from './control_fields/AddFeedMapSheet';
// import { FiCloud } from 'react-icons/fi';

export type ToolchainNodeData = {
  id: string,
  type: string,
  data: toolchainNode,
  position: XYPosition,
}

export default memo(({ data }: NodeProps<toolchainNode>) => {
  useEffect(() => {
    console.log("Got data", data);
  }, [data]);
  
  return (
    <>
      <Handle type="target" id={"||UNCLASSIFIED||"} position={Position.Left} style={{top:0}} onContextMenu={(e) => e.preventDefault()} 
        className='w-[30px] h-[30px] -ml-1 rounded-full overflow-visible z-10'>
        <div className='h-full flex flex-col justify-center bg-none pointer-events-none text-xs text-primary'>
          <div className="cloudinput gradient">
            <div>
              
            </div>
          </div>
        </div>
      </Handle>
      {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
        <React.Fragment key={index}>
          <Handle key={index} type="target" id={input.key} position={Position.Left} style={{top:30*index + 75}} onContextMenu={(e) => e.preventDefault()} className='w-5 h-5 rounded-full border-2 border-[#e92a67] overflow-visible z-10'>
            {/* <p className='ml-6 h-4 text-nowrap text-primary text-xs flex flex-col justify-center'>{input.key}</p> */}
            <div className='ml-6 h-5 flex flex-col justify-center'>
              <Input className='pl-2 h-2 mb-1 w-20 text-xs' spellCheck={false} defaultValue={input.key}/>
            </div>
          </Handle>
        </React.Fragment>
      ))}
      {(
        <Handle 
          type="target" 
          id={"||ADD_ARG_BUTTON||"} 
          isConnectable={false} 
          position={Position.Left} 
          style={{top:30*((data.input_arguments || []).length) + 75}} 
          className='w-5 h-5 rounded-full overflow-visible z-10' 
          onContextMenu={(e) => e.preventDefault()}
        >
          <AddFeedMapSheet>
            <Button className='h-5 w-5 rounded-full p-0 m-0 pointer-events-auto border-2 border-[#2a8af6] border-dashed text-[#2a8af6] active:text-[#2a8af6]/70 active:border-[#2a8af6]/70' variant={"ghost"}>
              <Plus className='w-4 h-4'/>
            </Button>
          </AddFeedMapSheet>
        </Handle>
      )}

      {(data.feed_mappings || [] as feedMapping[]).map((feed : feedMapping, index : number) => (
        <React.Fragment key={index}>
          <Handle
            key={index} 
            type="source" 
            isConnectable={!(feed.destination === "<<STATE>>" || feed.destination === "<<USER>>")} 
            id={`feed-${index}`} 
            position={Position.Right}
            style={{
              top:30*index + 75,
              borderColor: (feed.destination === "<<STATE>>") ? 
                            '#fed734' : (feed.destination === "<<USER>>") ?
                            '#2a8af6' : 
                            '#e92a67',
            }} 
            className='w-5 h-5 rounded-full border-2 z-10'
            onContextMenu={(e) => e.preventDefault()}
            // onClick={(e) => {if (e.button === 2) e.preventDefault();}}
          >
            <ModifyFeedMapSheet data={feed} className='pointer-events-auto'>
              <button className='absolute p-0 m-0 h-full flex flex-col justify-center w-3 rounded-full -ml-5 text-primary active:text-primary/70'>
                <ChevronRight className='w-3 h-3'/>
              </button>
            </ModifyFeedMapSheet>
            <div className='h-full flex flex-col justify-center bg-none pointer-events-none text-xs text-primary'>
              <p className='w-full text-center pointer-events-none'>{(feed.destination === "<<STATE>>") ? 'S' : (feed.destination === "<<USER>>") ? 'U' : ''}</p>
            </div>
          </Handle>
        </React.Fragment>
      ))}
      <Handle 
        type="source" 
        id={"||ADD_BUTTON||"} 
        isConnectable={false} 
        position={Position.Right} 
        style={{top:30*((data.feed_mappings || []).length) + 75}} 
        className='w-5 h-5 rounded-full overflow-visible z-10' onContextMenu={(e) => e.preventDefault()}
      >
        <AddFeedMapSheet>
          <Button className='h-5 w-5 rounded-full p-0 m-0 pointer-events-auto border-2 border-[#2a8af6] border-dashed text-[#2a8af6] active:text-[#2a8af6]/70 active:border-[#2a8af6]/70' variant={"ghost"}>
            <Plus className='w-4 h-4'/>
          </Button>
        </AddFeedMapSheet>
      </Handle>
      <div className="wrapper gradient rounded-2xl bg-transparent" onContextMenu={(e) => e.preventDefault()}>
        <div className="px-4 py-2 shadow-md bg-background text-primary rounded-lg">
          <div className="flex h-[50px]">
            <div className='flex flex-row'>
              <p className='h-5 flex flex-col justify-center pr-2'>{"id: "}</p>
              <Input
                className='text-sm h-5 max-w-40'
                spellCheck={false}
                defaultValue={data.id}
              />
            </div>
          </div>
          
          <div className='flex flex-row'>
            <div className='flex flex-col w-20 mr-2'style={{height: 30*(1+(data.input_arguments || [])?.length) + 0}}>
              {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
                <React.Fragment key={index}>
                  <p className='text-nowrap text-primary/0 text-xs select-none' style={{top:30*index + 10}}>{input.key}</p>
                </React.Fragment>
              ))}
            </div>
            <div className='flex flex-row-reverse justify-start w-full' style={{height: 30*(1+(data.feed_mappings || [])?.length) + 0}}>
              {/* {(data.feed_mappings || [] as feedMapping[]).map((feed : feedMapping, index : number) => (
                <div className='absolute text-nowrap text-primary text-xs select-none' style={{top:30*index + 65}} onContextMenu={(e) => e.preventDefault()}>
                  <ModifyFeedMapSheet data={feed} className='h-5 w-5 select-none rounded-full flex flex-col justify-center bg-none text-xs text-primary translate-x-[2px] border-2 border-pink-500'>
                    <div className='h-full flex flex-col justify-center bg-none pointer-events-auto text-xs text-primary'>
                      <p className='w-full text-center pointer-events-none'>{(feed.destination === "<<STATE>>") ? 'S' : (feed.destination === "<<USER>>") ? 'U' : ''}</p>
                    </div>
                  </ModifyFeedMapSheet>
                </div>
              ))} */}
            </div>
          </div>
        </div>
      </div>
    </>
  );
});
