"use client";
interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}


type collection_mode_type = "create" | "edit" | "view" | undefined;

/**
 * v0 by Vercel.
 * @see https://v0.dev/t/n2FrFZXZwwu
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */

import axios from 'axios';
import { useEffect, useState } from "react"
import { Label } from "@/registry/new-york/ui/label"
import { SelectValue, SelectTrigger, SelectItem, SelectContent, Select } from "@/registry/new-york/ui/select"
import { Input } from "@/registry/new-york/ui/input"
import { Textarea } from "@/registry/new-york/ui/textarea"
import { Button } from "@/registry/new-york/ui/button"
import { ScrollArea } from "@/registry/new-york/ui/scroll-area"
import { SVGProps } from "react"
import { 
  fetchCollection, 
  fetch_collection_document_type,
  deleteDocument,
  createCollection,
  openDocument,
  modifyCollection
} from "@/hooks/querylakeAPI";
import { useContextAction } from "@/app/context-provider";
import craftUrl from "@/hooks/craftUrl";
import { useRouter } from 'next/navigation';
import { Progress } from '@/registry/default/ui/progress';

const file_size_as_string = (size : number) => {
  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  } else if (size < 1024 * 1024 * 1024) {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  } else {
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }
}

export function FileDisplayType({ 
  name, 
  subtext = undefined,
  progress = undefined,
  onOpen = undefined,
  onDelete = undefined
} : { 
  name: string, 
  subtext?: string[],
  progress?: number,
  onOpen?: () => void,
  onDelete?: () => void
}) {
  return (
    <div className="h-14 flex flex-row items-center justify-between border-b pt-2 pb-2">
      <div className='pb-2 flex flex-col'>
        {(onOpen === undefined)?(
          <p className="font-medium max-w-[400px] whitespace-nowrap overflow-hidden text-ellipsis">{name}</p>
        ):(
          <Button variant="link" className="font-medium p-0 h-6]" onClick={onOpen}>
            <p className="font-medium max-w-[50vw] md:max-w-[30vw] xl:max-w-[25vw] whitespace-nowrap overflow-hidden text-ellipsis">{name}</p>
          </Button>
        )}
        {(subtext !== undefined) && (
          <p className={`text-xs text-primary/35`}>{subtext.join(" | ")}</p>
        )}
      </div>
      {progress !== undefined && (
        // <div className="w-1/4 h-2 bg-gray-200 rounded-md">
        //   {/* <div className="h-full bg-blue-500 rounded-md" style={{ width: `${progress}%` }} /> */}
        //   <p>{progress.toString()}</p>
        // </div>
        // <div className=''>
          <Progress value={progress} className='h-2 ml-10 mb-2 w-[100px]' />
        // </div>
      )}
      {(onDelete !== undefined) && (
        <Button size="icon" variant="ghost" onClick={onDelete}>
          <TrashIcon className="w-4 h-4" />
        </Button>
      )}
    </div>
  );
}

type uploading_file_type = {
  title: string,
  progress: number,
}

