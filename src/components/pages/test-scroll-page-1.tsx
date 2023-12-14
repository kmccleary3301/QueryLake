import { useRef, useImperativeHandle} from 'react'

import '@/App.css'
// import { Button } from './components/ui/button'
// import { ThemeProvider } from "@/components/theme-provider"
// import craftUrl from '@/hooks/craftUrl'
// import { ChatInput } from '../ui/chat'
// import ScrollViewBottomStick from '../manual_components/scrollview-bottom-stick'
// import { ScrollArea } from '../ui/scroll-area'
// import { Separator } from "@/components/ui/separator"
import { ScrollArea } from '../ui/scroll-area'
// const tags = Array.from({ length: 50 }).map(
//   (_, i, a) => `v1.2.0-beta.${a.length - i}`
// )

export default function TestScrollPage1() {
	const testArray = Array(500).fill("Test Message");


  const texteAreaRef = useRef<HTMLTextAreaElement>(null)
  useImperativeHandle(texteAreaRef, () => texteAreaRef.current!);


	// return (
	// 	<div style={{height: "100%", display: 'flex', flexDirection: "column", justifyContent: "center"}}>
	// 		<div className="w-full flex flex-col flex-grow" style={{
	// 			borderWidth: 2,
	// 			borderColor: "#00FF00",
	// 			width: 200,
	// 			height: 200
	// 		}}> {/* Set parent container to 100% height */}
	// 			<div style={{
	// 				position: 'absolute',
	// 				borderWidth: 2,
	// 				borderColor: "#FF0000",
	// 				// height: "80%",
	// 				// width: "100%",
	// 				// minHeight: 20,
	// 				// minWidth: 20,
	// 				// display: "grid",
	// 				// gridArea: "1/1/2/2"
	// 				// gridTemplateAreas: "'header' 'content' 'footer'"
	// 				width: "100em"
					
	// 			}}>
	// 			</div>
	// 		</div>


	// 	</div>
	// );

	return (
		<>
		<div style={{height: "100%", display: 'flex', flexDirection: "column", justifyContent: "center"}}>
			<div className="w-full flex flex-col flex-grow" style={{
				borderWidth: 2,
				borderColor: "#00FF00",
			}}> {/* Set parent container to 100% height */}
				<div className="flex flex-col flex-grow py-4 gap-x-4 h-[calc(100vh-200px)]" style={{
					// position: 'absolute',
					borderWidth: 2,
					borderColor: "#FF0000",
					// height: "80%",
					// width: "100%",
					padding: 10,
					display: "grid",
					flexDirection: "column",
					gridArea: "1/1/2/2"
				}}>
					<ScrollArea className="h-[calc(100vh-200px)] w-full">
					<div className='css-view-175oi2r r-WebkitOverflowScrolling-150rngu r-flexDirection-eqz5dr r-flexGrow-16y2uox r-flexShrink-1wbh5a2 r-overflowX-11yh6sk r-overflowY-auto r-transform-agouwx r-scrollbarWidth-2eszeu'>
						{testArray.map((v_2 : string, k_2 : number) => (
							<p key={k_2}>
								{v_2}
							</p>
						))}
					</div>
					</ScrollArea>
				</div>
				<p>
					{"FFFFFFFF\nFFFFFFFFFFFF\nFFFFFFFFFFFF"}
				</p>
			</div>
			<p>
				{"FFFFFFFF\nFFFFFFFFFFFF\nFFFFFFFFFFFF"}
			</p>
			<p>
				{"FFFFFFFF\nFFFFFFFFFFFF\nFFFFFFFFFFFF"}
			</p>
		</div>
		</>
	);

  // return (
	// 			<div style={{height: "99vh", width: "99vw"}}>
	// 				<ScrollViewBottomStick
	// 					showsVerticalScrollIndicator={false}
	// 					animateScroll={false}
	// 				>
	// 					{testArray.map((v_2 : string, k_2 : number) => (
	// 						<p key={k_2}>
	// 							{v_2}
	// 						</p>
	// 					))}
	// 				</ScrollViewBottomStick>
	// 			</div>
  // )
}
