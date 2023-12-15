import { useRef} from 'react'
import '@/App.css'
import { Button } from '@/components/ui/button'
import { ThemeProvider } from "@/components/theme-provider"
import { Label } from '../ui/label'

export default function TestWebSockets() {
	const ws = useRef<WebSocket | null>(null);

	const connect = () => {
		ws.current = new WebSocket('ws://localhost:5000/ws');
	
		ws.current.onopen = () => {
			console.log('ws opened');
			ws.current?.send("hello from client");
		};
	
		ws.current.onclose = () => {
			console.log('ws closed');
		};
	
		ws.current.onerror = (error) => {
			console.log('ws error', error);
		};
	
		ws.current.onmessage = (msg) => {
			console.log('ws message', msg);
		};
	};

  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <>
				<Button variant="outline" onClick={connect}>
					<Label>
						{"Attempt Web Socket Connection"}
					</Label>
				</Button>
        
      </>
    </ThemeProvider>
  )
}
