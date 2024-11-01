"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ColumnDef } from "@tanstack/react-table";
import { Check, LucideLoader2, Minus, X } from "lucide-react";
// import type { ColumnSchema } from "./schema";
// import ColumnSchema
// import { format, set } from "date-fns";
import { getStatusColor } from "@/lib/request/status-code";
// import { regions } from "@/constants/region";
import {
  getTimingColor,
  getTimingLabel,
  getTimingPercentage,
  timingPhases,
} from "@/lib/request/timing";
import { cn } from "@/lib/utils";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { DataTableColumnHeader } from "@/components/data-table/data-table-column-header";
import TextWithTooltip from "@/components/custom/text-with-tooltip";
import { UTCDate } from "@date-fns/utc";
// import { file_size_as_string } from "@/app/collection/[[...slug]]/page";
import { useEffect, useState } from "react";
import { DataTableInfinite } from "@/components/custom/data_table_infinite/data-table-infinite";
import { z } from "zod";
import { fetchCollection } from "@/hooks/querylakeAPI";
import { useContextAction } from "@/app/context-provider";
import { useInfiniteQuery } from "@tanstack/react-query";
// import { createParser, createSerializer, createSearchParamsCache, parseAsArrayOf, parseAsBoolean, parseAsInteger, parseAsString, parseAsTimestamp, useQueryStates } from "nuqs";
import {
  createParser,
  createSearchParamsCache,
  createSerializer,
  parseAsArrayOf,
  parseAsBoolean,
  parseAsInteger,
  parseAsString,
  parseAsStringLiteral,
  parseAsTimestamp,
  type inferParserType,
} from "nuqs/server";
import { ARRAY_DELIMITER, RANGE_DELIMITER, SLIDER_DELIMITER, SORT_DELIMITER } from "@/lib/delimiters";
// import { produce } from 'immer';

// // import { SearchParamsType, searchParamsSerializer } from "./search-params";
// import { infiniteQueryOptions, keepPreviousData } from "@tanstack/react-query";
// import { Percentile } from "@/lib/request/percentile";
// import { useQueryStates } from "nuqs";

// export type MakeArray<T> = {
//   [P in keyof T]: T[P][];
// };

// const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

// export const REGIONS = ["ams", "fra", "gru", "hkg", "iad", "syd"] as const;

// export const regions: Record<string, string> = {
//   ams: "Amsterdam",
//   fra: "Frankfurt",
//   gru: "Sao Paulo",
//   hkg: "Hong Kong",
//   iad: "Washington D.C.",
//   syd: "Sydney",
// };


// export type InfiniteQueryMeta = {
//   totalRowCount: number;
//   filterRowCount: number;
//   totalFilters: MakeArray<ColumnSchema>;
//   currentPercentiles: Record<Percentile, number>;
//   chartData: { timestamp: number; [key: string]: number }[];
// };




// export interface CollectionDocument {
//   id: string;
//   file_name: string;
//   creation_timestamp: number;
//   integrity_sha256: string;
//   size_bytes: number;
//   encryption_key_secure: string;
//   organization_document_collection_hash_id: string | null;
//   user_document_collection_hash_id: string;
//   global_document_collection_hash_id: string | null;
//   toolchain_session_id: string | null;
//   website_url: string | null;
//   blob_id: string;
//   blob_dir: string;
//   finished_processing: boolean;
//   md: Record<string, any>;
//   bm25_score: number;
// }


// export const columnSchema = z.object({
//   id: z.string(),
//   file_name: z.string(),
//   creation_timestamp: z.number(),
//   integrity_sha256: z.string(),
//   size_bytes: z.number(),
//   encryption_key_secure: z.string(),
//   organization_document_collection_hash_id: z.string().nullable(),
//   user_document_collection_hash_id: z.string(),
//   global_document_collection_hash_id: z.string().nullable(),
//   toolchain_session_id: z.string().nullable(),
//   website_url: z.string().nullable(),
//   blob_id: z.string(),
//   blob_dir: z.string(),
//   finished_processing: z.boolean(),
//   md: z.record(z.any()),
//   bm25_score: z.number()
// });

// export const parseAsSort = createParser({
//   parse(queryValue) {
//     const [id, desc] = queryValue.split(SORT_DELIMITER);
//     if (!id && !desc) return null;
//     return { id, desc: desc === "desc" };
//   },
//   serialize(value) {
//     return `${value.id}.${value.desc ? "desc" : "asc"}`;
//   },
// });


