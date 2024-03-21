"use client";

import { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react";
import * as Icon from 'react-feather';
import ScrollViewBottomStickInner from "./scrollview-bottom-stick-inner";
import { Button } from "@/registry/default/ui/button";
import useResizeObserver from '@react-hook/resize-observer';
import { ScrollBar } from "@/registry/default/ui/scroll-area";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area"
import { cn } from "@/lib/utils";


type TestScrollSectionProps = {
	children: React.ReactNode,
}


const useSize = (target : React.RefObject<HTMLDivElement>) => {
  const [size, setSize] = useState<DOMRect>()

  useLayoutEffect(() => {
		if (target.current !== null) {
			setSize(target.current.getBoundingClientRect())
		}
  }, [target])

  // Where the magic happens
  useResizeObserver(target, (entry) => setSize(entry.contentRect))
  return size
}

export default function ScrollSection({ 
	children,
	scrollToBottomButton = false,
	scrollBar = true,
	className = "",
} : { 
	children: React.ReactNode,
	scrollToBottomButton?: boolean,
	scrollBar?: boolean,
	className?: string
}) {

	const [animateScroll, setAnimateScroll] = useState(false);
	const scrollDiv = useRef<HTMLDivElement>(null);
	const oldScrollValue = useRef(0);
  const oldScrollHeight = useRef(0);
	// const [chatBarHeightString, setChatBarHeightString] = useState(40);
	const observer = useRef<ResizeObserver>();	
	

	const interiorDiv = useRef<HTMLDivElement>(null);
	const interiorDivSize = useSize(interiorDiv);

	const [smoothScroll, setSmoothScroll]	= useState(false);
	
	const scrollToBottomHook = useCallback(() => {
		if (scrollDiv.current !== null) {
			scrollDiv.current.scrollTo({
				top: scrollDiv.current.scrollHeight,
        behavior: (smoothScroll)?"smooth":"instant"
      });
    }
  }, [smoothScroll]);
	
	useEffect(() => {
		setTimeout(() => { setSmoothScroll(true); }, 1000)
	}, []);

	useEffect(() => {
		// console.log("Resize monitor triggered");
		if (animateScroll) {
			scrollToBottomHook();
		}
	}, [interiorDivSize, animateScroll, scrollToBottomHook]);

	useEffect(() => {
		const div = interiorDiv.current;
		if (!div) return;
		
		if (animateScroll) {
			observer.current = new ResizeObserver(() => {
				if (animateScroll) {
					scrollToBottomHook();
				}
			});
		} else if (observer.current) {
			observer.current.unobserve(div)
		}
	}, [animateScroll, scrollToBottomHook]);


	// OLD VERSION ; Worked well, but it used default scrollbar and the Chrome scrollbar is ugly.
  // return (
	// 	<div className="scrollbar-custom mr-1 h-full w-[100%] overflow-y-auto"
	// 	ref={scrollDiv}
	// 	onChange={() => {
	// 		if (animateScroll) {
	// 			scrollToBottomHook();
	// 		}
	// 	}}
	// 	onScroll={(e) => {
	// 		if (animateScroll && e.currentTarget.scrollTop < oldScrollValue.current - 3 && e.currentTarget.scrollHeight === oldScrollHeight.current) {
	// 			// console.log("Unlocking");
	// 			setAnimateScroll(false);
	// 		} else if (!animateScroll && Math.abs( e.currentTarget.scrollHeight - (e.currentTarget.scrollTop + e.currentTarget.clientHeight)) < 5) {
	// 			// console.log("Locking Scroll");
	// 			scrollToBottomHook();
	// 			setAnimateScroll(true);
	// 		}
	// 		oldScrollValue.current = e.currentTarget.scrollTop;
	// 		oldScrollHeight.current = e.currentTarget.scrollHeight;
	// 	}}>
	// 		<ScrollViewBottomStickInner bottomMargin={0}>
	// 			<div className="flex flex-col" ref={interiorDiv}>
	// 					{props.children}
	// 			</div>
	// 		</ScrollViewBottomStickInner>
	// 		<div id="InputBox" className="flex flex-row justify-center h-0 pb-0">
	// 			<div className="absolute h-0 flex flex-grow flex-col justify-end">
	// 				<div className="bg-none flex flex-col justify-around pt-[10px] pb-0">
	// 					<div id="scrollButton" className="bg-transparent flex flex-row justify-end pb-[10px]">
	// 						{(animateScroll === false) && (

	// 							<Button onClick={() => {
	// 								// setAnimateScroll(true);
	// 								if (scrollDiv.current !== null) {
	// 									setAnimateScroll(true);
	// 								}
	// 							}} className="rounded-full bg-gray-800 z-5 p-0 w-10 h-10 items-center" variant={"secondary"}>
	// 								<Icon.ChevronDown className="text-white w-[50%] h-[50%]" />
	// 							</Button>
	// 						)}
	// 					</div>
	// 				</div>
	// 			</div> 
	// 		</div>
	// 	</div>
  // );

	return (
		<>
			<ScrollAreaPrimitive.Root
				className={cn("h-full w-full overflow-y-auto", className)}
			>
				<ScrollAreaPrimitive.Viewport
					ref={scrollDiv}
					id="scrollAreaPrimitive1" 
					className="h-full w-full rounded-[inherit]"
					onChange={() => {
						// console.log("Change called")
						if (animateScroll && scrollToBottomButton) {
							scrollToBottomHook();
						}
					}}
					onScroll={(e) => {
						if (animateScroll && e.currentTarget.scrollTop < oldScrollValue.current - 3 && e.currentTarget.scrollHeight === oldScrollHeight.current) {
							// console.log("Unlocking");
							setAnimateScroll(false);
						} else if (!animateScroll && Math.abs( e.currentTarget.scrollHeight - (e.currentTarget.scrollTop + e.currentTarget.clientHeight)) < 5) {
							// console.log("Locking Scroll");
							scrollToBottomHook();
							setAnimateScroll(true);
						}
						oldScrollValue.current = e.currentTarget.scrollTop;
						oldScrollHeight.current = e.currentTarget.scrollHeight;
					}}
				>
					<ScrollAreaPrimitive.Viewport id="scrollAreaPrimitive2" className="flex flex-col" ref={interiorDiv}>
						<div className="flex flex-row w-full justify-center">
							<div className="flex flex-col">
								{children}
							</div>
						</div>
					</ScrollAreaPrimitive.Viewport>
				</ScrollAreaPrimitive.Viewport>
				{/* <div className="w-full h-[20px] bg-purple-500"/> */}
				{scrollToBottomButton && (
					<div id="InputBox" className="flex flex-row justify-center h-0 pb-0">
						<div className="absolute h-0 flex flex-grow flex-col justify-end">
							<div className="bg-none flex flex-col justify-around pt-[10px] pb-0">
								<div id="scrollButton" className="bg-transparent flex flex-row justify-end pb-[10px]">
									{(animateScroll === false) && (
										<Button onClick={() => {
											// setAnimateScroll(true);
											if (scrollDiv.current !== null) {
												setAnimateScroll(true);
											}
										}} className="rounded-full z-5 p-0 w-10 h-10 items-center" variant={"secondary"}>
											<Icon.ChevronDown className="text-white w-[50%] h-[50%]" />
										</Button>
									)}
								</div>
							</div>
						</div> 
					</div>
				)}
				<ScrollBar className={`opacity-${scrollBar?"100":"0"}`}/>
    		{/* <ScrollAreaPrimitive.Corner /> */}
			</ScrollAreaPrimitive.Root>
		</>
  );
}
