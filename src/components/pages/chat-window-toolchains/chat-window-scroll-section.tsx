import { useState, useRef } from "react";
import * as Icon from 'react-feather';
import ChatBubble from "../../manual_components/chat-bubble";
import AnimatedPressable from "../../manual_components/animated-pressable";
import ScrollViewBottomStickInner from "../../manual_components/scrollable-bottom-stick/scrollview-bottom-stick-inner";

import { 
	sourceMetadata, 
	ChatEntry, 
	// selectedCollectionsType, 
	userDataType,
	buttonCallback,
} from "@/globalTypes";
// import { Loader2 } from 'lucide-react';
import ChatBarInput from "../../manual_components/chat-input-bar";
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import ClipLoader from "react-spinners/ClipLoader";
import { test_message_display } from "@/assets/test_message_display";
// import { create } from "domain";

import { Button } from "../../ui/button";
// import { set } from "react-hook-form";

type ChatWindowToolchainScrollSectionProps = {
  userData: userDataType,
	// scrollDiv: React.RefObject<HTMLDivElement>,
	animateScroll: boolean,
	setAnimateScroll: React.Dispatch<React.SetStateAction<boolean>>,
	onMessageSend: (message: string) => void,
	buttonCallbacks: buttonCallback[],
	displayChat: ChatEntry[],
	eventActive: string | undefined,
	testEventCall: (event_node_id: string, event_parameters: object, file_response: boolean) => void,
	setUploadFiles: React.Dispatch<React.SetStateAction<File[]>>,
	entryFired: boolean,
}