// export const searchParamsParser = {
//   // CUSTOM FILTERS
//   file_name: parseAsString,
//   creation_timestamp: parseAsArrayOf(parseAsTimestamp, RANGE_DELIMITER),
//   size_bytes: parseAsArrayOf(parseAsInteger, SLIDER_DELIMITER),
//   finished_processing: parseAsArrayOf(parseAsBoolean, ARRAY_DELIMITER),
  
//   // REQUIRED FOR SORTING & PAGINATION
//   sort: parseAsSort,
//   size: parseAsInteger.withDefault(30),
//   start: parseAsInteger.withDefault(0),
  
//   // REQUIRED FOR SELECTION
//   id: parseAsString,
// };

// export const searchParamsCache = createSearchParamsCache(searchParamsParser);
// export const searchParamsSerializer = createSerializer(searchParamsParser);
// export type SearchParamsType = inferParserType<typeof searchParamsParser>;

// export const dataOptions = (search: SearchParamsType) => {
//   return infiniteQueryOptions({
//     queryKey: ["data-table", searchParamsSerializer({ ...search })], // remove uuid as it would otherwise retrigger a fetch
//     queryFn: async ({ pageParam = 0 }) => {
//       const start = (pageParam as number) * search.size;
//       const serialize = searchParamsSerializer({ ...search, start });
//       const response = await fetch(`/infinite/api${serialize}`);
//       return response.json() as Promise<{
//         data: ColumnSchema[];
//         meta: InfiniteQueryMeta;
//       }>;
//     },
//     initialPageParam: 0,
//     getNextPageParam: (_lastGroup, groups) => groups.length,
//     refetchOnWindowFocus: false,
//     placeholderData: keepPreviousData,
//   });
// };


// export type ColumnSchema = z.infer<typeof columnSchema>;

// export const columns: ColumnDef<ColumnSchema>[] = [
//   {
//     id: "file_name",
//     accessorKey: "file_name",
//     header: "Name",
//     cell: ({ row }) => {
//       const value = row.getValue("file_name") as string;
//       return (
//         <TextWithTooltip className="font-mono max-w-[85px]" text={value} />
//       );
//     },
//     meta: {
//       label: "Name",
//     },
//   },
//   {
//     accessorKey: "creation_timestamp",
//     header: ({ column }) => (
//       <DataTableColumnHeader column={column} title="Created" />
//     ),
//     cell: ({ row }) => {
//       const date = new Date((row.getValue("creation_timestamp") as number)*1000);
//       return (
//         <HoverCard openDelay={0} closeDelay={0}>
//           <HoverCardTrigger asChild>
//             <div className="font-mono whitespace-nowrap">
//               {format(date, "LLL dd, y HH:mm:ss")}
//             </div>
//           </HoverCardTrigger>
//           <HoverCardContent
//             side="right"
//             align="start"
//             alignOffset={-4}
//             className="p-2 w-auto z-10"
//           >
//             <dl className="flex flex-col gap-1">
//               <div className="flex gap-4 text-sm justify-between items-center">
//                 <dt className="text-muted-foreground">Timestamp</dt>
//                 <dd className="font-mono truncate">{date.getTime()}</dd>
//               </div>
//               <div className="flex gap-4 text-sm justify-between items-center">
//                 <dt className="text-muted-foreground">UTC</dt>
//                 <dd className="font-mono truncate">
//                   {format(new UTCDate(date), "LLL dd, y HH:mm:ss")}
//                 </dd>
//               </div>
//               <div className="flex gap-4 text-sm justify-between items-center">
//                 <dt className="text-muted-foreground">{timezone}</dt>
//                 <dd className="font-mono truncate">
//                   {format(date, "LLL dd, y HH:mm:ss")}
//                 </dd>
//               </div>
//             </dl>
//           </HoverCardContent>
//         </HoverCard>
//       );
//     },
//     filterFn: "inDateRange",
//     meta: {
//       // headerClassName: "w-[182px]",
//     },
//   },
//   {
//     accessorKey: "size_bytes",
//     header: "Size",
//     cell: ({ row }) => {
//       const value = row.getValue("size_bytes");
//       if (typeof value === "undefined") {
//         return <Minus className="h-4 w-4 text-muted-foreground/50" />;
//       }
//       if (typeof value === "number") {
//         const colors = getStatusColor(value);
//         return <div className={`${colors.text} font-mono`}>{file_size_as_string(value)}</div>;
//       }
//       return <div className="text-muted-foreground">{`${value}`}</div>;
//     }
//   },
//   {
//     // TODO: make it a type of MethodSchema!
//     accessorKey: "finished_processing",
//     header: "Processing",
//     cell: ({ row }) => {
//       const value = row.getValue("finished_processing") as boolean;
//       return (
//         <>
//           {value ? (
//             <div className="h-4 bg-accent flex flex-row space-x-1 text-nowrap px-2 rounded-full">
//               <div className='h-auto flex flex-col justify-center'>
//                 <div style={{
//                   animation: 'spin 1.5s linear infinite'
//                 }}>
//                   <LucideLoader2 className="w-3 h-3 text-primary" />
//                 </div>
//               </div>
//               <p className='text-xs h-auto flex flex-col justify-center'>Processing</p>
//             </div>
//           ):(
//             <></>
//           )}
//         </>
//       );
//     }
//   },
// ];




