import craftUrl from "./craftUrl";
import { 
  timeWindowType, 
  collectionGroup, 
  userDataType, 
  metadataDocumentRaw,
  availableToolchainsResult,
  membershipType,
  toolchain_session,
  setStateOrCallback,
  QueryLakeApiKey,
  APIFunctionSpec,
} from "@/types/globalTypes";
import { SERVER_ADDR_HTTP } from "@/config_server_hostnames";
import { ToolChain } from "@/types/toolchains";
import { toast } from "sonner";

type getUserMembershipArgs = {
	auth : string, 
	subset: "accepted" | "open_invitations" | "all", 
	set_value?: React.Dispatch<React.SetStateAction<membershipType[]>> | ((value : membershipType[]) => void), 
	set_admin?: React.Dispatch<React.SetStateAction<boolean>> | ((admin : boolean) => void)
}

type DataResponse<T> = {success : true, result: T} | {success : false, error : string};

/**
 * Retrieves user memberships from the API.
 * @param args - The arguments for retrieving user memberships.
 */
export function getUserMemberships(args: getUserMembershipArgs) {
  const url = craftUrl(`/api/fetch_memberships`, {
    "auth": args.auth,
    "return_subset": args.subset
  });

  fetch(url).then((response) => {
    response.json().then((data) => {
      if (!data.success) {
        console.error("Failed to retrieve memberships", [data.note]);
        return;
      }
      if (args.set_admin) { args.set_admin(data.result.admin); }
      if (args.set_value) args.set_value(data.result.memberships);
      console.log("Fetched memberships:", data.result.memberships);
    });
  });
}

type getUserCollectionsArgs = {
	auth: string, 
	set_value?: React.Dispatch<React.SetStateAction<collectionGroup[]>> | ((value : collectionGroup[]) => void)
}

export function getUserCollections(args: getUserCollectionsArgs) {
  const url = craftUrl(`/api/fetch_all_collections`, {
    "auth": args.auth,
  });
  const collection_groups_fetch : collectionGroup[] = [];

  // let retrieved_data = {};

  fetch(url).then((response) => {
    response.json().then((data) => {
      // console.log("Data:", data);
      const retrieved = data.result.collections;
      if (data["success"] == false) {
        console.error("Collection error:", data["error"]);
        return;
      }
      try {
        const personal_collections : collectionGroup = {
          title: "My Collections",
          collections: [],
        };
        for (let i = 0; i < retrieved.user_collections.length; i++) {
          // console.log(retrieved.user_collections[i]);
          personal_collections.collections.push({
            "title": retrieved.user_collections[i]["name"],
            "hash_id": retrieved.user_collections[i]["hash_id"],
            "items": retrieved.user_collections[i]["document_count"],
            "type": retrieved.user_collections[i]["type"]
          })
        }
        collection_groups_fetch.push(personal_collections);
      } catch { return; }
      try {
        const global_collections : collectionGroup = {
          title: "Global Collections",
          collections: [],
        };
        for (let i = 0; i < retrieved.global_collections.length; i++) {
          global_collections.collections.push({
            "title": retrieved.global_collections[i]["name"],
            "hash_id": retrieved.global_collections[i]["hash_id"],
            "items": retrieved.global_collections[i]["document_count"],
            "type": retrieved.global_collections[i]["type"]
          })
        }
        collection_groups_fetch.push(global_collections);
      } catch { return; }
      try {
        const organization_ids = Object.keys(retrieved.organization_collections)
        for (let j = 0; j < organization_ids.length; j++) {
          try {
            const org_id = organization_ids[j];
            const organization_specific_collections : collectionGroup = {
              title: retrieved.organization_collections[org_id].name,
              collections: [],
            };
            for (let i = 0; i < retrieved.organization_collections[org_id].collections.length; i++) {
              organization_specific_collections.collections.push({
                "title": retrieved.organization_collections[org_id].collections[i].name,
                "hash_id": retrieved.organization_collections[org_id].collections[i].hash_id,
                "items": retrieved.organization_collections[org_id].collections[i].document_count,
                "type": retrieved.organization_collections[org_id].collections[i].type,
              })
            }
            collection_groups_fetch.push(organization_specific_collections)
          } catch { return; }
        }
      } catch { return; }
      // console.log("Start");
      if (args.set_value) args.set_value(collection_groups_fetch);
      // console.log("End");
    });
  });
  // return collection_groups_fetch;
}

