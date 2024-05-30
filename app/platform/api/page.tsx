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
import { LockKeyhole, Pencil, Trash } from "lucide-react";
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
            const last_used_date = (key.last_used === null)?null:(new Date(key.last_used * 1000));
            const last_used_string = (last_used_date === null)?
              "Never" :
              `${MONTH_NAMES[last_used_date.getMonth()]} ${last_used_date.getDate()}, ${last_used_date.getFullYear()}`;
            
						return {
							...key,
							created_string: created_string,
              last_used_string: last_used_string
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
					setApiKeys((old_keys) => [...old_keys, {...data, created_string: created_string, last_used_string: "Never"}]);
					setCreatedApiKey(data.api_key);
				} else {
					toast("Failed to create API key");
				}
			}
		})
	}

  const CreateApiKeyButton = () => {
    return (
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
              {/* <DialogClose>
                <Button type="button" variant="secondary">
                  Cancel
                </Button>
              </DialogClose> */}
              {/* {(createdApiKey === undefined) && ( */}
                <Button type="submit" onClick={() => {
                  createApiKeyHook(createApiKeyTitle.current || "");
                }}>Create API Key</Button>
              {/* )} */}
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  return (
		<div className="w-full h-[calc(100vh)] flex flex-row justify-center">
      {(ApiKeys.length > 0) ? (

      
      <ScrollArea className="w-full">
				<div className="pb-8 pt-4 px-16 md:pl-24 space-y-8">
					<h1 className="text-4xl font-semibold mb-4">All project API keys</h1>
					
					<p className="mb-4">
						Do not share your API key with others, or expose it in the browser or other client-side code.
					</p>

					<Table>
						<TableHeader>
							<TableRow>
								<TableHead className="text-nowrap w-full">NAME</TableHead>
								<TableHead className="text-nowrap pr-10">SECRET KEY</TableHead>
								<TableHead className="text-nowrap sm:pr-10 hidden sm:table-cell">CREATED</TableHead>
								<TableHead className="text-nowrap sm:pr-10 hidden md:table-cell">LAST USED</TableHead>
								<TableHead className="text-nowrap pr-10 hidden lg:table-cell">PROJECT ACCESS</TableHead>
								<TableHead className="text-nowrap pr-10 hidden lg:table-cell">CREATED BY</TableHead>
								<TableHead className="text-nowrap lg:pr-10 hidden xl:table-cell">PERMISSIONS</TableHead>
								<TableHead className="text-nowrap w-[40px] hidden xl:table-cell"><div className="min-w-[10px]"/></TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{ApiKeys.map((api_key : QueryLakeApiKey, index: number) => (
								<TableRow key={index}>
									<TableCell><p className="text-nowrap">{api_key.title}</p></TableCell>
									<TableCell><p className="text-nowrap">{api_key.key_preview}</p></TableCell>
									<TableCell className="hidden sm:table-cell">
                    <p className="text-nowrap">{api_key.created_string}</p>
                  </TableCell>
									<TableCell className="hidden md:table-cell">
                    <p className="text-nowrap">{api_key.last_used_string}</p>
                  </TableCell>
									<TableCell className="hidden lg:table-cell">
                    <p className="text-nowrap">Default Project</p>
                  </TableCell>
									<TableCell className="hidden lg:table-cell">
                    <p className="text-nowrap">{userData?.username}</p>
                  </TableCell>
									<TableCell className="text-nowrap hidden xl:table-cell">
										<div className="flex items-center">
											All
											{/* <PencilIcon className="ml-2 h-4 w-4 text-gray-600" />
											<TrashIcon className="ml-2 h-4 w-4 text-gray-600" /> */}
										</div>
									</TableCell>
									<TableCell className="text-nowrap py-0 hidden xl:table-cell">
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
						<CreateApiKeyButton />
						<Button className="ml-4" variant="outline">
							View user API keys
						</Button>
					</div>
				</div>
			</ScrollArea>
      ) : (
        <div className="pb-8 pt-10 px-16 md:pl-24 w-full space-y-8">
					<h1 className="text-3xl font-semibold mb-4 text-wrap">All project API keys</h1>
					<p className="mb-4">
						Do not share your API key with others, or expose it in the browser or other client-side code.
					</p>
          <div className="w-full flex flex-row justify-center p-8 px-16">
            <div className="flex flex-col gap-4">
              <div className="w-auto flex flex-row justify-center">
                <div className="p-2 rounded-md bg-accent flex-shrink">
                  <LockKeyhole className="w-6 h-6 text-primary" />
                </div>
              </div>
              <p className="text-md text-center">Create an API key to access this QueryLake deployment's API</p>
              <div className="w-auto flex flex-row justify-center">
                <CreateApiKeyButton />
              </div>
            </div>
          </div>
        </div>
      )}
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