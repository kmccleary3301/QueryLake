"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { DataTableInfinite } from "@/components/custom/data_table_infinite/data-table-infinite";
import { useContextAction } from "@/app/context-provider";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useQueryStates } from "nuqs";
import { useEffect, useMemo, useState } from "react";
import { columns, columnSchema, INFINITE_COLLECTION_ID, InfiniteQueryMeta, searchParamsParser, searchParamsSerializer } from "./columns";
import { DataFetcher, dataOptions } from "./query-options";
import { fetchCollection } from "@/hooks/querylakeAPI";
import craftUrl from "@/hooks/craftUrl";

const COLLECTION_ID = "wAloo9uVIwU9IhidVvU2MR0JXKOWi5A6";

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


export function Client({}) {
  const { userData } = useContextAction();
  const [totalDBRowCount, setTotalDBRowCount] = useState(0);

  useEffect(() => {
    if (!userData?.auth) return;
    
    fetchCollection({
      auth: userData.auth,
      collection_id: COLLECTION_ID,
      onFinish: (data) => {
        console.log("Collection Data", data);
        if (data?.document_count !== undefined) {
          setTotalDBRowCount(data.document_count);
        }
      }
    });
  }, [userData?.auth]);

  const [search] = useQueryStates(searchParamsParser);
  const { data, isFetching, isLoading, fetchNextPage } = useInfiniteQuery(
    dataOptions(
      search,
      userData?.auth as string,
      INFINITE_COLLECTION_ID,
      defaultFetcher
    )
  );

  const flatData = useMemo(
    () => data?.pages?.flatMap((page) => page.data ?? []) ?? [],
    [data?.pages]
  );

  const lastPage = data?.pages?.[data?.pages.length - 1];
  const filterDBRowCount = lastPage?.meta?.filterRowCount;
  const totalFetched = flatData?.length;

  const { sort, start, size, ...filter } = search;

  return (
    <div className="w-full h-[calc(100vh)] flex flex-row justify-center">
      {/* <ScrollArea className="w-full"> */}
        <div className="flex flex-row w-full justify-center">
          <div className="flex flex-col">
            <DataTableInfinite
              columns={columns}
              data={flatData}
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