export type fetch_collection_document_type = {
  title: string,
  hash_id: string,
  size: string,
  length: string,
  finished_processing: boolean,
}

type collectionResponse = {
  title: string,
  description: string,
  type: "user" | "organization" | "global",
  owner: string,
  public: boolean,
  document_count: number,
}

type fetchCollectionArgs = {
	auth: string, 
	collection_id: string,
  onFinish: (result : collectionResponse | undefined) => void
}

export function fetchCollection(args : fetchCollectionArgs) {
  const url = craftUrl(`/api/fetch_collection`, {
    "auth": args.auth,
    "collection_hash_id": args.collection_id
  });

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(undefined);
        return;
			}
			if (args.onFinish) args.onFinish(data.result as collectionResponse);
		});
	});
}

export function fetchCollectionDocuments({
  auth,
  collection_id,
  limit,
  offset,
  onFinish
}:{
  auth: string,
  collection_id: string,
  limit?: number,
  offset?: number,
  onFinish: (result : fetch_collection_document_type[] | undefined) => void
}) {
  const url = craftUrl(`/api/fetch_collection_documents`, {
    "auth": auth,
    "collection_hash_id": collection_id
  });

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
				if (onFinish) onFinish(undefined);
        return;
			}
			if (onFinish) onFinish(data.result as fetch_collection_document_type[]);
		});
	});
}

type openDocumentArgs = {
	auth: string, 
	document_id: string
}

export function openDocument(args : openDocumentArgs) {

  const url_doc_access = craftUrl("/api/craft_document_access_token", {
    "auth": args.auth,
    "hash_id": args.document_id
  });

  fetch(url_doc_access).then((response) => {
    console.log(response);
    response.json().then((data : DataResponse<{access_encrypted: string, file_name: string}>) => {
      if (data["success"] == false) {
        toast("Failed to fetch document");
        return;
      }
      const url_actual = craftUrl(`/api/fetch_document/${data.result.file_name}`, {
        "document_auth_access": data.result.access_encrypted
      })
      // Linking.openURL(url_actual.toString());
      window.open(url_actual.toString());
      // setUploadFiles([...uploadFiles.slice(0, upload_file_index), ...uploadFiles.slice(upload_file_index+1, uploadFiles.length)]);
    });
  });
}


type createCollectionArgs = {
	auth: string,
	title: string,
  description: string,
  public: boolean,
  organization_id?: string,
  onFinish: (result : false | {
    hash_id: string
  }) => void
}

export function createCollection(args : createCollectionArgs) {
  const url = craftUrl(`/api/create_document_collection`, {...{
    "auth": args.auth,
    "name": args.title,
    "description": args.description,
    "public": args.public,
  }, ...(args.organization_id?{"organization_id": args.organization_id}:{})});

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish) args.onFinish(data.result);
		});
	});
}


type modifyCollectionArgs = {
	auth: string,
  collection_id: string,
	title: string,
  description: string,
  public: boolean,
  onFinish: (result : false | {
    hash_id: string
  }) => void
}

export function modifyCollection(args : modifyCollectionArgs) {
  const url = craftUrl(`/api/modify_document_collection`, {
    "auth": args.auth, 
    "collection_hash_id": args.collection_id,
    "title": args.title,
    "description": args.description,
    // "public": args.public,
  });

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish) args.onFinish(data.result);
		});
	});
}


type deleteDocumentArgs = {
	auth: string, 
	document_id: string,
  onFinish: (result : boolean) => void
}

export function deleteDocument(args : deleteDocumentArgs) {
  const url = craftUrl(`/api/delete_document`, {
    "auth": args.auth,
    "hash_id": args.document_id
  });

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish) args.onFinish(true);
		});
	});
}


