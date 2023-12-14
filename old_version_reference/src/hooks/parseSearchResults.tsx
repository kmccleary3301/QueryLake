import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function parseSearchResults(userdata : userDataType, urls : string[]) {

  const url = craftUrl("http://localhost:5000/api/parse_urls", {
    "username": userdata.username,
    "password_prehash": userdata.password_pre_hash,
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
