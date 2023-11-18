import craftUrl from "./craftUrl";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

export default function getAvailableModels(userdata : userDataType, onFinish : (result : object) => void) {
  const url = craftUrl("http://localhost:5000/api/get_available_models", {
    "username": userdata.username,
    "password_prehash": userdata.password_pre_hash
  });

  fetch(url, {method: "POST"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve available models:", data.note);
				onFinish({});
        return;
			}
      console.log("Available models:", data.result);
			onFinish(data.result);
		});
	});
}