// type userDataType = {
//   username: string,
//   password_pre_hash: string,
// };

// type metadataType = {
//   type: "pdf"
//   collection_type: "user" | "organization" | "global",
//   document_id: string,
//   document_name: string,
//   location_link_chrome: string,
//   location_link_firefox: string,
// } | {
//   type: "web"
//   url: string, 
//   document_name: string,
// };

type openDocumentSecureArgs = {
	auth : string, 
	metadata: metadataDocumentRaw
}

type userDataAtomic = {
  username: string,
  password_pre_hash: string,
}

/**
 * `openDocumentSecure` is a function to securely open a PDF document.
 *
 * @param args - An object that includes user data and document metadata.
 * @param args.userData - An object that includes the username and prehashed password of the user.
 * @param args.userData.username - The username of the user.
 * @param args.userData.password_pre_hash - The prehashed password of the user.
 * @param args.metadata - An object that includes the type and ID of the document.
 * @param args.metadata.type - The type of the document. This function only handles documents of type "pdf".
 * @param args.metadata.document_id - The ID of the document.
 * @param args.metadata.location_link_chrome - The location link of the document for Chrome.
 *
 * This function first crafts a URL to get an access token for the document. It then sends a POST request to this URL.
 * If the request is successful, it crafts another URL to fetch the document and opens this URL in a new window.
 *
 * Note: This function does not return anything.
 */
export function openDocumentSecure(args: openDocumentSecureArgs) {
  if (args.metadata.type === "pdf") {
    const url_doc_access = craftUrl(`/api/craft_document_access_token`, {
      "auth": args.auth,
      "hash_id": args.metadata.document_id
    });
    fetch(url_doc_access).then((response) => {
      response.json().then((data) => {
        if (data["success"] == false) {
          console.error("Document Delete Failed", data["note"]);
          return;
        }
        const url_actual = craftUrl(`${SERVER_ADDR_HTTP}/api/async/fetch_document/`+data.result.file_name, {
          "auth_access": data.result.access_encrypted
        })
        if (args.metadata.type === "pdf") window.open(url_actual.toString()+args.metadata.location_link_chrome);
      });
    });
  }
}

type getSerpKeyArgs = {
	auth : string, 
	onFinish : (result : string) => void, 
	organization_hash_id? : string
}

export function getSerpKey(args : getSerpKeyArgs) {
	const params = {...{
    "auth": args.auth
  }, ...((args.organization_hash_id)?{"organization_hash_id": args.organization_hash_id}:{})};

  const url = craftUrl(`/api/get_serp_key`, params);

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("SERP key is undefined:", data.note);
				args.onFinish("");
        return;
			}
			args.onFinish(data.result.serp_key);
		});
	});
}

type setSerpKeyArgs = {
	auth : string, 
	serp_key : string, 
	onFinish? : (success : boolean) => void, 
	organization_hash_id? : string
}

/**
 * Sets the SERP key for a user or organization.
 * @param args - The arguments for setting the SERP key.
 * @param args.userdata - The user data containing the username and pre-hashed password.
 * @param args.serp_key - The SERP key to be set.
 * @param args.organization_hash_id - The hash ID of the organization (optional).
 * @param args.onFinish - The callback function to be called after setting the SERP key (optional).
 */
export function setSerpKey(args: setSerpKeyArgs) {
  const org_specified: boolean = args.organization_hash_id ? true : false;

  const params = {
    ...{
      "auth": args.auth,
      "serp_key": args.serp_key
    },
    ...(org_specified ? { "organization_hash_id": args.organization_hash_id } : {})
  };

  const url = craftUrl(`/api/` + (org_specified ? "set_organization_serp_key" : "set_user_serp_key"), params);

  fetch(url, { method: "POST" }).then((response) => {
    response.json().then((data) => {
      console.log(data);
      if (!data["success"]) {
        console.error("Failed to set SERP key:", data.note);
        if (args.onFinish) args.onFinish(false);
        return;
      }
      if (args.onFinish) args.onFinish(true);
    });
  });
}

