import { useRef, useState, useCallback, useEffect } from "react";
import useAutosizeTextArea from "@/hooks/useAutosizeTextArea";
import { Textarea } from "@/components/ui/textarea";
import "@/App.css";
import { ScrollArea } from "./scroll-area";
// import { DragEventHandler } from "react";
import {useDropzone} from 'react-dropzone';

// type FileDropEvent = React.DragEvent<HTMLDivElement>;

type AdaptiveTextAreaProps = {
    value: string,
    setValue: React.Dispatch<React.SetStateAction<string>>,
    maxHeight?: number,
    onSubmission?: (value : string) => void,
    onUpdateHeight?: (height : number) => void
    onDrop?: (files : File[]) => void,
}


export default function AdaptiveTextArea(props : AdaptiveTextAreaProps) {
//   const [value, setValue] = useState("");
  const textAreaRef = useRef<HTMLTextAreaElement>(null);
  const [preventUpdate, setPreventUpdate] = useState(false);

  useAutosizeTextArea(textAreaRef.current, props.value, 200, props.onUpdateHeight);

  const handleChange = (evt: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = evt.target?.value;
    if (!preventUpdate) {
      props.setValue(val);
    }
    setPreventUpdate(false);
  };

  const onKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!event.shiftKey && event.key === "Enter" && props.value.length > 0) {
      props.onSubmission?props.onSubmission(props.value):null;
      setPreventUpdate(true);
      props.setValue("");
      // setTimeout(() => {}, 20);
    }
  };

  

  const [dragging, setDragging] = useState(false);

  const handleDragEnter = () => {
    // event.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    // event.preventDefault();
    setDragging(false);
  };

  
  const onDrop = useCallback((acceptedFiles: File[]) => {
    console.log("DROP CALLED DROP CALLED", acceptedFiles);
    if (props.onDrop) {
      props.onDrop(acceptedFiles);
    }
  }, [props]);

  const {getRootProps} = useDropzone({onDrop});

  useEffect(() => {
    console.log("dragging:", dragging);
  }, [dragging]);

  return (
    <ScrollArea className={"flex-grow py-4 gap-x-4 items-start"}>
      <div 
        className={((dragging === true) && props.onDrop)?'hover:outline-[#FF0000]':''}
        {...getRootProps()} 
        style={{padding: 2}}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
      >
        <Textarea
          
          // onDrop={handleDrop}
          // onDragOver={handleDragOver}
          className={"min-h-[30px] resize-none bg-secondary"}
          id="review-text"
          onChange={handleChange}
          placeholder="Ask Anything"
          ref={textAreaRef}
          rows={1}
          value={props.value}
          spellCheck={false}
          style={{overflow: "hidden", fontSize: 18, lineHeight: 1.4}}
          onKeyDown={onKeyDown}
          // hid
        />
      </div>
    </ScrollArea>
  );
}
