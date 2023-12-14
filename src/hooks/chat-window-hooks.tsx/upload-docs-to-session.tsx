import { userDataType } from "@/globalTypes";
import craftUrl from "@/hooks/craftUrl";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";

type uploadDocsToSessionArgs = {
	session_hash : string,
	model_in_use: string | string[],
	collection_hash_id : string,
	on_finish? : () => void,
	userData : userDataType,
	setUploadFiles : (files : File[]) => void | React.Dispatch<React.SetStateAction<File[]>>,
	uploadFiles : File[],
	setEventActive? : (event : string) => void,
}

export default function uploadDocsToSession(args : uploadDocsToSessionArgs) {
	console.log("Got session hash:", args.session_hash);
	const url_2 = craftUrl("http://localhost:5000/api/async/upload_document_to_session", {
		"username": args.userData.username,
		"password_prehash": args.userData.password_pre_hash,
		"collection_hash_id": args.collection_hash_id,
		"session_id": args.session_hash,
		"collection_type": "toolchain_session",
		"event_parameters": {
			"model_choice": args.model_in_use
		}
	});
	
	const uploader = createUploader({
		destination: {
			method: "POST",
			url: url_2.toString(),
			filesParamName: "file",
		},
		autoUpload: true,
	});
	// const upload_files : File[]	= [];

	args.setUploadFiles([]);
	// let finished_uploads = 0;

	uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
		console.log(`item ${item.id} started uploading`);
		// setFinishedUploads(finishedUploads => finishedUploads+1);
		// setCurrentUploadProgress(0);
	});

	uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
		console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
		// setCurrentUploadProgress(item.completed);
	});

	uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
		console.log(`item ${item.id} response:`, item.uploadResponse);

		// finished_uploads += 1;

		// if (uploadFiles.length === 1) {
		//   on_finish();
		//   setUploadFiles([]);
		// } else {
		//   setUploadFiles(uploadFiles.slice(1, uploadFiles.length));
		// }
		
		// if (uploadFiles.length) {
			// setUploadFiles([]);
		//   props.setRefreshSidePanel(["collections"]);
		//   if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
		//   if (props.navigation) { props.navigation.navigate("ChatWindow"); }
		// }
	});
	// let formData = new FormData();
	for (let i = 0; i < args.uploadFiles.length; i++) {
		// formData.append("file", event.dataTransfer.files[i]);
		uploader.add(args.uploadFiles[i]);
		console.log(args.uploadFiles[i]);
	}
	// setPublishStarted(true);

	if (args.uploadFiles.length === 0) {
		// props.setRefreshSidePanel(["collections"]);
		// if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
		// if (props.navigation) { props.navigation.navigate("ChatWindow"); }
	}
	if (args.setEventActive) args.setEventActive("file_upload");
}