type getChatHistoryArgs = {
	auth : string, 
	time_windows : timeWindowType[], 
	set_value?: React.Dispatch<React.SetStateAction<timeWindowType[]>> | ((values : timeWindowType[]) => void)
};

export function getChatHistory(args : getChatHistoryArgs) {
  const currentTime = Date.now()/1000;
  const url = craftUrl(`/api/fetch_toolchain_sessions`, {
    "auth": args.auth
  });
  const chat_history_tmp : timeWindowType[] = args.time_windows.slice();

  fetch(url).then((response) => {
    response.json().then((data) => {
      console.log("Fetched session history:", data);
      if (!data.success) {
        console.error("Failed to retrieve sessions", data.note);
        return;
      }
      const sessions = data.result.sessions;
      for (let i = 0; i < sessions.length; i++) {
        const entry = sessions[i];
        // console.log((currentTime - entry.time));
        for (let j = 0; j < chat_history_tmp.length; j++) {
          if ((currentTime - entry.time) < chat_history_tmp[j].cutoff) { 
            // chat_history_tmp_today.push(entry); 
            chat_history_tmp[j].entries.push(entry);
            break
          }
        }
      }
      if (args.set_value) args.set_value(chat_history_tmp);
    });
  });
}

type modelTypes = {
	default_model: string,
	local_models: string[],
	external_models: {
		openai?: string[]
	}
};

type getAvailableModelsArgs = {
	auth : string, 
	onFinish? : (result : modelTypes) => void
};

export function getAvailableModels(args : getAvailableModelsArgs) {
  const url = craftUrl(`/api/get_available_models`, {
    "auth": args.auth
  });

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available models:", data.note);
				if (args.onFinish) args.onFinish({
					default_model: "Error",
					external_models: {},
					local_models: []
				});
        return;
			}
      console.log("Available models:", data.result.available_models);
			if (args.onFinish) args.onFinish(data.result.available_models);
		});
	});
}

// type toolchainEntry = {
//   name: string,
//   id: string,
//   category: string
//   chat_window_settings: object
// };

// type toolchainCategory = {
//   category: string,
//   entries: toolchainEntry[]
// };

// type availableToolchainsResult = {
// 	default: toolchainEntry,
// 	toolchains: toolchainCategory[]
// }

type getAvailableToolchainsArgs = {
	auth : string, 
	onFinish? : (result : availableToolchainsResult | undefined) => void
};

export function getAvailableToolchains(args : getAvailableToolchainsArgs) {
  const url = craftUrl(`/api/get_available_toolchains`, {
    "auth": args.auth
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : true, result: availableToolchainsResult} | {success : false, error : string}) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available toolchains:", data.error);
				if (args.onFinish) args.onFinish(undefined);
        return;
			}
      // console.log("Available models:", data.result);
			if (args.onFinish) args.onFinish(data.result);
		});
	});
}

type setOpenAIAPIKeyArgs = {
	auth : string, 
	api_key : string, 
	onFinish? : (success : boolean) => void, 
	organization_hash_id? : string
}

export function setOpenAIAPIKey(args : setOpenAIAPIKeyArgs) {
	const org_specified : boolean = (args.organization_hash_id)?true:false;
  
  const params = {...{
    "auth": args.auth
  }, ...(org_specified?{
    "openai_organization_id": args.api_key,
    "organization_hash_id": args.organization_hash_id
  }:{
    "openai_api_key": args.api_key
  })};

  const url = craftUrl(`/api/`+(org_specified?"set_organization_openai_id":"set_user_openai_api_key"), params);

  fetch(url).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to set OpenAI API key:", data.note);
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish) args.onFinish(true);
		});
	});
}

type fetchToolchainSessionsArgs = {
	auth : string, 
	onFinish? : setStateOrCallback<toolchain_session[]>
};

