"use client";
import { Skeleton } from "@/registry/default/ui/skeleton";
import { 
	DISPLAY_COMPONENTS, 
	configEntriesMap, 
	contentMapping, 
	displayComponents, 
	displayMapping, 
	inputComponents, 
	inputMapping
} from "@/types/toolchain-interface";
import { Input } from "@/registry/default/ui/input";
import { 
	Trash2,
	Plus,
	CircleEllipsis
} from 'lucide-react';
import { Button } from "@/registry/default/ui/button";
import RouteSetter from "@/app/nodes/display_editor/components/route-setter";
import RouteAddSheet from "@/app/nodes/display_editor/components/route-add-sheet";
import SheetDemo from "@/registry/default/example/sheet-demo";
import InputComponentSheet from "@/app/nodes/display_editor/components/input-component-sheet";
import { BreadcrumbEllipsis } from "@/registry/default/ui/breadcrumb";



import ChatInput from '@/components/toolchain_interface/chat-input';
import Chat from '@/components/toolchain_interface/chat';
import CurrentEventDisplay from '@/components/toolchain_interface/current-event-display';
import FileUpload from '@/components/toolchain_interface/file-upload';
import Markdown from '@/components/toolchain_interface/markdown';
import Switch from '@/components/toolchain_interface/switch';
import Text from '@/components/toolchain_interface/text';
import "@/lib/sine-opacity.css";
import { INPUT_COMPONENT_FIELDS } from "@/types/toolchain-interface";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/registry/default/ui/hover-card";

export function DisplayComponentSkeletonMapper({
	info,
	children
}:{
	info: contentMapping,
	children?: React.ReactNode
}) {

  const getEffectiveConfig = (info : inputMapping) => {
    let effectiveConfig : configEntriesMap = new Map();
    const default_fields = INPUT_COMPONENT_FIELDS[info.display_as];
    if (default_fields.config) {
      for (const entry of default_fields.config) {
        effectiveConfig.set(entry.name, {name: entry.name, value: entry.default});
      }
    }
    for (const entry of info.config) {
      effectiveConfig.set(entry.name, entry);
    }

    return effectiveConfig;
  }

	switch(info.display_as) {
		
    case "chat":
      return (
        <Chat demo configuration={(info as displayMapping)}/>
      );

    case "current-event-display":
      return (
        <CurrentEventDisplay demo configuration={(info as displayMapping)}/>
      );

    case "markdown":
      return (
        <Markdown demo configuration={(info as displayMapping)}/>
      );

    case "text":
      return (
        <Text demo configuration={(info as displayMapping)}/>
      );

    case "chat-input":
      return (
        <ChatInput configuration={info}/>
      );

    case "file-upload":
      return (
        <FileUpload configuration={info}/>
      );

    case "switch":
      return (
        <Switch configuration={info} entriesMap={getEffectiveConfig(info)}/>
      );    
  }
}

export default function DisplayMappings({
	info,
	onDelete,
	setInfo,
}:{
	info: contentMapping,
	onDelete: () => void,
	setInfo: (value: contentMapping) => void
}) {

	const onRouteSet = (value: (string | number)[]) => {
		setInfo({...info, display_route: value} as displayMapping);
	}	

	return (
		<>
		{(DISPLAY_COMPONENTS.includes(info.display_as as displayComponents)) ? ( 
      // Display Component

			<div className="flex-grow flex flex-col pt-4 space-y-2">
				<div className="w-auto flex flex-row space-x-2 justify-between">
					<div className="flex-grow h-auto flex flex-col justify-center text-base">
						<div className="flex flex-row">
							Display as:
							<p className="underline pl-2">{" "+info.display_as}</p>
						</div>
					</div>
					<Button size="icon" variant="ghost" onClick={onDelete}>
						<Trash2 className="w-4 h-4 text-primary" />
					</Button>
				</div>
				<div className="w-auto flex flex-row space-x-2 min-h-10 justify-between">
					<div className="flex-grow h-auto flex flex-col justify-center">
						{((info as displayMapping).display_route.length > 0) ? (
							<RouteSetter onRouteSet={onRouteSet} route={(info as displayMapping).display_route}/>
						) : (
							<p className="text-primary/40 select-none h-auto flex flex-col justify-center">{"Add a state object route."}</p>
						)}
					</div>
					{/* <div className="pr-2"> */}
						<RouteAddSheet
							type={"string"}
							onChange={(value) => {
								onRouteSet([...(info as displayMapping).display_route, value]);
							}}
						>
							<Button size="icon" variant="ghost">
									<Plus className="w-4 h-4 text-primary" />
							</Button>
						</RouteAddSheet>
					{/* </div> */}
				</div>
        <div className="sine-opacity-med disabled pointer-events-none">
				  <DisplayComponentSkeletonMapper info={info}/>
        </div>
			</div>
		) : (
      // Input Component
			// <div className="flex flex-row space-x-2 w-auto">

      <div>

        <div className="group h-full relative inline-flex flex-col justify-center z-5">
          <div className="sine-opacity-med disabled pointer-events-none">
            <DisplayComponentSkeletonMapper info={info}/>
          </div>

          <div className="absolute h-full bg-primary/10 opacity-0 hover:opacity-100 rounded-r-[inherit] w-full hidden group-hover:flex group-hover flex-row-reverse justify-around pointer-events-auto">
            <div className="flex min-w-full rounded-lg flex-row px-2 gap-1 justify-between">
            <InputComponentSheet
              value={info as inputMapping}
              type={info.display_as as inputComponents}
              onChange={(value : inputMapping) => {
                setInfo(value);
              }}
              onDelete={onDelete}
            >
              <div className="h-auto flex flex-col justify-center">
                <Button variant={"transparent"} className="p-0 m-0">
                  <BreadcrumbEllipsis className="w-4 h-4 text-primary" />
                </Button>
              </div>
            </InputComponentSheet>
            <div className="w-10 flex flex-col justify-center">
              <Button variant={"transparent"} className="p-0 m-0" onClick={onDelete}>
                <Trash2 className="w-4 h-4 text-primary" />
              </Button>
            </div>
            </div>
          </div>
        </div>
			</div>
		)}
		</>
	)
}