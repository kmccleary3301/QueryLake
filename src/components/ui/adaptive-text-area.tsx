import { useRef, useState } from "react";
import useAutosizeTextArea from "@/hooks/useAutosizeTextArea";
import { Textarea } from "@/components/ui/textarea";
import "@/App.css";
import { ScrollArea } from "./scroll-area";

type AdaptiveTextAreaProps = {
    value: string,
    setValue: React.Dispatch<React.SetStateAction<string>>,
    maxHeight?: number,
    onSubmission?: (value : string) => void,
    onUpdateHeight?: (height : number) => void
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

  return (
    <ScrollArea className="flex-grow py-4 gap-x-4 items-start">
      <div style={{padding: 2}}>
        <Textarea
          className="min-h-[30px] resize-none"
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
