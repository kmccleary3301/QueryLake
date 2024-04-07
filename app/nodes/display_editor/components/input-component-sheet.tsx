import { Button } from "@/registry/default/ui/button"
import { Input } from "@/registry/default/ui/input"
import { Label } from "@/registry/default/ui/label"
import { ScrollArea } from "@/registry/default/ui/scroll-area"
import {
	Sheet,
	SheetClose,
	SheetContent,
	SheetDescription,
	SheetFooter,
	SheetHeader,
	SheetTitle,
	SheetTrigger,
} from "@/registry/default/ui/sheet"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
	DropdownMenuItem
} from "@/registry/default/ui/dropdown-menu"
import { ToggleGroup, ToggleGroupItem } from "@/registry/default/ui/toggle-group"
import { INPUT_COMPONENT_FIELDS, configEntryFieldType, inputComponentConfig, inputComponents, inputEvent, inputMapping } from "@/types/toolchain-interface"
import { Plus, Trash2 } from "lucide-react"
import { useEffect, useRef, useState, Fragment, useCallback, ChangeEvent } from "react"
import CompactInput from "@/registry/default/ui/compact-input"

export default function InputComponentSheet({
	value,
	type,
	onChange,
	onDelete,
	children
}:{
	value: inputMapping,
	type: inputComponents,
	onChange: (config : inputMapping) => void,
	onDelete: () => void,
	children: React.ReactNode
}) {
	const [actingValue, setActingValue] = useState<inputMapping>(JSON.parse(JSON.stringify(value)));
	const [componentConfig, setComponentConfig] = useState<inputComponentConfig>(INPUT_COMPONENT_FIELDS[type]);
	const resetActingValue = useCallback(() => {setActingValue(JSON.parse(JSON.stringify(value)))}, [value]);
	const setHook = useCallback((hook : inputEvent, index : number) => {
		setActingValue({
			...actingValue, 
			hooks: [
				...actingValue.hooks.slice(0, index),
				hook,
				...actingValue.hooks.slice(index+1)
			]
		});
	}, [actingValue]);


	useEffect(() => {setComponentConfig(INPUT_COMPONENT_FIELDS[type])}, [type]);
	useEffect(() => {resetActingValue()}, [value]);

	return (
		<Sheet onOpenChange={resetActingValue}>
			<SheetTrigger asChild>
				{children}
			</SheetTrigger>
			<SheetContent className="h-full flex flex-col">
				<SheetHeader>
					<SheetTitle>{`Configure \`${type}\` Component`}</SheetTitle>
					<SheetDescription>
						Configure input component for toolchain interface.
					</SheetDescription>
				</SheetHeader>
				<div className="flex flex-col space-y-2">
				{/* <div className='pt-2 pb-2 flex flex-row space-x-1'> */}
					<CompactInput 
						onChange={(e : ChangeEvent<HTMLInputElement>) => setActingValue({...actingValue, tailwind: e.target.value})}
						placeholder='Component Tailwind' 
						className='h-10 w-full'
						defaultValue={actingValue.tailwind}
					/>
				{/* </div> */}

					<div className="h-10 flex flex-row w-full justify-between">
						<Label className="h-full flex flex-col justify-center">Hooks</Label>
						<DropdownMenu>
							<DropdownMenuTrigger className="flex items-center gap-1">
								{/* <Button variant={"ghost"} className="py-0 h-full"> */}
									<Plus className="w-4 h-4 text-primary"/>
								{/* </Button> */}
							</DropdownMenuTrigger>
							<DropdownMenuContent align="start">
								{componentConfig.hooks.map((hook, index) => (
									<DropdownMenuItem key={index} onClick={() => {
										setHook({hook: hook, target_event: "", target_route: "", store: false}, actingValue.hooks.length);
									}}>{hook}</DropdownMenuItem>
								))}
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
				</div>
				<ScrollArea className="flex-grow rounded-md border-[2px] border-secondary">
					<div className="p-2 flex flex-col space-y-2">
						{actingValue.hooks.map((hookLocal, index) => (
							<Fragment key={index}>
							<div className="flex flex-row justify-between h-10">
								<p className="pb-1 pl-1 h-auto flex flex-col justify-center pt-2">{hookLocal.hook}</p>
								<div className="flex flex-row space-x-1">
									<ToggleGroup
										type="single"
										onValueChange={(value : "" | "store") => {
											setHook({...hookLocal, store: (value === "store")}, index);
										}}
										className='flex flex-row justify-between'
										value={(hookLocal.store) ? "store" : ""}
									>
										<ToggleGroupItem value="store" aria-label="Align center" variant={"outline"}>
											Store
										</ToggleGroupItem>
									</ToggleGroup>

									<Button size="icon" variant="ghost" onClick={() => {
										setActingValue({
											...actingValue, 
											hooks: [
												...actingValue.hooks.slice(0, index),
												...actingValue.hooks.slice(index+1)
											]
										});
									}}>
										<Trash2 className="w-4 h-4 text-primary" />
									</Button>
								</div>
							</div>
							<div className="flex flex-row space-x-2">
								<Input
									value={hookLocal.target_event} 
									onChange={(event) => {
										setHook({...hookLocal, target_event: event.target.value}, index);
									}}
									placeholder="Target Event"
								/>
								<Input
									value={hookLocal.target_route} 
									onChange={(event) => {
										setActingValue({
											...actingValue, 
											hooks: [
												...actingValue.hooks.slice(0, index),
												{...hookLocal, target_route: event.target.value},
												...actingValue.hooks.slice(index+1)
											]
										});
									}}
									placeholder="Target Route"
								/>
							</div>
							</Fragment>
						))}
					</div>
				</ScrollArea>
				<div className="flex-4 flex flex-col space-y-1">
				{componentConfig.config && (
					<>
						<Label className="h-full">Config</Label>
						{componentConfig.config.map((configEntry : configEntryFieldType, index) => (
							<Fragment key={index}>
								{configEntry.type === "boolean"  && (
									<ToggleGroup
										type="single"
										// onValueChange={(value : boolean) => {
										// 	setEntryType((value === "number") ? "number" : "string");
										// }}
										// className='flex flex-row justify-between'
										// value={(entryType === "number") ? "number" : ""}
									>
										<ToggleGroupItem value="number" aria-label="Align center" variant={"outline"}>
											{configEntry.name}
										</ToggleGroupItem>
									</ToggleGroup>
								)}
								{configEntry.type === "string"  && (
									<CompactInput placeholder={configEntry.name}/>
								)}
							</Fragment>
						))}
					</>
				)}
				</div>

				<SheetFooter>
					<SheetClose asChild>
						<Button type="submit" className="w-full" onClick={() => onChange(actingValue)}>Save</Button>
					</SheetClose>
				</SheetFooter>
			</SheetContent>
		</Sheet>
	)
}