"use client";
import { Input } from '@/registry/default/ui/input';
import { feedMapping, nodeInputArgument, toolchainNode } from '@/types/toolchains';
import React, { memo, ReactNode, useEffect } from 'react';
import { Handle, NodeProps, Position, XYPosition } from 'reactflow';
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
      <div className="cloud gradient">
        <div>
          {/* <FiCloud /> */}
        </div>
      </div>

      {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
        <React.Fragment key={index}>
          <Handle key={index} type="target" id={input.key} position={Position.Left} style={{top:30*index + 75}} className='w-5 h-5 rounded-full border-2 border-[#e92a67] overflow-visible z-10'>
            {/* <p className='ml-6 h-4 text-nowrap text-primary text-xs flex flex-col justify-center'>{input.key}</p> */}
            <div className='ml-6 h-5 flex flex-col justify-center'>
              <Input className='pl-2 h-2 mb-1 w-20 text-xs' spellCheck={false} defaultValue={input.key}/>
            </div>
          </Handle>
        </React.Fragment>
      ))}
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
          >
            <div className='h-full flex flex-col justify-center bg-none pointer-events-none text-xs text-primary'>
              <p className='w-full text-center'>{(feed.destination === "<<STATE>>") ? 'S' : (feed.destination === "<<USER>>") ? 'U' : ''}</p>
            </div>
          </Handle>
        </React.Fragment>
      ))}
      <div className="wrapper gradient">
        <div className="px-4 py-2 shadow-md rounded-lg bg-background text-primary">
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
            <div className='flex flex-col w-20 mr-2'style={{height: 30*(data.input_arguments || [])?.length - 0}}>
              {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
                <React.Fragment key={index}>
                  <p className='text-nowrap text-primary/0 text-xs select-none' style={{top:30*index + 10}}>{input.key}</p>
                </React.Fragment>
              ))}
            </div>
            {/* <div className='h-auto bg-green-500'>
              <p className='text-nowrap'>{"Hello there. How are you?"}</p>
            </div> */}
            <div className='flex flex-row justify-start w-full' style={{height: 30*(data.feed_mappings || [])?.length - 0}}>
              
            </div>
          </div>
          {/* <Handle type="source" id={`feed-default-default`}position={Position.Right}className='h-4 w-2 !bg-teal-500'/> */}
        </div>
      </div>
    </>
  );
});
