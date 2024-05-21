"use client";
import { feedMapping, nodeInputArgument, toolchainNode } from '@/types/toolchains';
import React, { memo } from 'react';
import { Handle, Position, XYPosition } from 'reactflow';

export type ToolchainNodeData = {
  id: string,
  type: string,
  data: toolchainNode,
  position: XYPosition,
}

function ToolchainNodeReactFlowPrimitive({ data }:{
  data: toolchainNode
}) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400 text-black">
      <div className="flex h-[50px] bg-teal-500">
        <div className="rounded-full w-12 h-12 flex justify-center items-center bg-gray-100"/>
        <p>{data.id}</p>
        <div className="ml-2">
          {/* <div className="text-lg font-bold">{data.id}</div> */}
          {/* <div className="text-gray-500">{data.id}</div> */}
        </div>
      </div>
      
      <div className='flex flex-row'>
        <div className='flex flex-col bg-red-500'>
          {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
            <React.Fragment key={index}>
              <p className='ml-2 text-nowrap text-black/0 select-none' style={{top:30*index + 10}}>{input.key}</p>
              <Handle key={index} type="target" id={input.key} position={Position.Left} style={{top:30*index + 75}} className='w-2 mb-2 !bg-teal-500'>
                <p className='ml-2 h-4 text-nowrap text-black flex flex-col justify-center '>{input.key}</p>
              </Handle>
            </React.Fragment>
          ))}
        </div>
        <div className='h-auto w-20 bg-green-500'>

        </div>
        <div className='flex flex-row justify-start w-full'>
          <div className='flex flex-col bg-red-500'>
            <div style={{height: 30*(data.input_arguments || [])?.length - 0, width: 40}}/>
            {(data.feed_mappings || [] as feedMapping[]).map((feed : feedMapping, index : number) => (
              <React.Fragment key={index}>
                {/* <p className='ml-2 h-4 text-nowrap text-black/0 select-none' style={{top:30*index + 75}}>{input.key}</p> */}
                <Handle key={index} type="source" id={`feed-${index}`} position={Position.Right} style={{top:30*index + 75}} className='h-4 w-2 !bg-teal-500 justify-between'>
                  <div className='flex flex-row justify-end bg-none'>
                    <p className='h-4 text-nowrap flex flex-col justify-center text-right pr-3 pl-3'>{feed.destination}</p>
                    {/* <div className='h-4 w-1 !bg-teal-500'/> */}
                  </div>
                </Handle>
              </React.Fragment>
            ))}
            {/* <div className='bg-pink-500 w-10 h-10'></div> */}
            <div className='bg-pink-500 w-10 h-10'></div>
          </div>
        </div>
      </div>
    </div>
    // <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400 text-black">
    //   <div className="flex">
    //     {/* <div className="rounded-full w-12 h-12 flex justify-center items-center bg-gray-100">
    //       {data.emoji}
    //     </div>
    //     <div className="ml-2">
    //       <div className="text-lg font-bold">{data.name}</div>
    //       <div className="text-gray-500">{data.job}</div>
    //     </div> */}


    //   {data.input_arguments?.map((input : nodeInputArgument, index : number) => (
    //     <Handle key={index} type="target" position={Position.Left} className="px-2 py-2 !bg-teal-500">
    //       <p>{input.key}</p>
    //     </Handle>
    //   ))}

    //   {/* <Handle type="source" position={Position.Right} className="w-2 h-2 !bg-teal-500" /> */}
    //   </div>
    // </div>
  );
}

function CustomNode({ data }:{
  data:{
    emoji: string,
    name: string,
    job: string
  }
}) {
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400 text-black">
      <div className="flex">
        <div className="rounded-full w-12 h-12 flex justify-center items-center bg-gray-100">
          {data.emoji}
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold">{data.name}</div>
          <div className="text-gray-500">{data.job}</div>
        </div>
      </div>

      <Handle type="target" position={Position.Left} className="w-2 h-2 !bg-teal-500" />
      <Handle type="source" position={Position.Right} className="w-2 h-2 !bg-teal-500" />
    </div>
  );
}

export const ToolchainNodeReactFlow = memo(ToolchainNodeReactFlowPrimitive);

export default memo(CustomNode);