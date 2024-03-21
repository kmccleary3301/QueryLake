"use client";

// import { getCookie } from "@/hooks/cookie-move";
import { getCookie } from "@/hooks/cookies";
import { useEffect, useState } from "react";

export default function DisplayUserDataCookie() {
	const [cookie, setCookie] = useState(null);

	const cookieRetrieve = async() => {

		setCookie(await getCookie({ key: "UD" }));
	}

	useEffect(() => {
		// console.log("Component got cookie:", cookie);
		cookieRetrieve();
	}, []);

  return (
    <div>
      <h1>Display User Data Cookie</h1>
			<p>{JSON.stringify(cookie, null, "\t")}</p>
    </div>
  );
}