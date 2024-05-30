"use client";
/**
 * v0 by Vercel.
 * @see https://v0.dev/t/wcm0mArUul3
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */
import { TableHead, TableRow, TableHeader, TableCell, TableBody, Table } from "@/registry/default/ui/table"
import { Button } from "@/registry/default/ui/button"
import { QueryLakeApiKey } from "@/types/globalTypes";
import { useEffect, useRef, useState } from "react";
import { createApiKey, fetchApiKeys } from "@/hooks/querylakeAPI";
import { useContextAction } from "@/app/context-provider";
import { toast } from "sonner";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Pencil, Trash } from "lucide-react";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/registry/default/ui/dialog";
import { Label } from "@/registry/default/ui/label";
import { Input } from "@/registry/default/ui/input";

const MONTH_NAMES = [
	"Jan", "Feb", "Mar", "Apr", "May", "Jun",
	"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];

export default function Component() {

	const { userData } = useContextAction();
	const [ApiKeys, setApiKeys] = useState<QueryLakeApiKey[]>([]);
	const [createdApiKey, setCreatedApiKey] = useState<string>();
	const createApiKeyTitle = useRef<string>();

	useEffect(() => {
		fetchApiKeys({
			auth: userData?.auth as string,
			onFinish: (data) => {
				if (data !== false) {
					const keys_with_date_strings : QueryLakeApiKey[] = data.map((key : QueryLakeApiKey) => {
						const create_date = (new Date(key.created * 1000));
					const created_string = `${MONTH_NAMES[create_date.getMonth()]} ${create_date.getDate()}, ${create_date.getFullYear()}`;
						return {
							...key,
							created_string: created_string
						}
					});
					setApiKeys(keys_with_date_strings);
				} else {
					toast("Failed to fetch API keys");
				}
			}
		})
	}, []);

	const createApiKeyHook = (title : string) => {
		createApiKey({
			auth: userData?.auth as string,
			...(title !== "")?{name: title}:{},
			onFinish: (data) => {
				if (data !== false) {
					const create_date = (new Date(data.created * 1000));
					const created_string = `${MONTH_NAMES[create_date.getMonth()]} ${create_date.getDate()}, ${create_date.getFullYear()}`;
					setApiKeys((old_keys) => [...old_keys, {...data, created_string: created_string}]);
					setCreatedApiKey(data.api_key);
				} else {
					toast("Failed to create API key");
				}
			}
		})
	}

  return (
		<div className="w-full h-[calc(100vh)] flex flex-row justify-center">
      <ScrollArea className="w-full">
				<div className="p-8 px-16">
					<h1 className="text-3xl font-semibold mb-4">All project API keys</h1>
					{/* <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6" role="alert">
						<p className="font-bold">Project API keys have replaced user API keys.</p>
						<p>
							We recommend using project based API keys for more granular control over your resources.{" "}
							<a className="underline text-blue-800" href="#">
								Learn more
							</a>
						</p>
					</div> */}
					<p className="mb-4">
						Do not share your API key with others, or expose it in the browser or other client-side code.
					</p>
					{/* <p className="mb-6">
						View usage per API key on the{" "}
						<a className="underline text-blue-800" href="#">
							Usage page
						</a>
						.
					</p> */}
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead className="text-nowrap w-full">NAME</TableHead>
								<TableHead className="text-nowrap pr-10">SECRET KEY</TableHead>
								<TableHead className="text-nowrap pr-10">CREATED</TableHead>
								<TableHead className="text-nowrap pr-10">LAST USED</TableHead>
								<TableHead className="text-nowrap pr-10">PROJECT ACCESS</TableHead>
								<TableHead className="text-nowrap pr-10">CREATED BY</TableHead>
								<TableHead className="text-nowrap pr-10">PERMISSIONS</TableHead>
								<TableHead className="text-nowrap w-[40px]"><div className=""/></TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{ApiKeys.map((api_key : QueryLakeApiKey, index: number) => (
								<TableRow key={index}>
									<TableCell><p className="text-nowrap">{api_key.title}</p></TableCell>
									<TableCell><p className="text-nowrap">{api_key.key_preview}</p></TableCell>
									<TableCell><p className="text-nowrap">{api_key.created_string}</p></TableCell>
									<TableCell><p className="text-nowrap">May 17, 2024</p></TableCell>
									<TableCell><p className="text-nowrap">Default Project</p></TableCell>
									<TableCell><p className="text-nowrap">{userData?.username}</p></TableCell>
									<TableCell className="text-nowrap">
										<div className="flex items-center">
											All
											{/* <PencilIcon className="ml-2 h-4 w-4 text-gray-600" />
											<TrashIcon className="ml-2 h-4 w-4 text-gray-600" /> */}
										</div>
									</TableCell>
									<TableCell className="text-nowrap py-0">
										<div className="flex flex-row space-x-4">
											<Button variant={"ghost"} className="h-8 w-8 p-0 rounded-full text-primary active:text-primary/70">
												<Pencil className="w-4 h-4"/>
											</Button>
											<Button variant={"ghost"} className="h-8 w-8 p-0 rounded-full text-primary active:text-primary/70">
												<Trash className="w-4 h-4"/>
											</Button>
										</div>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
					<div className="mt-6">
						<Dialog onOpenChange={(open : boolean) => {if (open) setCreatedApiKey(undefined);}}>
							<DialogTrigger asChild>
								<Button>+ Create new secret key</Button>
							</DialogTrigger>
							<DialogContent className="">
								<DialogHeader>
									<DialogTitle>Create a new API key</DialogTitle>
									<DialogDescription>
										Add a new API key for use with the server API.
									</DialogDescription>
								</DialogHeader>
								<div className="grid gap-4 py-4">
									<div className="flex flex-col gap-4">
										<Label htmlFor="name" className="">
											Name (Optional)
										</Label>
										<Input id="name" onChange={(e) => {createApiKeyTitle.current = e.target.value;}} className="col-span-1" />
									</div>
									{/* <div className="flex flex-col gap-4">
										<Label htmlFor="username" className="">
											Username
										</Label>
										<Input id="username" value="@peduarte" className="col-span-3" />
									</div> */}
								</div>
								{createdApiKey && (
									<p className="text-xs text-nowrap">{createdApiKey}</p>
								)}
								<DialogFooter>
									<div className="flex flex-row space-x-4">
										<DialogClose asChild>
											<Button type="button" variant="secondary">
												Cancel
											</Button>
										</DialogClose>
										{(createdApiKey === undefined) && (
											<Button onClick={() => {
												createApiKeyHook(createApiKeyTitle.current || "");
											}}>Create API Key</Button>
										)}
									</div>
								</DialogFooter>
							</DialogContent>
						</Dialog>
						
						<Button className="ml-4" variant="outline">
							View user API keys
						</Button>
					</div>
				</div>
			</ScrollArea>
    </div>
  )
}

// function PencilIcon(props) {
//   return (
//     <svg
//       {...props}
//       xmlns="http://www.w3.org/2000/svg"
//       width="24"
//       height="24"
//       viewBox="0 0 24 24"
//       fill="none"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//     >
//       <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
//       <path d="m15 5 4 4" />
//     </svg>
//   )
// }


// function TrashIcon(props) {
//   return (
//     <svg
//       {...props}
//       xmlns="http://www.w3.org/2000/svg"
//       width="24"
//       height="24"
//       viewBox="0 0 24 24"
//       fill="none"
//       stroke="currentColor"
//       strokeWidth="2"
//       strokeLinecap="round"
//       strokeLinejoin="round"
//     >
//       <path d="M3 6h18" />
//       <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
//       <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
//     </svg>
//   )
// }