import { useEffect } from 'react'
import { motion, useAnimation} from "framer-motion";

import '@/App.css'
// import { Button } from './components/ui/button'
// import { ThemeProvider } from "@/components/theme-provider"
// import craftUrl from '@/hooks/craftUrl'
// import { ChatInput } from '../ui/chat'
// import ScrollViewBottomStick from '../manual_components/scrollview-bottom-stick'
// import { ScrollArea } from '../ui/scroll-area'
// import { Separator } from "@/components/ui/separator"
// import { ScrollArea } from '../ui/scroll-area'
// const tags = Array.from({ length: 50 }).map(
//   (_, i, a) => `v1.2.0-beta.${a.length - i}`
// )

export default function TestFramerAnimation() {


  // const texteAreaRef = useRef<HTMLTextAreaElement>(null)
  // useImperativeHandle(texteAreaRef, () => texteAreaRef.current!);

	const controls = useAnimation()
  
	useEffect(() => {

		controls.set({ opacity: 1, width: 400})
	
		// With variants
		// controls.set("hidden")
	
		controls.start("variantLabel")
		controls.start({
			opacity: 0,
			width: 200,
			transition: { duration: 10 }
		})
	}, [controls]);

  return (
		<>
			<motion.div animate={controls} >
				<div style={{
					width: "100%"
				}}>
					<div style={{
						width: 400,
						height: 400,
						overflow: "clip",
						backgroundColor: "#FF0000",
					}}>

					</div>
				</div>
			</motion.div>
		</>
	);

}
