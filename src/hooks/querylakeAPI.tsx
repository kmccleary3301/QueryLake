import craftUrl from "./craftUrl";
import { 
  timeWindowType, 
  collectionGroup, 
  userDataType, 
  metadataDocumentRaw,
  availableToolchainsResult,
  membershipType,
} from "@/globalTypes";




type getUserMembershipArgs = {
	username : string, 
	password_prehash: string, 
	subset: "accepted" | "open_invitations" | "all", 
	set_value?: React.Dispatch<React.SetStateAction<membershipType[]>> | ((value : membershipType[]) => void), 
	set_admin?: React.Dispatch<React.SetStateAction<boolean>> | ((admin : boolean) => void)
}

/**
 * Retrieves user memberships from the API.
 * @param args - The arguments for retrieving user memberships.
 */
export function getUserMemberships(args: getUserMembershipArgs) {
  const url = craftUrl("http://localhost:5000/api/fetch_memberships", {
    "username": args.username,
    "password_prehash": args.password_prehash,
    "return_subset": args.subset
  });

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      if (!data.success) {
        console.error("Failed to retrieve memberships", [data.note]);
        return;
      }
      if (args.set_admin) { args.set_admin(data.result.admin); }
      if (args.set_value) args.set_value(data.result.memberships);
    });
  });
}

type getUserCollectionArgs = {
	username : string, 
	password_prehash: string, 
	set_value?: React.Dispatch<React.SetStateAction<collectionGroup[]>> | ((value : collectionGroup[]) => void)
}

export function getUserCollections(args: getUserCollectionArgs) {
  const url = craftUrl("http://localhost:5000/api/fetch_all_collections", {
    "username": args.username,
    "password_prehash": args.password_prehash
  });
  const collection_groups_fetch : collectionGroup[] = [];

  // let retrieved_data = {};

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      const retrieved = data.result.collections;
      if (data["success"] == false) {
        console.error("Collection error:", data["note"]);
        return;
      }
      try {
        const personal_collections : collectionGroup = {
          title: "My Collections",
          collections: [],
        };
        for (let i = 0; i < retrieved.user_collections.length; i++) {
          console.log(retrieved.user_collections[i]);
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
      console.log("Start");
      if (args.set_value) args.set_value(collection_groups_fetch);
      console.log("End");
    });
  });
  // return collection_groups_fetch;
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
	userData : userDataType, 
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
    const url_doc_access = craftUrl("http://localhost:5000/api/craft_document_access_token", {
      "username": args.userData.username,
      "password_prehash": args.userData.password_pre_hash,
      "hash_id": args.metadata.document_id
    });
    fetch(url_doc_access, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        if (data["success"] == false) {
          console.error("Document Delete Failed", data["note"]);
          return;
        }
        const url_actual = craftUrl("http://localhost:5000/api/async/fetch_document/"+data.result.file_name, {
          "auth_access": data.result.access_encrypted
        })
        if (args.metadata.type === "pdf") window.open(url_actual.toString()+args.metadata.location_link_chrome);
      });
    });
  }
}

type getSerpKeyArgs = {
	userdata : userDataType, 
	onFinish : (result : string) => void, 
	organization_hash_id? : string
}

export function getSerpKey(args : getSerpKeyArgs) {
	const params = {...{
    "username": args.userdata.username,
    "password_prehash": args.userdata.password_pre_hash
  }, ...((args.organization_hash_id)?{"organization_hash_id": args.organization_hash_id}:{})};

  const url = craftUrl("http://localhost:5000/api/get_serp_key", params);

  fetch(url, {method: "POST"}).then((response) => {
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
	serp_key : string, 
	userdata : userDataType, 
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
      "username": args.userdata.username,
      "password_prehash": args.userdata.password_pre_hash,
      "serp_key": args.serp_key
    },
    ...(org_specified ? { "organization_hash_id": args.organization_hash_id } : {})
  };

  const url = craftUrl("http://localhost:5000/api/" + (org_specified ? "set_organization_serp_key" : "set_user_serp_key"), params);

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
	username : string, 
	password_prehash: string, 
	time_windows : timeWindowType[], 
	set_value?: React.Dispatch<React.SetStateAction<timeWindowType[]>> | ((values : timeWindowType[]) => void)
};

export function getChatHistory(args : getChatHistoryArgs) {
  const currentTime = Date.now()/1000;
  const url = craftUrl("http://localhost:5000/api/fetch_toolchain_sessions", {
    "username": args.username,
    "password_prehash": args.password_prehash
  });
  const chat_history_tmp : timeWindowType[] = args.time_windows.slice();

  fetch(url, {method: "POST"}).then((response) => {
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
	userdata : userDataType, 
	onFinish? : (result : modelTypes) => void
};

export function getAvailableModels(args : getAvailableModelsArgs) {
  const url = craftUrl("http://localhost:5000/api/get_available_models", {
    "username": args.userdata.username,
    "password_prehash": args.userdata.password_pre_hash
  });

  fetch(url, {method: "POST"}).then((response) => {
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
	userdata : userDataAtomic, 
	onFinish? : (result : availableToolchainsResult | undefined) => void
};

export function getAvailableToolchains(args : getAvailableToolchainsArgs) {
  const url = craftUrl("http://localhost:5000/api/get_available_toolchains", {
    "username": args.userdata.username,
    "password_prehash": args.userdata.password_pre_hash
  });

  fetch(url, {method: "POST"}).then((response) => {
		response.json().then((data : {success : true, result: availableToolchainsResult} | {success : false, note : string}) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available toolchains:", data.note);
				if (args.onFinish) args.onFinish(undefined);
        return;
			}
      // console.log("Available models:", data.result);
			if (args.onFinish) args.onFinish(data.result);
		});
	});
}

type setOpenAIAPIKeyArgs = {
	api_key : string, 
	userdata : userDataType, 
	onFinish? : (success : boolean) => void, 
	organization_hash_id? : string
}

export function setOpenAIAPIKey(args : setOpenAIAPIKeyArgs) {
	const org_specified : boolean = (args.organization_hash_id)?true:false;
  
  const params = {...{
    "username": args.userdata.username,
    "password_prehash": args.userdata.password_pre_hash,
  }, ...(org_specified?{
    "openai_organization_id": args.api_key,
    "organization_hash_id": args.organization_hash_id
  }:{
    "openai_api_key": args.api_key
  })};

  const url = craftUrl("http://localhost:5000/api/"+(org_specified?"set_organization_openai_id":"set_user_openai_api_key"), params);

  fetch(url, {method: "POST"}).then((response) => {
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