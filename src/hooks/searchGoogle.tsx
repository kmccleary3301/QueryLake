// import { SERPAPI_KEY, SERPER_API_KEY } from "$env/static/private";
// import getSerpKey from "./getSerpKey";
import craftUrl from "./craftUrl";
// import { getJson } from "serpapi";
// import type { GoogleParameters } from "serpapi";

type userDataType = {
  username: string,
  password_pre_hash: string,
  serp_key?: string
};

// async function searchWebSerpApi(query: string, serp_api_key : string) {
//   const response = await getJson("google", {
// 		q: query,
// 		hl: "en",
// 		gl: "us",
// 		google_domain: "google.com",
// 		api_key: serp_api_key,
// 	});

// 	// Show result as JSON

// 	return response;
// }

// const _useragent_list = [
//   'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
//   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
//   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
//   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
//   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
//   'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62',
//   'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0'
// ]


// function get_useragent() {
//   return _useragent_list[Math.floor(_useragent_list.length*Math.random())]
// }


// export default function searchGoogle(query : string) {
//   const term = "Google";
//   const results = 20;
//   const lang = "en";
//   const params={
//     "q": term,
//     "num": results + 2,  // Prevents multiple requests
//     "hl": lang,
//     "start": 0,
//   };

//   const url = new URL("https://www.google.com/search");
//   for (const [key, value] of Object.entries(params)) {
//     url.searchParams.append(key, value.toString());
//     // console.log(`${key}: ${value}`);
//   }

//   console.log(url);
//   // for (let key in params) {

//   //   url.searchParams.append(key, params[key]);
//   // }

//   fetch(url, {
//     method: "GET", 
//     headers: {
//       "User-Agent": get_useragent()
//     }
//   }).then((response) => {
// 		console.log(response);
// 		response.json().then((data) => {
//       console.log(data);
// 		});
// 	});
// }


export default function searchGoogle(query : string, userData : userDataType, organization_hash_id : undefined | string, onFinish : (result : object | undefined) => void) {
  const org_specified : boolean = (organization_hash_id !== undefined);
  const params = {...{
    "auth": {
      "username": userData.username,
      "password_prehash": userData.password_pre_hash,
    },
    "query": query
  }, ...(org_specified?{"organization_hash_id": organization_hash_id}:{})};

  const url = craftUrl(`/api/search_google`, params);

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      console.log(data);
      if (!data["success"]) {
        console.error("Google Search Failed:", data.note);
        onFinish(undefined);
        return;
      }
      onFinish(data.result);
    });
  });
}


export function embedUrls(urls : string[], userData : userDataType, onFinish : (result : object | undefined) => void) {
  
  const url = craftUrl(`/api/embed_urls`, {
    "auth": {
      "username": userData.username,
      "password_prehash": userData.password_pre_hash,
    },
    "urls": urls
  });

  fetch(url, {method: "POST"}).then((response) => {
    response.json().then((data) => {
      console.log(data);
      if (!data["success"]) {
        console.error("Embed URLS failed:", data.note);
        onFinish(undefined);
        return;
      }
      onFinish(data.result);
    });
  });
}