export function fetchToolchainSessions(args : fetchToolchainSessionsArgs) {
  const url = craftUrl(`/api/fetch_toolchain_sessions`, {
    "auth": args.auth
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : true, result: toolchain_session[]} | {success : false, error : string}) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available toolchains:", data.error);
				// if (args.onFinish) args.onFinish(undefined);
        return;
			}
      // console.log("Available models:", data.result);
      const results = data.result as toolchain_session[];

			if (args.onFinish) args.onFinish(results);
		});
	});
}


type fetchToolchainConfigArgs = {
	auth : string,
  toolchain_id: string,
	onFinish? : setStateOrCallback<ToolChain>
};

export function fetchToolchainConfig(args : fetchToolchainConfigArgs) {

  const url = craftUrl(`/api/fetch_toolchain_config`, {
    "auth": args.auth,
    "toolchain_id": args.toolchain_id
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : true, result: ToolChain} | {success : false, error : string}) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available toolchains:", data.error);
				// if (args.onFinish) args.onFinish(undefined);
        return;
			}
      // console.log("Available models:", data.result);
      // const results = data.result as toolchain_session[];

			if (args.onFinish) args.onFinish(data.result);
		});
	});
}


export function modifyUserExternalProviders(args :{
  auth: string,
  update?: object,
  delete?: string[],
  onFinish?: (result : boolean) => void
}) {

  const url = craftUrl(`/api/modify_user_external_providers`, {
    "auth": args.auth,
    ...(args.update)?{"update": args.update}:{},
    ...(args.delete)?{"delete": args.delete}:{},
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean}) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish) args.onFinish(data.success);
		});
	});
}


export function fetchApiKeys(args :{
  auth: string,
  onFinish?: (result : QueryLakeApiKey[] | false) => void
}) {

  const url = craftUrl(`/api/fetch_api_keys`, {
    "auth": args.auth,
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean, result?: {api_keys: QueryLakeApiKey[]}}) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish && data.result) args.onFinish(data.result.api_keys);
		});
	});
}

export function createApiKey(args :{
  auth: string,
  name?: string,
  onFinish?: (result : QueryLakeApiKey & {api_key : string} | false) => void
}) {

  const url = craftUrl(`/api/create_api_key`, {
    "auth": args.auth,
    ...(args.name)?{"title": args.name}:{}
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean, result?: QueryLakeApiKey & {api_key : string}}) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish && data.result) args.onFinish(data.result);
		});
	});
}

export function deleteApiKey(args :{
  auth: string,
  api_key_id: string,
  onFinish?: (result : boolean) => void
}) {

  const url = craftUrl(`/api/delete_api_key`, {
    "auth": args.auth,
    "api_key_id": args.api_key_id
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean, result?: QueryLakeApiKey & {api_key : string}}) => {
      console.log(data);
      if (args.onFinish) args.onFinish(data["success"]);
      return;
		});
	});
}


export function QuerylakeFunctionHelp(args :{
  onFinish?: (result : APIFunctionSpec[] | false) => void
}) {

  const url = craftUrl(`/api/function_help`, {
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean, result?: APIFunctionSpec[]}) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish && data.result) args.onFinish(data.result);
		});
	});
}

export type UsageEntryType = {
  start_timestamp: number,
  organization_id: null | string,
  id: string,
  user_id: string,
  value: object,
  window: "hour" | "day" | "month",
  api_key_id: null | string,
}

export function QuerylakeFetchUsage(args :{
  auth: string,
  onFinish?: (result : UsageEntryType[] | false) => void,
  start_time: number,
  window: "hour" | "day" | "month",
  end_time: number
}) {

  const url = craftUrl(`/api/get_usage_tally`, {
    "auth": args.auth,
    "window": args.window,
    "start_timestamp": args.start_time,
    "end_timestamp": args.end_time
  });

  fetch(url).then((response) => {
		response.json().then((data : {success : boolean, result?: UsageEntryType[]}) => {
      console.log(data);
			if (!data["success"]) {
				if (args.onFinish) args.onFinish(false);
        return;
			}
			if (args.onFinish && data.result) args.onFinish(data.result);
		});
	});
}
