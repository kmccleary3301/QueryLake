"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { DataTableInfinite, DataTableInfiniteProps } from "@/components/custom/data_table_infinite/data-table-infinite";
import { useContextAction } from "@/app/context-provider";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useQueryStates } from "nuqs";
import { Usable, useEffect, useMemo, useState, use } from "react";
import { columns, ColumnSchema, columnSchema, InfiniteQueryMeta, searchParamsParser, searchParamsSerializer } from "./columns";
import { DataFetcher, dataOptions } from "./query-options";
import { fetchCollection, QueryLakeFetchDocument } from "@/hooks/querylakeAPI";
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
import { ColumnDef, Table } from "@tanstack/react-table";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import { DocumentChunkTableSheetDetails, DocumentChunkSheetDetailsContent } from "./data-table-sheet-details";
import { useParams } from "next/navigation";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { AppSidebar } from "@/components/app-sidebar";
import { CollectionSidebar } from "./document-sidebar";
import { userDataType } from "@/types/globalTypes";

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

type uploading_file_type = {
  title: string,
  progress: number,
}

type collection_mode_type = "create" | "edit" | "view" | undefined;

export default function Page() {
  const { userData, refreshCollectionGroups } = useContextAction();
  const [totalDBRowCount, setTotalDBRowCount] = useState(0);

  const resolvedParams = useParams() as {
    slug: string[],
  };

  const collection_mode_immediate = "view";
  
  const [CollectionMode, setCollectionMode] = useState<collection_mode_type>(collection_mode_immediate);
  const [collectionTitle, setCollectionTitle] = useState<string>("");
  const [collectionDocuments, setCollectionDocuments] = useState<fetch_collection_document_type[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<uploading_file_type[]>([]);
  const [pendingUploadFiles, setPendingUploadFiles] = useState<File[] | null>(null);
  const [dataRowsProcessed, setDataRowsProcessed] = useState<ColumnSchema[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [collectionId, setCollectionId] = useState<string | undefined>(undefined);

  const fetchCollectionCallback = () => {
    if (!userData?.auth) return;
    QueryLakeFetchDocument({
      auth: userData.auth,
      document_id: resolvedParams["slug"][1],
      onFinish: (data) => {
        console.log("Document Data", data);
        if (data === false) { return; }
        setCollectionTitle(data.file_name);
        setTotalDBRowCount(data.chunk_count);
        setCollectionId(data.collection_id);
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


  const [search] = useQueryStates(searchParamsParser);
  const { data, isFetching, isLoading, fetchNextPage } = useInfiniteQuery(
    dataOptions(
      search,
      userData?.auth as string,
      resolvedParams["slug"][1],
      collectionId as string,
      defaultFetcher
    )
  );

  const flatData = useMemo(
    () => data?.pages?.flatMap((page) => page.data ?? []) ?? [],
    [data?.pages]
  );

  // useEffect(() => {
  //   console.log("Data", data);
  // }, [data]);

  // useEffect(() => {
  //   if (collectionId === undefined) return;
  //   fetchNextPage();
  // }, [collectionId]);


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
    <div 
      className="w-full h-[calc(100vh)] absolute flex flex-row justify-center overflow-hidden"
      style={{
        "--container-width": "100%"
      } as React.CSSProperties}
    >
      {/* <ScrollArea className="w-full"> */}
        <div className="flex flex-row w-[var(--container-width)] justify-center overflow-hidden">
        <SidebarProvider open={sidebarOpen} className="w-full">
          <SidebarInset>
          
            <div className="flex flex-col overflow-hidden w-full sticky">
              <DataTableInfinite
                className="overflow-hidden w-full"
                columns={columns}
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
                rowEntrySidebarComponent={(props: {selectedRow: ColumnSchema | undefined, table: Table<ColumnSchema>}) => {
                  return (
                    <DocumentChunkTableSheetDetails
                      // TODO: make it dynamic via renderSheetDetailsContent
                      title={(props.selectedRow as ColumnSchema | undefined)?.document_name}
                      titleClassName="font-mono"
                      table={props.table}
                      onDownload={() => {
                        if (!props.selectedRow) return;
                        openDocument({
                          auth: userData?.auth as string,
                          document_id: resolvedParams["slug"][1]
                        });
                      }}
                    >
                      <DocumentChunkSheetDetailsContent
                        data={props.selectedRow as ColumnSchema}
                        filterRows={totalDBRowCount}
                      />
                    </DocumentChunkTableSheetDetails>
                  )
                }}
                setControlsOpen={setSidebarOpen}
              />
            </div>
          </SidebarInset>
          <CollectionSidebar
            collapsible="motion" 
            side="right"
            user_auth={userData as userDataType}
            document_id={resolvedParams["slug"][1]}
            collection_name={collectionTitle}
            set_collection_name={setCollectionTitle}
          />
        </SidebarProvider>
          
        </div>
      {/* </ScrollArea> */}
    </div>
  );
}
