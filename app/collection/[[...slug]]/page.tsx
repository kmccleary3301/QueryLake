"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { DataTableInfinite, DataTableInfiniteProps } from "@/components/custom/data_table_infinite/data-table-infinite";
import { useContextAction } from "@/app/context-provider";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useQueryStates } from "nuqs";
import { useEffect, useMemo, useState } from "react";
import { columns, ColumnSchema, columnSchema, InfiniteQueryMeta, searchParamsParser, searchParamsSerializer } from "./columns";
import { DataFetcher, dataOptions } from "./query-options";
import { fetchCollection } from "@/hooks/querylakeAPI";
import craftUrl from "@/hooks/craftUrl";

import axios from 'axios';
import { Label } from '@/components/ui/label';
import { SelectValue, SelectTrigger, SelectItem, SelectContent, Select } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { SVGProps } from "react"
import {
  fetch_collection_document_type,
  deleteDocument,
  createCollection,
  openDocument,
  modifyCollection,
  fetchCollectionDocuments
} from "@/hooks/querylakeAPI";
// import { useContextAction } from "@/app/context-provider";
// import craftUrl from "@/hooks/craftUrl";
import { useRouter } from 'next/navigation';
import { Progress } from '@/components/ui/progress';
import { Copy, LucideLoader2 } from 'lucide-react';
import "./spin.css";
import { handleCopy } from '@/components/markdown/markdown-code-block';
import { ColumnDef } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";

// const COLLECTION_ID = "wAloo9uVIwU9IhidVvU2MR0JXKOWi5A6";

const defaultFetcher: DataFetcher = async (params) => {
  console.log("defaultFetcher Params", params);
  const url_make = craftUrl('/api/search_bm25', params);

  const response = await fetch(url_make);
  const result = await response.json();
  console.log("defaultFetcher Result", result);

  return Promise.resolve({
    data: result.result,
    meta: {
      totalRowCount: 1000,
      filterRowCount: result.total + 10,
    } as InfiniteQueryMeta
  });
};

interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

type uploading_file_type = {
  title: string,
  progress: number,
}

type collection_mode_type = "create" | "edit" | "view" | undefined;

export default function Page({ params, searchParams }: DocPageProps) {
  const { userData, refreshCollectionGroups } = useContextAction();
  const [totalDBRowCount, setTotalDBRowCount] = useState(0);

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
  const [dataRowsProcessed, setDataRowsProcessed] = useState<ColumnSchema[]>([]);

  

  const fetchCollectionCallback = () => {
    if (!userData?.auth) return;
    fetchCollection({
      auth: userData.auth,
      collection_id: params["slug"][1],
      onFinish: (data) => {
        console.log("Collection Data", data);
        if (data === undefined) { return; }
        setCollectionTitle(data.title);
        setCollectionDescription(data.description);
        setCollectionIsPublic(data.public);
        setTotalDBRowCount(data.document_count);
      }
    });
  };


  // Keep refreshing collection documents every 5s if they are still processing
  useEffect(() => { 
    let documents_processing = false;
    collectionDocuments.forEach(doc => {
      if (!doc.finished_processing) {
        documents_processing = true;
      }
    });
    if (documents_processing) {
      setTimeout(() => {
        // TODO: update this to fetch documents where finished_processing is false
      }, 5000)
    }
  }, [collectionDocuments]);


  useEffect(() => {
    if ( userData?.auth !== undefined) {
      if (CollectionMode === "edit" || CollectionMode === "view") {
        // setCollectionMode(collection_mode_immediate)
        fetchCollectionCallback();
      }
    }
  }, [CollectionMode])


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

    const totalCount = pendingUploadFiles.length;

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
            // setUploadingFiles(files => [...files.slice(0, i), {...files[i], progress: progress}, ...files.slice(i+1)]);
          },
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        const response_data = response.data as {success: false} | {success : true, result: fetch_collection_document_type};

        if (response_data.success) {
          setUploadingFiles(files => files.slice(1));
          setCollectionDocuments((docs) => [response_data.result,...docs]);
          if (i === totalCount - 1) {
            onFinishedUploads(collection_hash_id);
          }
        }
        setPendingUploadFiles((files) => files?.filter((_, j) => j !== 0) || null)
        console.log("Pending Uploading Files", pendingUploadFiles.length);

      } catch (error) {
        console.error(`Failed to upload file ${file.name}:`, error);
      }
    }
  };

  const onFinishedUploads = (collection_hash_id : string) => {
    setPublishStarted(false);
    setPendingUploadFiles(null);
    refreshCollectionGroups();
    if (CollectionMode === "create")
      router.push(`/collection/edit/${collection_hash_id}`);
  }

  const [search] = useQueryStates(searchParamsParser);
  const { data, isFetching, isLoading, fetchNextPage } = useInfiniteQuery(
    dataOptions(
      search,
      userData?.auth as string,
      params["slug"][1],
      defaultFetcher
    )
  );

  const flatData = useMemo(
    () => data?.pages?.flatMap((page) => page.data ?? []) ?? [],
    [data?.pages]
  );

  useEffect(() => {
    console.log("Data", data);
  }, [data]);


  const lastPage = data?.pages?.[data?.pages.length - 1];
  const filterDBRowCount = lastPage?.meta?.filterRowCount;
  const totalFetched = flatData?.length;

  const { sort, start, size, ...filter } = search;

  const deletionColumn : ColumnDef<ColumnSchema> = {
    id: "delete_button",
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Deletion" />
    ),
    cell: ({ row }) => {
      const value = row.getValue("id") as string;
      return (
        <Button 
          className="h-6 p-2 bg-[#DC2626] hover:bg-[#DC2626]/70 active:bg-[#DC2626]/50"
        >
          {/* <Trash className="w-4 h-4 p-0" /> */}
          <p className="text-black font-mono">Delete</p>
        </Button>
      )
    },
    enableHiding: true,
  }

  useEffect(() => {
    setDataRowsProcessed(flatData);
  }, [flatData, uploadingFiles, pendingUploadFiles]);

  return (
    <div className="w-full h-[calc(100vh)] flex flex-row justify-center overflow-hidden sticky">
      {/* <ScrollArea className="w-full"> */}
        <div className="flex flex-row w-full justify-center overflow-hidden">
          <div className="flex flex-col overflow-hidden w-full">
            <DataTableInfinite
              className="overflow-hidden w-[100%]"
              columns={[...columns, deletionColumn]}
              data={dataRowsProcessed}
              // data={flatData}
              totalRows={totalDBRowCount}
              // filterRows={filterDBRowCount}
              filterRows={totalDBRowCount}
              totalRowsFetched={totalFetched}
              defaultColumnFilters={Object.entries(filter)
                .map(([key, value]) => ({
                  id: key,
                  value,
                }))
                .filter(({ value }) => value ?? undefined)}
              defaultColumnSorting={sort ? [sort] : undefined}
              searchColumnFiltersSchema={columnSchema}
              searchParamsParser={searchParamsParser}
              isFetching={isFetching}
              isLoading={isLoading}
              fetchNextPage={fetchNextPage}
            />
          </div>
        </div>
      {/* </ScrollArea> */}
    </div>
  );
}
