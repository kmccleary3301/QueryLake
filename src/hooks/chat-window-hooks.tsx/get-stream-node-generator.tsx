import craftUrl from "../craftUrl";
import { userDataType, displayType, ChatEntry } from "@/globalTypes";
import hexToUtf8 from "./hex-to-utf8";
import { SetStateAction, Dispatch } from "react";
import EventSource from "@/lib/react-native-server-sent-events";
import { MessageEvent, ErrorEvent } from "@/lib/react-native-server-sent-events";

type getStreamNodeGeneratorProps = {
	node_id : string, 
	stream_argument_id : string, 
	session_id : string,
	user_data : userDataType,
	display_mappings : displayType[],
	set_chat : (Dispatch<SetStateAction<ChatEntry | undefined>>) | ((value : ChatEntry | undefined) => void),
};

export default async function getStreamNodeGenerator(props : getStreamNodeGeneratorProps) {
	console.log("stream node prop call:", {
		"username": props.user_data.username,
		"password_prehash": props.user_data.password_pre_hash,
		"session_id": props.session_id,
		"event_node_id": props.node_id,
		"stream_variable_id": props.stream_argument_id
	});
	const url = craftUrl("http://localhost:5000/api/async/toolchain_stream_node_propagation_call", {
		"username": props.user_data.username,
		"password_prehash": props.user_data.password_pre_hash,
		"session_id": props.session_id,
		"event_node_id": props.node_id,
		"stream_variable_id": props.stream_argument_id
	});
	
	console.log("Created url:", url);
	const es = new EventSource(url, {
		method: "GET",
	});

	es.addEventListener("open", () => {
		console.log("Open stream node SSE connection.", props.node_id);
		
	});

	console.log("GLOBAL DISPLAY MAPPINGS:", props.display_mappings);

	const relevant_display_mappings : displayType[] = [];
	for (let i = 0; i < props.display_mappings.length; i++) {
		console.log("Parsing displayMap for relevance:", props.display_mappings[i]);
		if (props.display_mappings[i].input_argument === props.node_id && (props.display_mappings[i].type === "node_stream_temporary_output" || props.display_mappings[i].type === "node_stream_output")) {
			console.log("Pushing");
			relevant_display_mappings.push(props.display_mappings[i]);
		}
	}
	console.log("Using relevant mappings:", relevant_display_mappings);
	let recieved_string = "";
	es.addEventListener("message", (event : MessageEvent) => {
		let decoded = event.data.toString();
		decoded = hexToUtf8(decoded);
		// decoded = JSON.parse(decoded);
		if (decoded === "<<CLOSE>>") {
			es.close();
			return;
		}
		recieved_string += decoded;
		for (let i = 0; i < relevant_display_mappings.length; i++) {
			const mapping = relevant_display_mappings[i];
			if (mapping.display_as === "chat_entry") {
				props.set_chat({
					role: 'assistant',
					state: 'writing',
					content: recieved_string
				});
			}
		}
	});

	es.addEventListener("error", (event : ErrorEvent) => {
		if (event.type === "error") {
			console.error("Connection error:", event.message);
		} else if (event.type === "exception") {
			console.error("Error:", event.message, event.error);
		}
	});

	es.addEventListener("close", () => {
		console.log("Close stream node SSE connection.");
		props.set_chat(undefined);
	});
}
