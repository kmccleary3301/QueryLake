import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function getSerpKey(userdata : userDataType, onFinish : (result : string) => void, organization_hash_id : undefined | string) {
	const params = {...{
    "username": userdata.username,
    "password_prehash": userdata.password_pre_hash
  }, ...((organization_hash_id !== undefined)?{"organization_hash_id": organization_hash_id}:{})};

  const url = craftUrl("http://localhost:5000/api/get_serp_key", params);

  fetch(url, {method: "POST"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("SERP key is undefined:", data.note);
				onFinish("");
        return;
			}
			onFinish(data.result);
		});
	});
}
