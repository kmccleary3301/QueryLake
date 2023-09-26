import { useState, useRef, useEffect } from 'react';
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from 'expo-font';
import {
  View,
  Text,
  Pressable,
  TextInput,
  StatusBar
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { ScrollView } from 'react-native-gesture-handler';
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
import EventSource from '../react-native-server-sent-events';
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";

export default function ChatWindowWeb({ navigation }) {
	const scrollViewRef = useRef();
	const inputTwo = useRef("");
	const [inputText, setInputText] = useState('');
	const [chat, setChat] = useState("Sample Text");
	const [sseOpened, setSseOpened] = useState(false);
	const [fileDragHover, setFileDragHover] = useState(false);
	const [filesPrepared, setFilesPrepared] = useState<File[]>([]);
	const [filesProgress, setFilesProgress] = useState<Number[]>([]);
	const [submitInput, setSubmitInput] = useState(false);

	useFonts({
		'YingHei': require('../../assets/fonts/MYingHeiHK-W4.otf'),
	});

	let genString = "";
	let termLet: string[] = [];


	const sse_fetch = async function() {
		if (sseOpened === true) {
			return;
		}
		console.log("Starting SSE")

		const url = new URL("http://localhost:5000/chat");
		url.searchParams.append("query", inputText);

		// setInputText("");

		console.log(url.toString());
		const es = new EventSource(url, {
			method: "GET"
		});

		es.addEventListener("open", (event) => {
			console.log("Open SSE connection.");
			setSseOpened(true);
		});

		es.addEventListener("message", (event) => {
			// console.log("New message event:", event);
			if (event === undefined || event.data === undefined)
				return;
			let decoded = event.data.toString();
			if (decoded == '-DONE-') {
				es.close()
			} else {
				// for (let key in Object.keys(uri_decode_map)) {
				//   decoded = decoded.replace(key, uri_decode_map[key]);
				// }
				decoded = decodeURI(decoded);
				console.log([decoded]);
				genString += decoded;
			}

			setChat(genString);
			// setLog(chat+" HELLOOOOOOOOOOOO"+chat+chat);
		});

		es.addEventListener("error", (event) => {
			if (event.type === "error") {
				console.error("Connection error:", event.message);
			} else if (event.type === "exception") {
				console.error("Error:", event.message, event.error);
			}
		});
		
		es.addEventListener("close", (event) => {
			console.log("Close SSE connection.");
			setSseOpened(false);
		});
	}

	const handleDragOver = (event: any) => {
		setFileDragHover(true);
		event.preventDefault();
		console.log("Hello");
	  };
	
	  const handleDragEnd = (event: any) => {
		setFileDragHover(false);
		event.preventDefault();
		console.log("Goodbye");
	  };
	
	  const handleDrop = (event: any) => {
		setFileDragHover(false);
		event.preventDefault();
		setFilesPrepared(event.dataTransfer.files);
		console.log("Set files to:", event.dataTransfer.files);
		let formData = new FormData()
		formData.append("file", event.dataTransfer.files[0]);
		const uploader = createUploader({ 
		  destination: {method: 'POST', url: "http://localhost:5000/uploadfile", filesParamName: 'file'},
		  autoUpload: true,
		  grouped: true,
		  
		  //...
		});
		
		uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
			console.log(`item ${item.id} started uploading`);  
		});
	
		uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
		  console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
		});
		
		uploader.add(event.dataTransfer.files[0]);
		// // fetch("http://localhost:5000/uploadfile", {method: "POST", body: formData});
		// axios.request({
		//   method: "post", 
		//   url: "http://localhost:5000/uploadfile", 
		//   data: formData, 
		//   onUploadProgress: (p) => {
		//     console.log(p); 
		//     //this.setState({
		//         //fileprogress: p.loaded / p.total
		//     //})
		//   }
	  // }).then (data => {
	  //     //this.setState({
	  //       //fileprogress: 1.0,
	  //     //})
	  //     console.log("Then hook called");
	  // })
	  };

	const log_key_press = (e: {nativeEvent: {key: string, shiftKey: boolean}}) => {
		if (e.nativeEvent.key === 'Enter' && e.nativeEvent.shiftKey === false) {
			setSubmitInput(true);
		}
	};

	useEffect(() => {
		if (submitInput && inputText !== "") {
			setSubmitInput(false);
			setInputText("");
		}
	}, [inputText]);

	return (
		<View style={styles.container}>
			<View style={styles.chatColumn}>
				<View style={styles.chatBoxContainer}>
					<ScrollView 
						style={styles.chatBoxPrimary}
						ref={scrollViewRef}
						onContentSizeChange={() => scrollViewRef.current.scrollToEnd({ animated: true })}
					>
						<Text style={styles.chatBoxText}>
							{chat}
						</Text>
					</ScrollView>
				</View>

				<View style={styles.inputBoxContainer}>
					<div
						onDragOver={handleDragOver}
						onDragEnd={handleDragEnd}
						onDrop = {handleDrop}
						onDragLeave={handleDragEnd}
						style={{
							flex: 8,
							padding: 0,
							height: '100%',
						}}
					>
						<TextInput
							// ref={input => { this.textInput = inputTwo }}
							editable
							multiline
							numberOfLines={4}
							value={inputText}
							onKeyPress={(e: {nativeEvent: {key: string, shiftKey: boolean}}) => {log_key_press(e)}}
							onChangeText={text => {
								setInputText(text);
							}} 
							style={{
								fontFamily: "YingHei",
								fontSize: 15,
								height: '100%',
								width: '100%',
								backgroundColor: (fileDragHover?'#836454':'#D7AE98'),
								borderRadius: 10,
								padding: 10,
							}}
						/>
					</div>
					
					<View style={styles.inputBoxSendContainer}>
						<Pressable onPress={sse_fetch} style={styles.inputBoxSendRequest}>
							<Text style={{fontFamily: "YingHei", fontSize: 15}}>Go</Text>
						</Pressable>
					</View>
					
				</View>
			</View>
			<StatusBar style="auto"/>
		</View>
	);
}

