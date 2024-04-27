"use server"
import { RequestCookie } from 'next/dist/compiled/@edge-runtime/cookies'
import { cookies } from 'next/headers'

export const getCookie = ({
	key, 
	convert_object = true
} : { 
	key : string, 
	convert_object?: boolean
}) => {
	const cookieStore = cookies();

	if (cookieStore.has(key)) {
		const cookie = cookieStore.get(key) as RequestCookie;

		const cookie_get = (convert_object)? JSON.parse(cookie.value) : cookie.value;
		
		return cookie_get;
		// return NextResponse.json({ data: cookie_get }, { status: 200});
	}
	return undefined;
}

export const setCookie = ({ key, value } : { key : string, value : object | string }) => {
	const cookieStore = cookies();
	if (typeof value === 'object') {
		// console.log("Setting Cookie:", key, JSON.stringify(value));
		cookieStore.set(key, JSON.stringify(value));
	} else {
		// console.log("Setting Cookie:", key, value);
		cookieStore.set(key, value);
	}
}

export const deleteCookie = ({ key } : { key : string }) => {
	const cookieStore = cookies();
	cookieStore.delete(key);
}