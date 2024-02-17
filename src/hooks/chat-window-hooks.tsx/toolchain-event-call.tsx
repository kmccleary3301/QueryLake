import { userDataType } from "@/typing/globalTypes";
import craftUrl from "@/hooks/craftUrl";

type toolchainEventCallArgs = {
	session_hash: string,
	event_node_id: string,
	event_parameters: object,
	user_data: userDataType,
	file_response?: boolean,
}


export default function toolchainEventCall(args : toolchainEventCallArgs) {
	// setEntryFired(true);
	// setEventActive(event_node_id);
	console.log("Calling event", args.event_node_id);
	if (args.session_hash === undefined) {
		console.log("Toolchain Id is undefined!");
		return;
	}

	console.log("urls used:", {
		"username": args.user_data.username,
		"password_prehash": args.user_data.password_pre_hash,
		"session_id": args.session_hash,
		"event_node_id": args.event_node_id,
		"event_parameters": args.event_parameters
	});

	const url = craftUrl("http://localhost:5000/api/async/toolchain_event_call", {
		"username": args.user_data.username,
		"password_prehash": args.user_data.password_pre_hash,
		"session_id": args.session_hash,
		"event_node_id": args.event_node_id,
		"event_parameters": args.event_parameters,
		"return_file_response": (args.file_response)?args.file_response:false
	});

	fetch(url, {method: "GET"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
			console.log(data);
			if (!data["success"]) {
				console.error("Failed to call toolchain event:", data.note);
				// onFinish({});
				return;
			}
			console.log("Successfully called toolchain event. Result:", data);
			if (data.result.flag && data.result.flag === "file_response") {
				const url_doc_access = craftUrl("http://localhost:5000/api/async/get_toolchain_output_file_response/"+data.result.file_name, {
					"server_zip_hash": data.result.server_zip_hash,
					"document_password": data.result.password
				});
				window.open(url_doc_access.toString());
			}
		});
	});
}
