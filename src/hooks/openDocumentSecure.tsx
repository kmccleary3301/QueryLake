import {
  Linking
} from "react-native";
import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type metadataType = {
  "type": "pdf"
  "collection_type": "user" | "organization" | "global",
  "document_id": string,
  "document_name": string,
  "location_link_chrome": string,
  "location_link_firefox": string,
} | {
  "type": "web"
  "url": string, 
  "document_name": string
};



export default function openDocumentSecure(userData : userDataType, metadata: metadataType) {
  if (metadata.document_name) {
    const url_doc_access = craftUrl("http://localhost:5000/api/craft_document_access_token", {
      "username": userData.username,
      "password_prehash": userData.password_pre_hash,
      "hash_id": metadata.document_id
    });
    fetch(url_doc_access, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        if (data["success"] == false) {
          console.error("Document Delete Failed", data["note"]);
          return;
        }
        const url_actual = craftUrl("http://localhost:5000/api/async/fetch_document/"+data.result.file_name, {
          "auth_access": data.result.access_encrypted
        })
        Linking.openURL(url_actual.toString()+metadata.location_link_chrome);
      });
    });
  }
  
  // const url = new URL(host);
  // url.searchParams.append("parameters", JSON.stringify(parameters));
  // return url.toString();
}