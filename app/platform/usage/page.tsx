"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useState } from "react";
import { useContextAction } from "@/app/context-provider";

import { Bar, BarChart, XAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import { QuerylakeFetchUsage, UsageEntryType } from "@/hooks/querylakeAPI";

export const description = "A stacked bar chart with a legend"

const chartData = [
  { date: "2024-07-15", running: 450 },
  { date: "2024-07-16", running: 380, swimming: 420 },
  { date: "2024-07-17", running: 520, swimming: 120 },
  { date: "2024-07-18", running: 140, swimming: 550 },
  { date: "2024-07-19", running: 600, swimming: 350 },
  { date: "2024-07-20", running: 480, swimming: 400 },
]

const chartConfig = {
  running: {
    label: "Running",
    color: "hsl(var(--chart-1))",
  },
  swimming: {
    label: "Swimming",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig


type UsageGraphData = {
	date: string,
	start_time: number
}




type UsageInfo = {
  tokens?: number
  input_tokens?: number
  output_tokens?: number
}

const USAGE_ENTRY_KEYS = ["tokens", "input_tokens", "output_tokens"];

type TaggedUsageInfo = { path: string } & UsageInfo;
type DatedUsageInfo = { date: string } & UsageInfo;
type DatedTaggedUsageInfo = { date: string } & TaggedUsageInfo;
type ModelComposition = {
  model: string,
  time_data: DatedUsageInfo[]
}

type CategorizedSeries = {
  category: string,
  models: ModelComposition[]
}

function TestGraph({
  data
}:{
  data : ModelComposition
}) {
	return (
		<Card>
			<CardHeader>
				<CardTitle className="text-lg">{data.model}</CardTitle>
				<CardDescription>Model usage for {data.model}</CardDescription>
			</CardHeader>
			<CardContent>
				<ChartContainer config={{
          tokens: {
            label: "Tokens",
            color: "hsl(var(--chart-1))",
          },
          input_tokens: {
            label: "Input Tokens",
            color: "hsl(var(--chart-2))",
          },
          output_tokens: {
            label: "Output Tokens",
            color: "hsl(var(--chart-3))",
          }
        }}>
					<BarChart accessibilityLayer data={data.time_data}>
						<XAxis
							dataKey="date"
							tickLine={true}
							tickMargin={10}
							axisLine={true}
							tickFormatter={(value) => {
								return new Date(value).toLocaleDateString("en-US", {
									weekday: "short",
								})
							}}
						/>
						<Bar
							dataKey="tokens"
							stackId="a"
							fill="var(--color-tokens)"
							radius={[0, 0, 4, 4]}
						/>
            <Bar
							dataKey="input_tokens"
							stackId="a"
							fill="var(--color-input_tokens)"
							radius={[0, 0, 4, 4]}
						/>
            
						<Bar
							dataKey="output_tokens"
							stackId="a"
							fill="var(--color-output_tokens)"
							radius={[4, 4, 0, 0]}
						/>
						<ChartTooltip
              // wrapperClassName="w-[200px]"
              labelClassName="pr-10"
							content={<ChartTooltipContent indicator="line" />}
							cursor={false}
							defaultIndex={1}
						/>
					</BarChart>
				</ChartContainer>
			</CardContent>
		</Card>
	)
}

const get_usage_from_object = (usage_obj: object) => {
  let usage_entries : TaggedUsageInfo[] = [];
  let usage_entry : TaggedUsageInfo = {path: ""};
  for (const [key, value] of Object.entries(usage_obj)) {
    if (USAGE_ENTRY_KEYS.includes(key) && typeof value === 'number') {
	    usage_entry[key as keyof UsageInfo] = value;
      // usage_entries.push({ [key]: value });
    }
    

  }
  if (Object.keys(usage_entry).length > 1) {
    usage_entries.push(usage_entry);
    return usage_entries;
  }
  for (const [key, value] of Object.entries(usage_obj)) {
    if (typeof value === 'object') {
      let usage_entries_retrieved = get_usage_from_object(value).map((e : TaggedUsageInfo) => {
        return {...e, path: (e.path.length > 0)?(key + "/" + e.path):key};
      });
      usage_entries.push(...usage_entries_retrieved);
    }
  }
  return usage_entries;
}

export default function UsagePage(){

	const { userData } = useContextAction();
	const [currentMonth, setCurrentMonth] = useState(new Date().toISOString().slice(0, 7));
  const [currentData, setCurrentData] = useState<CategorizedSeries[]>([]);


	const month_string_to_unix_time = (month: string) => {
		const date_time = new Date(month + "-01T00:00:00Z").getTime() / 1000;
		return date_time;
	}

  const unix_time_to_string = (unix_time: number, granularity: "month" | "day" | "hour") => {
    const date_time = new Date(unix_time * 1000);
    return date_time.toISOString().slice(0, granularity === "month" ? 7 : (granularity === "day" ? 10 : 13));
  }

	const fastForwardMonths = (month: string, months: number) => {
		const newDate = new Date(month + "-01T00:00:00Z");
		newDate.setMonth(newDate.getMonth() + months);
		return newDate.getTime()/1000;
	};

	useEffect(() => {
		QuerylakeFetchUsage({
			auth: userData?.auth as string,
			window: "day",
			start_time: month_string_to_unix_time(currentMonth),
			end_time: fastForwardMonths(currentMonth, 1),
			onFinish: (data: UsageEntryType[] | false) => {
        console.log("Got data:", data);
				if (data === false) { return; }
        let all_info : DatedTaggedUsageInfo[] = [];
        data.forEach((entry : UsageEntryType) => {
          const usage_info : DatedTaggedUsageInfo[] = get_usage_from_object(entry.value).map((e : TaggedUsageInfo) => {
            return {...e, date: unix_time_to_string(entry.start_timestamp, "day")};
          });
          all_info.push(...usage_info);
        });
        // console.log("Usage Entries Extracted:", get_usage_from_object(data[0].value));
        let model_compositions : Map<string, Map<string, ModelComposition>> = new Map();
        for (const usage_entry of all_info) {
          const {path, ...usage_entry_data} = usage_entry;
          // const path = usage_entry.path;
          const path_parts = path.split("/");
          const category = path_parts.slice(0, path_parts.length-1).join("/");
          const model = path_parts[path_parts.length - 1];
          // const model = path;
          let inner_map = model_compositions.get(category) || new Map();
          const time_data = inner_map.get(model)?.time_data || [];
          time_data.push(usage_entry_data);
          inner_map.set(model, {model: model, time_data: time_data});
          model_compositions.set(category, inner_map);
        }
        const modelCompositionsList : CategorizedSeries[] = 
        Array.from(model_compositions.entries()).map(([category, modelsMap]) => ({
          category,
          models: Array.from(modelsMap.entries()).map(([model, composition]) => composition),
        }))
        setCurrentData(modelCompositionsList);
			}
		})
	}, []);

	return (

		<div className="w-full h-[calc(100vh)] flex flex-row justify-center">
			<ScrollArea className="w-full">
				<div className="flex flex-row justify-center">
					<div className="pt-10 w-[85vw] md:w-[70vw] flex flex-wrap justify-center gap-10">
            {currentData.map((category_entry, index) => (
              <div key={index} className="flex flex-col space-y-8">
                {/* <h1 className="text-4xl border-b-accent pb-2 border-b-4"><b>{category_entry.category}</b></h1> */}
                <div className="flex-wrap">
                  {category_entry.models.map((model_entry, index_2) => (
                    <div className="w-[450px] h-[450px]">
                      <TestGraph key={index_2} data={model_entry}/>
                    </div>
                  ))}
                </div>
              </div>
            ))}
						{/* <TestGraph/> */}
					</div>
				</div>
      </ScrollArea>
    </div>
	)
}