export default function CollectionPage({ params, searchParams }: DocPageProps) {

  const router = useRouter();
  const collection_mode_immediate = (["create", "edit", "view"].indexOf(params["slug"][0]) > -1) ? params["slug"][0] as collection_mode_type : undefined
  const [CollectionMode, setCollectionMode] = useState<collection_mode_type>(collection_mode_immediate);
  const [collectionTitle, setCollectionTitle] = useState<string>("");
  const [collectionDescription, setCollectionDescription] = useState<string>("");
  const [collectionDocuments, setCollectionDocuments] = useState<fetch_collection_document_type[]>([]);
  const [collectionIsPublic, setCollectionIsPublic] = useState<boolean>(false);
  const [collectionOwner, setCollectionOwner] = useState<string>("personal");
  const [publishStarted, setPublishStarted] = useState<boolean>(false);
  const [uploadingFiles, setUploadingFiles] = useState<uploading_file_type[]>([]);
  const [pendingUploadFiles, setPendingUploadFiles] = useState<File[] | null>(null);


  const {
    userData,
    refreshCollectionGroups,
  } = useContextAction();

  useEffect(() => {
    if ( userData?.auth !== undefined) {
      if (CollectionMode === "edit" || CollectionMode === "view") {
        // setCollectionMode(collection_mode_immediate)
        fetchCollection({
          auth: userData?.auth,
          collection_id: params["slug"][1],
          onFinish: (data) => {
            if (data !== undefined) {
              setCollectionTitle(data.title);
              setCollectionDescription(data.description);
              setCollectionDocuments(data.document_list);
              setCollectionIsPublic(data.public);
            }
          }
        })
      }
    }
  }, [CollectionMode])

  const onPublish = () => {

    const create_args = {
      auth: userData?.auth as string,
      title: collectionTitle,
      description: collectionDescription,
      public: collectionIsPublic,
    }

    if (CollectionMode === "create") {
      createCollection({
        ...create_args, 
        ...(collectionOwner === "personal") ?
                                            {} :
                                            {organization_id: collectionOwner},
        onFinish: (result : false | {hash_id : string}) => {
          if (result !== false) {
            if (pendingUploadFiles !== null) {
              start_document_uploads(result.hash_id);
            } else {
              router.push(`/collection/edit/${result.hash_id}`);
            }
          }
        }
      });
    } else {
      modifyCollection({
        ...create_args,
        collection_id: params["slug"][1],
        onFinish: (result) => {
          if (result !== false && pendingUploadFiles !== null) {
            start_document_uploads(params["slug"][1]);
          }
          refreshCollectionGroups();
        }
      })
      
    }
  }


  // const start_document_uploads = (collection_hash_id : string) => {
  //   let url_2 = craftUrl("/upload/", {
  //     "auth": userData?.auth as string,
  //     "collection_hash_id": collection_hash_id
  //   });
    
  //   const uploader = createUploader({
  //     destination: {
  //       method: "POST",
  //       url: url_2.toString(),
  //       filesParamName: "file",
  //     },
  //     autoUpload: true,
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
  //     console.log(`item ${item.id} started uploading`);
  //     // setFinishedUploads(finishedUploads => finishedUploads+1);
  //     // setCurrentUploadProgress(0);
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
  //     console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
  //     let uploading_files = uploadingFiles;
  //     console.log("uploading_files", uploading_files);

  //     setUploadingFiles(files => [{...files[0], progress: item.completed}, ...files.slice(1)]);
  //   });

  //   uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
  //     console.log(`item ${item.id} response:`, item.uploadResponse);
  //     const new_uploading_files = uploadingFiles.slice(1);
  //     setUploadingFiles(new_uploading_files);
  //     if (new_uploading_files.length === 0) {
  //       onFinishedUploads(collection_hash_id);
  //     }
  //   });

  //   const files = Array.from(pendingUploadFiles as FileList);

  //   for (let i = 0; i < files.length; i++) {
  //     uploader.add(files[i]);
  //   }
  //     setUploadingFiles(files.map((file) => {
  //       return {
  //         title: file.name,
  //         progress: 0
  //       }
  //     }))
  //   setPublishStarted(true);
  // };

  const start_document_uploads = async (collection_hash_id : string) => {
    if (pendingUploadFiles === null) return;

    const url_2 = craftUrl("/upload/", {
      "auth": userData?.auth as string,
      "collection_hash_id": collection_hash_id
    });
  
    setPublishStarted(true);
    
    setUploadingFiles(pendingUploadFiles.map((file) => {
      return {
        title: file.name,
        progress: 0
      }
    }));

    for (let i = 0; i < pendingUploadFiles.length; i++) {
      const file = pendingUploadFiles[i];
      const formData = new FormData();
      formData.append("file", file);
  
      try {
        const response = await axios.post(url_2.toString(), formData, {
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded / (progressEvent.total || 1)) * 100);
            console.log(`File ${file.name} upload progress: ${progress}%`, progress);
            setUploadingFiles(files => [{...files[0], progress: progress}, ...files.slice(1)]);

          },
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        console.log(`File ${file.name} upload response:`, response.data);

        const response_data = response.data as {success: false} | {success : true, result: fetch_collection_document_type};
        // setUploadingFiles(files => [{...files[0], progress: 100}, ...files.slice(1)]);

        if (response_data.success) {
          setCollectionDocuments((docs) => [response_data.result,...docs]);
        }

        setPendingUploadFiles((files) => files?.filter((_, i) => i !== 0) || null)

  
        const new_uploading_files = uploadingFiles.filter((_, i) => i !== 0);
        setUploadingFiles(new_uploading_files);
        if (new_uploading_files.length === 0) {
          onFinishedUploads(collection_hash_id);
        }
      } catch (error) {
        console.error(`Failed to upload file ${file.name}:`, error);
      }
    }
  };


  // THIS FUNCTION IS CONFIRMED WORKING WITH NETWORK
  // HOWEVER IT DOESN'T SUPPORT PROGRESS TRACKING

  // const start_document_uploads = async (collection_hash_id : string) => {
  //   const url_2 = craftUrl("/upload/", {
  //     "auth": userData?.auth as string,
  //     "collection_hash_id": collection_hash_id
  //   });
  
  //   // fetch("/api/upload/", {method: "POST"});

  //   const files = Array.from(pendingUploadFiles as FileList);
  
  //   setPublishStarted(true);
  
  //   for (let i = 0; i < files.length; i++) {
  //     const file = files[i];
  //     const formData = new FormData();
  //     formData.set("file", file);
      
  //     try {
  //       const response = await fetch(url_2.toString(), {
  //         method: 'POST',
  //         body: formData,
  //         // headers: {
  //         //   'Content-Type': 'multipart/form-data'
  //         // }
  //       });
  
  //       if (!response.ok) {
  //         throw new Error(`HTTP error! status: ${response.status}`);
  //       }
  
  //       const data = await response.json();
  
  //       console.log(`File ${file.name} upload response:`, data);
  
  //       const new_uploading_files = uploadingFiles.slice(1);
  //       setUploadingFiles(new_uploading_files);
  //       if (new_uploading_files.length === 0) {
  //         onFinishedUploads(collection_hash_id);
  //       }
  //     } catch (error) {
  //       console.error(`Failed to upload file ${file.name}:`, error);
  //     }
  //   }
  // };

  const onFinishedUploads = (collection_hash_id : string) => {
    setPublishStarted(false);
    setPendingUploadFiles(null);
    refreshCollectionGroups();
    if (CollectionMode === "create")
      router.push(`/collection/edit/${collection_hash_id}`);
  }

  return (
    <ScrollArea className="w-full h-[calc(100vh)]">
      <div className="p-4 flex flex-col items-center w-full min-h-[calc(100vh)]">
        <h1 className="text-3xl font-bold tracking-tight mb-4 text-center">
          {(CollectionMode === "create")?"Create a Document Collection":(CollectionMode === "edit")?"Edit Document Collection":(CollectionMode === "view")?"View Document Collection":"Bad URL!"}
        </h1>
        <div className="grid px-4 md:grid-cols-2 md:gap-8 w-[80%] md:w-full flex-grow max-w-5xl pb-8">
          <div className="gap-2 grid-cols-2 flex flex-col space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div className="grid w-full items-center gap-1.5">
                <Label htmlFor="visibility">Visibility</Label>
                <Select value={(collectionIsPublic?"public":"private")} onValueChange={(value : string) => {
                  setCollectionIsPublic(value === "public");
                }} disabled={(CollectionMode !== "create" && CollectionMode !== "edit")}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select visibility" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">Public</SelectItem>
                    <SelectItem value="private">Private</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid w-full items-center gap-1.5">
                <Label htmlFor="owner">Owner</Label>
                <Select value={collectionOwner} onValueChange={(value : string) => {
                  setCollectionOwner(value);
                }} disabled={(CollectionMode !== "create")}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select owner" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="personal">Personal</SelectItem>
                    {(userData !== undefined) && userData.memberships.map((membership, index) => (
                      <SelectItem key={index} value={membership.organization_id}>{membership.organization_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid w-full items-center gap-1.5">
              <Label htmlFor="title">Title</Label>
              <Input
                onChange={(event) => {
                  setCollectionTitle(event.target.value);
                }}
                value={collectionTitle}
                id="title" 
                placeholder={(params["slug"][0] === "create")?"Enter title":""}
                disabled={(params["slug"][0] === "view")}
              />
            </div>
            <div className="w-full items-center gap-1.5 flex-grow flex flex-col">
              <Label htmlFor="description" className='w-full text-left'>Description</Label>
              <Textarea
                className='flex-grow'
                id="description"
                value={collectionDescription}
                disabled={(params["slug"][0] === "view")}
                onChange={(event) => {
                  setCollectionDescription(event.target.value);
                }}
                placeholder="Enter description"
              />
            </div>
          </div>
          <div className="gap-4 pt-4 md:pt-0 flex flex-col">
            {(CollectionMode === "create" || CollectionMode === "edit") && (
              <div className="grid w-full items-center gap-1.5">
                <Label htmlFor="document">Upload Document</Label>
                <Input id="document" type="file" multiple onChange={(event) =>{
                  if (event.target.files !== null) {
                    setPendingUploadFiles(Array.from(event.target.files));
                  }
                }}/>
              </div>
            )}
            <div className="h-72 w-full rounded-md border flex-grow">
              <ScrollArea className="p-4 pt-2 text-sm h-full">
                {(pendingUploadFiles !== null && !publishStarted) && pendingUploadFiles.map((file, index) => (
                  <FileDisplayType
                    key={index}
                    name={file.name}
                    subtext={[file_size_as_string(file.size)]}
                    onDelete={() => {
                      setPendingUploadFiles(pendingUploadFiles.filter((_, i) => i !== index));
                    }} 
                  />
                ))}

                {uploadingFiles.map((file, index) => (
                  <FileDisplayType
                    key={index}
                    name={file.title}
                    progress={file.progress} 
                  />
                ))}
                {collectionDocuments.map((doc, index) => (
                  <FileDisplayType
                    key={index} 
                    name={doc.title}
                    onOpen={() => {
                      openDocument({
                        auth: userData?.auth as string,
                        document_id: doc.hash_id
                      })
                    }}
                    subtext={[doc.size]} 
                    // progress={doc.progress} 
                    onDelete={(CollectionMode === "create" || CollectionMode === "edit")?(() => {
                      deleteDocument({
                        auth: userData?.auth as string,
                        document_id: doc.hash_id,
                        onFinish: (success : boolean) => {
                          if (success) {
                            const newDocs = collectionDocuments.filter((_, i) => i !== index);

                            setCollectionDocuments(newDocs);
                          }
                        }
                      })
                    }):undefined}
                  />
                ))}
              </ScrollArea>
            </div>
            {(CollectionMode === "create" || CollectionMode === "edit") && (
              <Button disabled={publishStarted} className="w-full h-10" type="submit" onClick={onPublish}>
                Publish
              </Button>
            )}
          </div>
        </div>
      </div>
    </ScrollArea>
  )
}

function TrashIcon(props : SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M3 6h18" />
      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    </svg>
  )
}

