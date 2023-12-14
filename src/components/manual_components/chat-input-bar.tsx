import { useState, useRef, useImperativeHandle} from 'react'
import '@/App.css'
import { Button } from '@/components/ui/button'
// import { ThemeProvider } from "@/components/theme-provider"
import { PaperPlaneIcon } from '@radix-ui/react-icons'
import AdaptiveTextArea from '@/components/ui/adaptive-text-area'

type ChatBarInputProps = {
	onMessageSend?: (message: string) => void,
  handleDrop?: (event: object) => void,
  fileDropEnabled?: boolean,
  chatEnabled?: boolean,
  onHeightChange?: (height : number) => void
}

export default function ChatBarInput(props : ChatBarInputProps) {
  const [userInput, setUserInput] = useState("");

  const texteAreaRef = useRef<HTMLTextAreaElement>(null)
  useImperativeHandle(texteAreaRef, () => texteAreaRef.current!);

  return (
    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'center', paddingTop: 0 }}>
      <div style={{width: "60vw", display: 'flex', flexDirection: 'row', justifyContent: 'center'}}>
        <AdaptiveTextArea 
          value={userInput}
          setValue={setUserInput}
          onSubmission={(value : string) => {
            if (props.onMessageSend) props.onMessageSend(value);
          }}
          onUpdateHeight={props.onHeightChange}
        />
        
        <div style={{
          display: "flex", 
          height: "auto", 
          paddingLeft: 10, 
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <Button variant="outline" type="submit" size="icon" disabled={(userInput.length < 1)} onClick={()=>{
            if (props.onMessageSend) props.onMessageSend(userInput);
            setUserInput("");
          }}>
            <PaperPlaneIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