const styles = {
	buttonTest: {
		alignItems: 'center',
		justifyContent: 'center',
		paddingVertical: 12,
		paddingHorizontal: 12,
		borderRadius: 4,
		elevation: 3,
		backgroundColor: 'black',
	},
	leftPanelContainer: {
		flex: 1,
		backgroundColor: '#D7AE98',
		height: '100%',
		// justifyContent: 'center',
		alignItems: 'center',
		paddingVertical: 20
	},
	uploadButton: {
		// flex: 1,
		backgroundColor: '#FF0000',
		// borderRadius: 20,
		alignItems: 'center',
		justifyContent: 'center',
		width: '100%',
		paddingVertical: 10,
		paddingHorizontal: 20
	},
	container: {
		flex: 1,
		flexDirection: 'row',
		backgroundColor: '#D7AE9888',
		alignItems: 'center',
		justifyContent: 'center',
	},
	chatBoxContainer: {
		paddingVertical: 10,
		// width: '100%',
		// height: '500px',
		flex: 5,
		paddingHorizontal: 0,
	},
	chatBoxPrimary: {
		// width: '100%',
		// height: '100%',
		// flexGrow: 0,
		borderRadius: 10,
		backgroundColor: '#D7AE98',
		padding: 10,
	},
	chatBoxText: {
		fontFamily: "YingHei",
		fontSize: 20,
		height: '10px',
	},
	chatColumn: {
		flexDirection: 'column',
		// flex: 5,
		height: '100%',
		width: '88%',
		paddingHorizontal: 0,
		paddingVertical: 24,
	},
	inputBoxContainer: {
		height: 80,
		// flex: 1,
		flexDirection: 'row',
		backgroundColor: '#FFAAAA00',
		borderRadius: 10,
		// margin: '10px 0',
		alignItems: 'center',
		justifyContent: 'space-between',
		// paddingRight: 24,
		paddingVertical: 2,
		
		paddingHorizontal: 0,
		// padding: 10,
	},
	inputBoxTextInput: {
		fontFamily: "YingHei",
		fontSize: 15,
		height: '100%',
		flex: 8,
		backgroundColor: '#D7AE98',
		borderRadius: 10,
		padding: 10,
	},
	inputBoxSendRequest: {
		flex: 1,
		height: '100%',
		backgroundColor: '#D7AE98',
		borderRadius: 20,
		alignItems: 'center',
		justifyContent: 'center',
		padding: 10,
	},
	inputBoxSendContainer: {
		paddingLeft: 10,
		height: '80%',
		width: '10%',
	},
};