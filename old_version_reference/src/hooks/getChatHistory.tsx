import craftUrl from "./craftUrl";

type timeWindowType = {
  title: string,
  cutoff: number,
  entries: object[]
}

export default function getChatHistory(username : string, password_prehash: string, time_windows : timeWindowType[], set_value: React.Dispatch<React.SetStateAction<any>>) {
  const currentTime = Date.now()/1000;
  const url = craftUrl("http://localhost:5000/api/fetch_toolchain_sessions", {
    "username": username,
    "password_prehash": password_prehash
  });
  let chat_history_tmp : timeWindowType[] = time_windows.slice();

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      console.log("Fetched session history:", data);
      if (!data.success) {
        console.error("Failed to retrieve sessions", data.note);
        return;
      }
      const sessions = data.result.sessions;
      for (let i = 0; i < sessions.length; i++) {
        let entry = sessions[i];
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