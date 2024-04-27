"use client";
import { FC, CSSProperties } from 'react';
import { Handle, Position, NodeProps, NodeResizer } from 'reactflow';
import SonnerDemo from '@/registry/default/example/sonner-demo';
import PopoverDemo from '@/registry/default/example/popover-demo';


const sourceHandleStyleA: CSSProperties = { top: 50 };
const sourceHandleStyleB: CSSProperties = {
  bottom: 50,
  top: 'auto',
};

const CustomNode: FC<NodeProps> = ({ data, xPos, yPos }) => {
  return (
    <>
      <NodeResizer />
      <Handle type="target" position={Position.Left} />
      <div>
        <div>
          Label: <strong>{data.label}</strong>
        </div>
        <div>
          Position:{' '}
          <strong>
            {xPos.toFixed(2)},{yPos.toFixed(2)}
          </strong>
        </div>
      </div>
      <div style={{
        width: 100,
        height: 100,
        backgroundColor: 'red',
      }}>
        <SonnerDemo />
        <PopoverDemo />
      </div>

      <Handle
        type="source"
        position={Position.Right}
        id="a"
        style={sourceHandleStyleA}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="b"
        style={sourceHandleStyleB}
      />
    </>
  );
};

export default CustomNode;