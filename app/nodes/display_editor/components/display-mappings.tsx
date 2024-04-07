import { Skeleton } from "@/registry/default/ui/skeleton";
import { 
	DISPLAY_COMPONENTS, 
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
import RouteSetter from "./route-setter";
import RouteAddSheet from "./route-add-sheet";
import SheetDemo from "@/registry/default/example/sheet-demo";
import InputComponentSheet from "./input-component-sheet";
import { BreadcrumbEllipsis } from "@/registry/default/ui/breadcrumb";

export function DisplayComponentSkeletonMapper({
	info,
	children
}:{
	info: contentMapping,
	children?: React.ReactNode
}) {
	switch(info.display_as) {
		// Display Components
		case "chat":
			return (
				<div className="flex flex-row space-x-4 w-auto	">
					<div>
						<Skeleton className="rounded-full w-10 h-10"/>
					</div>
					<div className="flex-grow flex flex-col space-y-3">
						{Array(10).fill(0).map((_, i) => (
							<Skeleton key={i} className="rounded-full w-auto h-3"/>
						))}
					</div>
				</div>
			);
		case "markdown":
			return (
				<div className="flex-grow flex flex-col space-y-3">
					{Array(10).fill(0).map((_, i) => (
						<Skeleton key={i} className="rounded-full w-auto h-3"/>
					))}
				</div>
			);
		case "text":
			return (
				<div className="flex-grow flex flex-col space-y-3">
					{Array(10).fill(0).map((_, i) => (
						<Skeleton key={i} className="rounded-full w-auto h-3"/>
					))}
				</div>
			);
		case "graph":
			return (
				<div>
					<h2>{"Graph (Not Implemented)"}</h2>
				</div>
			);


		// Input Components
		case "chat_input":
		case "file_upload":
			return (
				<Skeleton className="rounded-md h-10 border-dashed border-[2px] border-primary/50 flex flex-col justify-center">
					{children}
				</Skeleton>
			);
	}
}

export default function DisplayMappings({
	info,
	onDelete,
	onRouteSet,
}:{
	info: contentMapping,
	onDelete: () => void,
	onRouteSet: (route: (string | number)[]) => void
}) {

	return (
		<>
		{(DISPLAY_COMPONENTS.includes(info.display_as as displayComponents)) ? ( // Display Component
			<div className="flex flex-col w-auto pt-4 space-y-2">
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
				<DisplayComponentSkeletonMapper info={info}/>
			</div>
		) : ( // Input Component
			<div className="flex flex-row space-x-2 w-auto">
				

				<DisplayComponentSkeletonMapper info={info}>
					<div className="flex flex-row space-x-1">
					<InputComponentSheet
						value={info as inputMapping}
						type={info.display_as as inputComponents}
						onChange={(config) => {}}
						onDelete={onDelete}
					>
						{/* <Button size="icon" variant="ghost"> */}
						<div className="w-10 flex flex-col justify-center">
							<div className="w-auto flex flex-row justify-center">
								<BreadcrumbEllipsis className="w-4 h-4 text-primary" />
							</div>
						</div>
						{/* </Button> */}
					</InputComponentSheet>
					<p className="w-auto text-center select-none h-auto flex flex-col justify-center">
						{info.display_as}
					</p>
					{/* <Button size="icon" variant="ghost" onClick={onDelete}> */}
					<div className="w-10 flex flex-col justify-center">
						<div className="w-auto flex flex-row justify-center">
							<Trash2 className="w-4 h-4 text-primary" onClick={onDelete} />
						</div>
					</div>
					{/* </Button> */}
					</div>
				</DisplayComponentSkeletonMapper>
				
				
			</div>
		)}
		</>
	)
}