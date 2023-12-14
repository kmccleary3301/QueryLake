import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function setSerpKey(serp_key : string, userdata : userDataType, onFinish : (success : boolean) => void, organization_hash_id : undefined | string) {
	const org_specified : boolean = (organization_hash_id !== undefined);
  
  const params = {...{
    "username": userdata.username,
    "password_prehash": userdata.password_pre_hash,
    "serp_key": serp_key
  }, ...(org_specified?{"organization_hash_id": organization_hash_id}:{})};

  const url = craftUrl("http://localhost:5000/api/"+(org_specified?"set_organization_serp_key":"set_user_serp_key"), params);

  fetch(url, {method: "POST"}).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to set SERP key:", data.note);
				onFinish(false);
        return;
			}
			onFinish(true);
		});
	});
}