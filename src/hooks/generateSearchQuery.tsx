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
Respond to the instructions with a long query which states the question clearly without additional context required. 
You should not say more than the query. You should not say any words except the query. For the context, today is {{currentDate}}.
The query can be multiple sentences, and should include any relevant details.
The query should emulate what desired reference materials might ideally contain.
However, your response should only consist of the generated google query, with no additional words, symbols, or quotations.
Do not begin your response with an introduction, assurance, or otherwise.
`;

export default function generateSearchQuery(userData : userDataType, context : ChatEntry[], onFinish : (result : string) => void) {
	let today = new Date();
	let dd = String(today.getDate()).padStart(2, '0');
	let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
	let yyyy = today.getFullYear();

	let currentDate = mm + '/' + dd + '/' + yyyy;
	// document.write(today);
	
	let system_instruction_new = system_instruction.replace("{{currentDate}}", currentDate);

	let history_to_send = [{role: "system", content: system_instruction_new}]

	let chat_history = "Chat History:\n\n<HISTORY>\n\n";
	for (let i = 0; i < context.length - 1; i++) {
		let origin_string = (context[i].origin === "user")?"USER: ":"ASSISTANT: "
		chat_history += origin_string+context[i].content_raw_string+"\n\n";
		history_to_send.push({
			role: (context[i].origin === "user")?"user":"assistant",
			content: context[i].content_raw_string
		})
	}
	chat_history += "</HISTORY>\n" +
	"Given the previous chat history, craft a lexical query to answer the following question, and do not write anything else except for the query.\n" +
	"Do not search for visual data, such as images or videos, as these will be completely useless.\n" +
	"USER: " + context[context.length - 1].content_raw_string;

	history_to_send.push({
		role: "user",
		content: chat_history
	})

	console.log("Crafting system instruction");
	console.log(system_instruction_new);
	console.log(chat_history)

	const url = craftUrl("http://localhost:5000/api/llm_call_model_synchronous", {
		"username": userData.username,
		"password_prehash": userData.password_pre_hash,
		"history": history_to_send
	});
	fetch(url, {method: "POST"}).then((response) => {
		console.log(response);
		response.json().then((data) => {
      console.log(data);
			if (!data["success"]) {
        console.error("Failed to retrieve session");
				return;
			}
      let query = data.result
        .replace(/^[\s]*(Sure)[\!]?[^\n]*\n/, "")
        
        // .replace(/(?i)(sure)/, "")
        .replace(/^[\s]*[\"|\'|\`]*/, "")
        .replace(/[\"|\'|\`]*[\s]*$/, "");
      console.log([query]);
			onFinish(query);
		});
	});
}