const COLLECTION_ID = "wAloo9uVIwU9IhidVvU2MR0JXKOWi5A6";

export default function TestPage() {
  const {
    userData,
    // refreshCollectionGroups,
  } = useContextAction();

  const [totalDBRowCount, setTotalDBRowCount] = useState(0);
  // const [flatData, setFlatData] = useState<ColumnSchema[]>([]);
  // const [isFetching, setIsFetching] = useState(false);

  useEffect(() => {
    // setIsFetching(true);
    fetchCollection({
      auth: userData?.auth as string,
      collection_id: COLLECTION_ID,
      onFinish: (data) => {
        if (data !== undefined) {
          setTotalDBRowCount(data.document_count);
        }
        // setIsFetching(false);
      }
    })
  }, []);


  // const [search] = useQueryStates(searchParamsParser);
  // const { data, isFetching, isLoading, fetchNextPage } = useInfiniteQuery(
  //   dataOptions(search)
  // );

  // const flatData = React.useMemo(
  //   () => data?.pages?.flatMap((page) => page.data ?? []) ?? [],
  //   [data?.pages]
  // );

  // const lastPage = data?.pages?.[data?.pages.length - 1];
  // // const totalDBRowCount = lastPage?.meta?.totalRowCount;
  // const filterDBRowCount = lastPage?.meta?.filterRowCount;
  // const totalFilters = lastPage?.meta?.totalFilters;
  // const currentPercentiles = lastPage?.meta?.currentPercentiles;
  // const chartData = lastPage?.meta?.chartData;
  // const totalFetched = flatData?.length;

  // const { sort, start, size, ...filter } = search;

  



  return (
    <div className="w-full h-[calc(100vh)] flex flex-row justify-center">
      <ScrollArea className="w-full">
        <div className="flex flex-row justify-center pt-10">
          <div className="max-w-[85vw] md:max-w-[70vw] lg:max-w-[45vw]">
            <h1>Test Page</h1>
            <h1>Total Docs: {totalDBRowCount}</h1>
          </div>
        </div>
      </ScrollArea>
    </div>
  );


  // return (
  //   <div className="w-full h-[calc(100vh)] flex flex-row justify-center">
  //     <ScrollArea className="w-full">
  //       <div className="flex flex-row justify-center pt-10">
  //         <div className="max-w-[85vw] md:max-w-[70vw] lg:max-w-[45vw]">
  //         <DataTableInfinite
  //           columns={columns}
  //           data={flatData}
  //           totalRows={totalDBRowCount}
  //           filterRows={filterDBRowCount}
  //           totalRowsFetched={totalFetched}
  //           defaultColumnFilters={Object.entries(filter)
  //             .map(([key, value]) => ({
  //               id: key,
  //               value,
  //             }))
  //             .filter(({ value }) => value ?? undefined)}
  //           defaultColumnSorting={sort ? [sort] : undefined}
  //           // defaultRowSelection={search.uuid ? { [search.uuid]: true } : undefined}
  //           // filterFields={filterFields}
  //           isFetching={isFetching}
  //           isLoading={isLoading}
  //           fetchNextPage={fetchNextPage}
  //         />
  //         </div>
  //       </div>
  //     </ScrollArea>
  //   </div>
  // );
}