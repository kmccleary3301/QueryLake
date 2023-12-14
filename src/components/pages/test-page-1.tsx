import { useState, useRef, useImperativeHandle} from 'react'
import reactLogo from '@/assets/react.svg'
import viteLogo from '/vite.svg'
import '@/App.css'
// import { Button } from './components/ui/button'
import { Button } from '@/components/ui/button'
import { ThemeProvider } from "@/components/theme-provider"
import craftUrl from '@/hooks/craftUrl'
// import { ChatInput } from '../ui/chat'
// import { Input } from "@/components/ui/input"

import { PaperPlaneIcon } from '@radix-ui/react-icons'
// import { Textarea } from '../ui/textarea'
import AdaptiveTextArea from '@/components/ui/adaptive-text-area'
// import { ScrollArea } from '../ui/scroll-area'
// import { Separator } from "@/components/ui/separator"

// const tags = Array.from({ length: 50 }).map(
//   (_, i, a) => `v1.2.0-beta.${a.length - i}`
// )

export default function TestPage1() {
  const [userInput, setUserInput] = useState("");

  const [count, setCount] = useState(0);


  const attempt_login = () => {
    const url = craftUrl("http://localhost:5000/api/login", {
      "username": "w",
      "password": "w"
    });

    fetch(url, {method: "POST"}).then((response) => {
      console.log("Fetching");
      console.log(response);
      response.json().then((data) => {
        console.log("Got data:", data);
      });
    });
  }

  const texteAreaRef = useRef<HTMLTextAreaElement>(null)
  useImperativeHandle(texteAreaRef, () => texteAreaRef.current!);


  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <>
        <div>
          <a href="https://vitejs.dev" target="_blank">
            <img src={viteLogo} className="logo" alt="Vite logo" />
          </a>
          <a href="https://react.dev" target="_blank">
            <img src={reactLogo} className="logo react" alt="React logo" />
          </a>
        </div>
        <h1>Vite + React</h1>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
          <p>
            Edit <code>src/App.tsx</code> and save to test HMR
          </p>
        </div>
        <p className="read-the-docs">
          Click on the Vite and React logos to learn more
        </p>
        <Button variant="outline" onClick={() => {console.log("Button clicked"); attempt_login();}}>
          <p>
            {"This is a fucking button!"}
          </p>
        </Button>
        <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'center', paddingTop: 0 }}>
          <div style={{width: "60vw", display: 'flex', flexDirection: 'row', justifyContent: 'center'}}>
            <AdaptiveTextArea 
              value={userInput}
              setValue={setUserInput}
            />
            
            <div style={{
              display: "flex", 
              height: "auto", 
              paddingLeft: 10, 
              flexDirection: 'column',
              justifyContent: 'center'
            }}>
              <Button variant="outline" type="submit" size="icon">
                <PaperPlaneIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </>
    </ThemeProvider>
  )
}
