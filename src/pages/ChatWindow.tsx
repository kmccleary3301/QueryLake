import { useState, useRef } from 'react';
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

export default function ChatWindow({ navigation }) {
	const scrollViewRef = useRef();
	const [inputText, setInputText] = useState('');
	const [chat, setChat] = useState("Sample Text");
	const [sseOpened, setSseOpened] = useState(false);

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

	const upload_test = async function() {
		// const res = await DocumentPicker.pick({
		//   type: [DocumentPicker.types.allFiles],
		// });

		// const res = await DocumentPickerOptions.pick
		const body = new FormData();
		console.log(body);
		// body.append('file', file)

		// fetch("http://localhost:5000/uploadfile/", {
		//   method: 'POST',
		//   body
		// })
	};

	

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
					<TextInput
						editable
						multiline
						onChangeText={text => setInputText(text)} 
						style={styles.inputBoxTextInput}
					/>
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
		// height: '20%',
		flex: 1,
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