import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function setOpenAIAPIKey(api_key : string, userdata : userDataType, onFinish : (success : boolean) => void, organization_hash_id : undefined | string) {
	const org_specified : boolean = (organization_hash_id !== undefined);
  
  const params = {...{
    "username": userdata.username,
    "password_prehash": userdata.password_pre_hash,
  }, ...(org_specified?{
    "openai_organization_id": api_key,
    "organization_hash_id": organization_hash_id
  }:{
    "openai_api_key": api_key
  })};

  const url = craftUrl("http://localhost:5000/api/"+(org_specified?"set_organization_openai_id":"set_user_openai_api_key"), params);

  fetch(url, {method: "POST"}).then((response) => {
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to set OpenAI API key:", data.note);
				onFinish(false);
        return;
			}
			onFinish(true);
		});
	});
}