export default function ChatWindowToolchainScrollSection(props : ChatWindowToolchainScrollSectionProps) {

	
	const scrollDiv = useRef<HTMLDivElement>(null);
	const oldScrollValue = useRef(0);
  const oldScrollHeight = useRef(0);
	const [chatBarHeightString, setChatBarHeightString] = useState(40);
	
	const scrollToBottomHook = () => {
    if (scrollDiv.current !== null) {
      scrollDiv.current.scrollTo({
        top: scrollDiv.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  return (
		<div className="scrollbar-custom mr-1 h-full overflow-y-auto" style={{
			// margin: 1,
			width: "100%",
			// height: "full",
			overflowY: "auto",
		}} 
		ref={scrollDiv}
		onChange={() => {
			if (props.animateScroll) {
				scrollToBottomHook();
			}
		}}
		onScroll={(e) => {
			if (props.animateScroll && e.currentTarget.scrollTop < oldScrollValue.current - 3 && e.currentTarget.scrollHeight === oldScrollHeight.current) {
				props.setAnimateScroll(false);
			} else if (props.animateScroll) {
				scrollToBottomHook();
			} else if (!props.animateScroll && Math.abs( e.currentTarget.scrollHeight - (e.currentTarget.scrollTop + e.currentTarget.clientHeight)) < 5) {
				// setAnimateScroll(true);
				scrollToBottomHook();
				props.setAnimateScroll(true);
			}
			// scrollValue.current.scrollIntoView() = 0;
			// if (!animateScroll && Math.abs( e.currentTarget.scrollHeight - (e.currentTarget.scrollTop + e.currentTarget.clientHeight)) < 5) {
			//   setAnimateScroll(true);
			// }
			if (props.animateScroll) {
				scrollToBottomHook();
			}
			oldScrollValue.current = e.currentTarget.scrollTop;
			oldScrollHeight.current = e.currentTarget.scrollHeight;
			// console.log("onScroll main window: ", e.currentTarget.scrollTop, e.currentTarget.scrollHeight, e.currentTarget.clientHeight);
		}}>
			<ScrollViewBottomStickInner bottomMargin={chatBarHeightString+70}>
				<div style={{
					width: "60vw",
					flexDirection: "column",
					justifyContent: "center"
				}}>
					{(props.displayChat !== undefined) && (
						// <ScrollViewBottomStick
						// 	height_string=""
						// 	animateScroll={false}
						//   // showsVerticalScrollIndicator={false}
						//   // animateScroll={animateScroll}
						// >
						<>
							<ChatBubble
								displayCharacter={props.userData.username[0]}
								state={"finished"}
								role={"assistant"} 
								input={test_message_display}
								userData={props.userData}
								sources={[]}
							/>
							{props.displayChat.map((v_2 : ChatEntry, k_2 : number) => (
									
								<div key={k_2}>
									
									{(v_2 !== undefined) && (
										<ChatBubble
											displayCharacter={props.userData.username[0]}
											state={(v_2.state)?v_2.state:"finished"}
											key={k_2}
											role={v_2.role} 
											input={v_2.content}
											userData={props.userData}
											sources={(v_2.sources)?v_2.sources.map((value : sourceMetadata) => ({document: value.metadata.document, metadata: value})):[]}
										/>
									)}
								</div>
							))}
							{(props.eventActive !== undefined) && (
								<div style={{width: "100%", flexDirection: "row", justifyContent: "center", paddingTop: 10, paddingBottom: 10}}>
									<div style={{display: "flex", flexDirection: "row", justifyContent: "center"}}>
										{/* <ActivityIndicator size={20} color="#E8E3E3"/> */}
										<ClipLoader size={20} color="#E8E3E3"/>
										<p style={{
											// fontFamily: 'Inter-Regular',
											color: "#E8E3E3",
											fontSize: 16,
											paddingLeft: 10,
											paddingRight: 10,
										}}>
											{"Running node: "+props.eventActive}
										</p>
									</div>
								</div>
							)}
							{(props.buttonCallbacks.length > 0 && props.eventActive === undefined && props.entryFired) && (
								<div style={{width: "100%", display: "flex", flexDirection: "row", justifyContent: "center"}}>
									<div style={{maxWidth: "100%", display: "flex", flexDirection: "row", flexWrap: "wrap"}}>
									{props.buttonCallbacks.map((v_2 : buttonCallback, k_2 : number) => (
										<div style={{padding: 10}} key={k_2}>
											<AnimatedPressable style={{
												borderRadius: 10,
												borderColor: "#E8E3E3",
												borderWidth: 2,
												flexDirection: "row" 
											}} onPress={() => {
												props.testEventCall(v_2.input_argument, {}, (v_2.return_file_response)?v_2.return_file_response:false)
												// testEventCall()
											}}>
												<div style={{padding: 10, display: "flex", flexDirection: "row", justifyContent: "center"}}>
													<Icon.Download size={16} color="#E8E3E3" />
													<p style={{
														// fontFamily: 'Inter-Regular',
														color: "#E8E3E3",
														fontSize: 16,
														paddingLeft: 10,
														paddingRight: 10,
													}}>
														{v_2.button_text}
													</p>
												</div>
											</AnimatedPressable>
										</div>
									))}
									</div>
								</div>
							)}
							
						</>
					)}
				</div>
			</ScrollViewBottomStickInner>
			
			<div id="InputBox" style={{
				display: "flex",
				flexDirection: 'row',
				justifyContent: 'center',
				height: 0,
				paddingBottom: 0,
			}}>
				<div style={{
					position: "absolute",
					height: 0,
					display: "flex",
					flexGrow: 1,
					flexDirection: 'column',
					justifyContent: "flex-end",
				}}>
					<div className="bg-none" style={{
						display: "flex",
						flexDirection: 'column',
						justifyContent: 'space-around',
						paddingTop: 10,
						paddingBottom: 0,
					}}>
						<div id="scrollButton" style={{
							backgroundColor: "#23232D00",
							display: "flex",
							flexDirection: "row",
							justifyContent: "flex-end",
							paddingBottom: 10,
							paddingRight: 50,
							// height: 0,
							// position: "absolute",
							transform: "translateX(140px)"
						}}>
							{(props.animateScroll === false) && (

								<Button onClick={() => {
									props.setAnimateScroll(true);
									if (scrollDiv.current !== null) {
										scrollDiv.current.scrollTo({
											top: scrollDiv.current.scrollHeight,
											behavior: 'smooth'
										});
									}
								}} style={{
									borderRadius: "50%",
									backgroundColor: "#23232D",
									zIndex: 5,
									padding: 0,
									width: 40,
									height: 40,
								}}>
									<Icon.ChevronDown size={24} color="#E8E3E3" />
								</Button>
							)}
						</div>
						<div className="bg-background" style={{
							paddingTop: 6,
							width: "100%",
							display: "flex",
							flexDirection: 'row',
							justifyContent: 'center',
						}}>
							<div style={{
								display: "flex",
								flexDirection: 'column',
								width: "60vw"
							}}>
								<div style={{
									paddingBottom: 0, 
									paddingLeft: 12, 
									display: "flex", 
									flexDirection: "row", 
									width: "100%",
								}}>
									<div id="Switch" style={{
										height: 28,
										borderRadius: 14,
										display: "flex",
										borderWidth: 1,
										borderColor: '#4D4D56',
										flexDirection: 'row',
										justifyContent: 'center',
										alignItems: 'center',
									}}>
										<div style={{paddingLeft: 10, paddingRight: 10}}>
											<div className="flex items-center space-x-2">
												<Switch id="airplane-mode" />
												<Label htmlFor="airplane-mode">Search Web</Label>
											</div>
										</div>
									</div>
									<div style={{display: "flex", flex: 1}}>

									</div>
								</div>
								<ChatBarInput
									onMessageSend={props.onMessageSend}
									handleDrop={(files: File[]) => {
										props.setUploadFiles(files);
									}}
									onHeightChange={(height : number) => { 
										// setChatBarHeight(height); 
										setChatBarHeightString(height);
									}}
									// handleDrop={handleDrop}
								/>
							</div>
						</div>
					</div>
				</div> 
			</div>
		</div>
  );
}
