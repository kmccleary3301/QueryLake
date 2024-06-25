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
import { createApiKey, deleteApiKey, fetchApiKeys } from "@/hooks/querylakeAPI";
import { useContextAction } from "@/app/context-provider";
import { toast } from "sonner";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Copy, LockKeyhole, Pencil, Plus, Trash } from "lucide-react";
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/registry/default/ui/dialog";
import { Label } from "@/registry/default/ui/label";
import { Input } from "@/registry/default/ui/input";
import { handleCopy } from "@/components/markdown/markdown-code-block";

const MONTH_NAMES = [
	"Jan", "Feb", "Mar", "Apr", "May", "Jun",
	"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
];


function CreateApiKeyButtonDialog({
  createApiKeyHook,
  setCreatedApiKey,
  createdApiKey,
  createApiKeyTitle,
}:{
  createApiKeyHook: (title : string) => void,
  setCreatedApiKey: React.Dispatch<React.SetStateAction<string | undefined>>,
  createdApiKey: string | undefined,
  createApiKeyTitle: React.MutableRefObject<string>
}) {
  return (
    <Dialog onOpenChange={(open : boolean) => {if (open) setCreatedApiKey(undefined);}}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="w-4 h-4 mr-2"/>
          Create new secret key
        </Button>
      </DialogTrigger>
      <DialogContent className="border-1">
        <DialogHeader>
          <DialogTitle>Create a new API key</DialogTitle>
          <DialogDescription>
            Add a new API key for use with the server API.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {((createdApiKey || "").length === 0) ? (
            
            <div className="flex flex-col gap-4">
              <Label htmlFor="name" className="">
                Name (Optional)
              </Label>
              <Input id="name" onChange={(e) => {createApiKeyTitle.current = e.target.value;}} className="col-span-1" />
            </div>
          ):(
            // <div className="flex flex-row space-x-4 max-w-full -mr-4" style={((createdApiKey || "").length > 0)?{}:{display: "none"}}>
              <div className="flex flex-row space-x-4 justify-between">
              <p className="text-sm text-nowrap overflow-hidden p-2 py-1 border-2 border-green-500 rounded-lg flex flex-col justify-center" >
                {createdApiKey}
              </p>
              <Button type="submit" className="p-0 m-0" variant={"transparent"} onClick={() => {
                handleCopy(createdApiKey || "")
              }}>
                <Copy className="w-4 h-4 text-primary"/>
              </Button>
              </div>
            // </div>
          )}
          
        </div>
        
        {/* <div className="flex flex-row gap-x-4 justify-between" style={((createdApiKey || "").length > 0)?{}:{display: "none"}}>
          <p className="text-sm text-nowrap p-2 py-1 border-2 border-green-500 rounded-lg flex flex-col justify-center" >
            {createdApiKey}
          </p>
          <Button className="p-0 m-0" variant={"transparent"} onClick={() => {
            handleCopy(createdApiKey || "")
          }}>
            <Copy className="w-4 h-4 text-primary"/>
          </Button>

        </div> */}
        <DialogFooter className="justify-between flex flex-row">
          {((createdApiKey || "").length === 0) ? (
            
            <Button type="submit" onClick={()=>{
              createApiKeyHook(createApiKeyTitle.current || "");
              console.log("Submitting")
            }}>Create API Key</Button>
          ):(
            // <div className="flex flex-row space-x-4 max-w-full -mr-4" style={((createdApiKey || "").length > 0)?{}:{display: "none"}}>
              <>
              
              </>
            // </div>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Component() {

	const { userData } = useContextAction();
	const [ApiKeys, setApiKeys] = useState<QueryLakeApiKey[]>([]);
	const [createdApiKey, setCreatedApiKey] = useState<string>();
	const createApiKeyTitle = useRef<string>("");

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

  

  return (
		<div className="w-full h-[calc(100vh)] flex flex-row justify-center">

      
      <ScrollArea className="w-full">
				<div className="pb-8 pt-4 px-16 md:pl-24 space-y-8">
					<h1 className="text-4xl font-semibold mb-4">All project API keys</h1>
					
					<p className="mb-4">
						Do not share your API key with others, or expose it in the browser or other client-side code.
					</p>
      {(ApiKeys.length > 0) ? (
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
                        <Button variant={"transparent"} className="h-8 w-8 p-0 rounded-full text-primary active:text-primary/70">
                          <Pencil className="w-4 h-4"/>
                        </Button>
                        <Button 
                          variant={"transparent"} 
                          className="h-8 w-8 p-0 rounded-full text-primary active:text-primary/70"
                          onClick={() => {
                            deleteApiKey({
                              auth: userData?.auth as string,
                              api_key_id: api_key.id,
                              onFinish: (success : boolean) => {
                                if (success) {
                                  setApiKeys((old_keys) => [...old_keys.slice(0, index), ...old_keys.slice(index + 1)]);
                                }
                              }
                            })
                          }}
                        >
                          <Trash className="w-4 h-4"/>
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="pt-10 px-16 md:pl-24 w-full space-y-8">
              {/* <h1 className="text-3xl font-semibold mb-4 text-wrap">All project API keys</h1>
              <p className="mb-4">
                Do not share your API key with others, or expose it in the browser or other client-side code.
              </p> */}
              <div className="w-full flex flex-row justify-center pt-8 pb-0 px-16">
                <div className="flex flex-col gap-8 pb-0 pt-16">
                  <div className="w-auto flex flex-row justify-center">
                    <div className="p-2 rounded-md bg-accent flex-shrink">
                      <LockKeyhole className="w-6 h-6 text-primary" />
                    </div>
                  </div>
                  <p className="text-md text-center w-[300px]">Create an API key to access this QueryLake deployment's API</p>
                  
                </div>
              </div>
            </div>
          )}
          <div className="px-16 md:pl-24 w-auto flex flex-row" style={{
            ...{justifyContent: (ApiKeys.length > 0)?"start":"center"},
            ...(ApiKeys.length > 0)?{paddingLeft: 0}:{}
          }}>
            <CreateApiKeyButtonDialog 
              createApiKeyHook={createApiKeyHook} 
              setCreatedApiKey={setCreatedApiKey} 
              createdApiKey={createdApiKey}
              createApiKeyTitle={createApiKeyTitle}
            />
            {(ApiKeys.length > 0) && (

              <Button className="ml-4" variant="outline">
                View user API keys
              </Button>
            )}
          </div>
          {/* </ScrollArea> */}
					{/* <div className="mt-6">
						<CreateApiKeyButtonDialog 
              createApiKeyHook={createApiKeyHook} 
              setCreatedApiKey={setCreatedApiKey} 
              createdApiKey={createdApiKey}
              createApiKeyTitle={createApiKeyTitle}
            />
						
					</div> */}
				</div>
			</ScrollArea>
      
    </div>
  )
}