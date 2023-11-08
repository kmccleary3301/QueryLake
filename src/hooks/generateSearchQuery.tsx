import craftUrl from "./craftUrl";

type ChatEntry = {
  origin: ("user" | "server"),
  // content_392098: ChatContent,
  content_raw_string: string
};

type userDataType = {
  username: string,
  password_pre_hash: string,
};

const system_instruction = `You will be provided with a chat history between a user and assistant, 
as well as new question.
Respond to the instructions with an appropriate query to answer the new question with a google search. You should not say more than query. You should not say any words except the query. For the context, today is {{currentDate}}.
The query can be multiple sentences, and should include any relevant details.
However, your response should only consist of the generated google query.
`;

export default function generateSearchQuery(userData : userDataType, context : ChatEntry[], onFinish : (result : string) => void) {
	let today = new Date();
	let dd = String(today.getDate()).padStart(2, '0');
	let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
	let yyyy = today.getFullYear();

	let currentDate = mm + '/' + dd + '/' + yyyy;
	// document.write(today);
	
	let system_instruction_new = system_instruction.replace("{{currentDate}}", currentDate);

	let chat_history = "Chat History:\n\n<HISTORY>\n\n";
	for (let i = Math.max(0, context.length - 4); i < context.length - 1; i++) {
		let origin_string = (context[i].origin === "user")?"USER: ":"ASSISTANT: "
		chat_history += origin_string+context[i].content_raw_string+"\n\n";
	}
	chat_history += "</HISTORY>\n" +
	"Given the above history, craft a google query to answer the following question:\n" +
	"USER: " + context[context.length - 1].content_raw_string;

	console.log("Crafting system instruction");
	console.log(system_instruction_new);
	console.log(chat_history)

	const url = craftUrl("http://localhost:5000/api/chat", {
		"username": userData.username,
		"password_prehash": userData.password_pre_hash,
		"question": chat_history,
		"system_instruction": system_instruction_new,
	});
	fetch(url, {method: "POST"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
			if (!data["success"]) {
				console.error("Failed to retrieve session");
				return;
			}
			console.log(data);
			onFinish(data["result"]);
		});
	});
}