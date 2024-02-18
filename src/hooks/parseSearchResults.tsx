import craftUrl from "./craftUrl";
import { SERVER_ADDR_HTTP } from "@/config_server_hostnames";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function parseSearchResults(userdata : userDataType, urls : string[]) {

  const url = craftUrl(`${SERVER_ADDR_HTTP}/api/parse_urls`, {
    "auth": {
      "username": userdata.username,
      "password_prehash": userdata.password_pre_hash,
    },
    "urls": urls
  });

  fetch(url, {method: "POST"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
      console.log(data);
			if (data.success && !data["success"]) {
        console.error("Failed to parse results:", data.note);
				// onFinish("");
        return;
			}
			// onFinish(data.result);
		});
	});
}
