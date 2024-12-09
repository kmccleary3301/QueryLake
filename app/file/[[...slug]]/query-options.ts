import { infiniteQueryOptions, keepPreviousData } from "@tanstack/react-query";
import { ColumnSchema, MakeArray, searchParamsSerializer, SearchParamsType } from "./columns";
import { InfiniteQueryMeta } from "./columns";
import craftUrl from "@/hooks/craftUrl";

type SearchParams = {
  auth: string;
  collection_ids: string[];
  query: string;
  offset: number;
  limit: number;
  table: string;
  group_chunks?: boolean;
  sort_by?: string;
  sort_dir?: "ASC" | "DESC";
}


// export type InfiniteQueryMeta = {
//   totalRowCount: number;
//   filterRowCount: number;
//   totalFilters: MakeArray<ColumnSchema>;
//   currentPercentiles: Record<Percentile, number>;
//   chartData: { timestamp: number; [key: string]: number }[];
// };

export type DataFetcher = (params: SearchParams) => Promise<{
  data: ColumnSchema[];
  meta: InfiniteQueryMeta;
}>;


export const dataOptions = (
  search: SearchParamsType,
  auth: string,
  document_id: string,
  collection_id: string,
  fetcher: DataFetcher,
) => {
  return infiniteQueryOptions({
    queryKey: ["data-table", searchParamsSerializer({ ...search })],
    queryFn: async ({ pageParam = 0 }) => {
      const start = (pageParam as number) * search.size;
      const searchParams: SearchParams = {
        auth,
        collection_ids: [collection_id],
        query: `document_id:"${document_id}"`,
        offset: start,
        limit: search.size,
        table: 'document_chunk',
        group_chunks: false,
        sort_by: search.sort ? `${search.sort.id}` : "document_name",
        sort_dir: search.sort ? (search.sort.desc ? "DESC" : "ASC") : undefined,
      };
      return fetcher(searchParams);
    },
    initialPageParam: 0,
    getNextPageParam: (_lastGroup, groups) => groups.length,
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
  });
};
