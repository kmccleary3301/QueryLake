import craftUrl from "./craftUrl";

type timeWindowType = {
  title: string,
  cutoff: number,
  entries: object[]
}

export default function getChatHistory(username : string, password_prehash: string, time_windows : timeWindowType[], set_value: React.Dispatch<React.SetStateAction<any>>) {
  const currentTime = Date.now()/1000;
  const url = craftUrl("http://localhost:5000/api/fetch_chat_sessions", {
    "username": username,
    "password_prehash": password_prehash
  });
  let chat_history_tmp : timeWindowType[] = time_windows.slice();

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      if (!data.success) {
        console.error("Failed to retrieve sessions", data.note);
        return;
      }
      for (let i = 0; i < data.result.length; i++) {
        let entry = {
          time: data.result[i].time,
          title: data.result[i].title,
          hash_id: data.result[i].hash_id,
        };
        // console.log((currentTime - entry.time));
        for (let j = 0; j < chat_history_tmp.length; j++) {
          if ((currentTime - entry.time) < chat_history_tmp[j].cutoff) { 
            // chat_history_tmp_today.push(entry); 
            chat_history_tmp[j].entries.push(entry);
            break
          }
        }
      }
      set_value(chat_history_tmp);
    });
  });
}