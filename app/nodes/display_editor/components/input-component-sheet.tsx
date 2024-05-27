"use client";
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
import { INPUT_COMPONENT_FIELDS, configEntry, configEntryFieldType, inputComponentConfig, inputComponents, inputEvent, inputMapping } from "@/types/toolchain-interface"
import { ChevronDown, ChevronUp, Plus, Trash2 } from "lucide-react"
import { useEffect, useState, Fragment, useCallback, ChangeEvent, use } from "react"
import CompactInput from "@/registry/default/ui/compact-input"
import { HoverTextDiv } from "@/registry/default/ui/hover-text-div";
import { Separator } from "@/registry/default/ui/separator";
import { Textarea } from "@/registry/default/ui/textarea";
import { Toggle } from "@/registry/default/ui/toggle";

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
	
	const [componentConfigFields, setComponentConfigFields] = useState<inputComponentConfig>(INPUT_COMPONENT_FIELDS[type]);
  // const 

  const updateConfigFields = (input_mapping_value : inputMapping) => {
    let newConfigFields : {[key: string]: configEntry} = {};
    (INPUT_COMPONENT_FIELDS[type].config || []).forEach((c : configEntryFieldType) => {
      newConfigFields[c.name] = {name : c.name, value: c.default};
    });
    input_mapping_value.config.forEach((c : configEntry) => {
      newConfigFields[c.name] = {name : c.name, value: c.value};
    });

    return {
      ...input_mapping_value,
      config: (INPUT_COMPONENT_FIELDS[type].config || []).map((c : configEntryFieldType) => (newConfigFields[c.name]))
    };
  }

  const [actingValue, setActingValue] = useState<inputMapping>(updateConfigFields(JSON.parse(JSON.stringify(value)) as inputMapping));

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

  const setConfigValue = (p : boolean | string | number, index : number) => {
    const field_name = (INPUT_COMPONENT_FIELDS[type].config || [])[index].name;
    if (!field_name) return;

    setActingValue((oldValue : inputMapping) => {return {
      ...oldValue, 
      config: [
        ...oldValue.config.slice(0, index),
        {name: field_name, value: p},
        ...oldValue.config.slice(index+1)
      ]
    }});
  };

	useEffect(() => {setComponentConfigFields(INPUT_COMPONENT_FIELDS[type])}, [type]);
	useEffect(() => {resetActingValue()}, [value]);
  useEffect(() => {console.log("Acting Value:", actingValue)}, [actingValue]);

  
	return (
		<Sheet>
			<SheetTrigger asChild>
				{children}
			</SheetTrigger>
			<SheetContent className="h-full flex flex-col" onContextMenu={(e) => {e.preventDefault()}}>
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
					<div className="h-10 flex flex-row w-full justify-between">
						<Label className="h-full flex flex-col justify-center">Hooks</Label>
						<DropdownMenu>
							<DropdownMenuTrigger className="flex items-center gap-1">
								{/* <Button variant={"ghost"} className="py-0 h-full"> */}
									<Plus className="w-4 h-4 text-primary"/>
								{/* </Button> */}
							</DropdownMenuTrigger>
							<DropdownMenuContent align="start">
								{componentConfigFields.hooks.map((hook, index) => (
									<DropdownMenuItem key={index} onClick={() => {
										setHook({
                      hook: hook, 
                      target_event: "", 
                      fire_index: Math.max(...actingValue.hooks.map((e) => e.fire_index), 0) + 1,
                      target_route: "", 
                      store: false
                    }, 
                    actingValue.hooks.length);
									}}>{hook}</DropdownMenuItem>
								))}
							</DropdownMenuContent>
						</DropdownMenu>
					</div>
				</div>
				<ScrollArea className="flex-grow rounded-md border-[2px] border-secondary">
					<div className="p-2 pr-4 flex flex-col space-y-4">
						{actingValue.hooks.map((hookLocal, index) => (
							<Fragment key={index}>
							<div className="flex flex-wrap justify-between space-y-2">
								<p id="Hook Title" className="pb-1 pl-1 h-auto flex flex-col justify-center pt-2">{hookLocal.hook}</p>

                <HoverTextDiv hint="Order of hook firing. Can be used to fire inputs together." className="flex flex-row gap-2">
                  <p className="flex flex-col justify-center w-8 text-right"><strong>{hookLocal.fire_index}</strong></p>
                  <div className="flex flex-col justify-center">
                    <Button className="p-0 m-0 h-4 w-6" variant="ghost" onClick={() => {
                      const newIndex = (hookLocal.fire_index) % (actingValue.hooks.length);
                      setHook({...hookLocal, fire_index: newIndex + 1}, index);
                    }}>
                      <ChevronUp className="w-4 h-4 text-primary"/>
                    </Button>
                    <Button className="p-0 m-0 h-4 w-6" variant="ghost" onClick={() => {
                      const newIndex = (hookLocal.fire_index - 2 + actingValue.hooks.length) % (actingValue.hooks.length); 
                      setHook({...hookLocal, fire_index: newIndex + 1}, index);
                    }}>
                      <ChevronDown className="w-4 h-4 text-primary"/>
                    </Button>
                  </div>
                </HoverTextDiv>

								<div id="Store and Delete" className="flex flex-row space-x-1">

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
								<Input
                  className="flex-shrink min-w-1/2"
									value={hookLocal.target_event} 
									onChange={(event) => {
										setHook({...hookLocal, target_event: event.target.value}, index);
									}}
									placeholder="Target Event"
									spellCheck={false}
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
									spellCheck={false}
								/>
							</div>
							{/* <div className="flex flex-row space-x-2"> */}
							{/* </div> */}
              {(index !== actingValue.hooks.length - 1) && <Separator/>}
							</Fragment>
						))}
					</div>
				</ScrollArea>
        <Label className="flex-shrink flex flex-col justify-center">Config</Label>
        <ScrollArea className="flex-5 rounded-md border-[2px] border-secondary">
          <div className="flex flex-wrap p-2 pr-4 gap-x-2 gap-y-4">
            {componentConfigFields.config && (
              <>
                {componentConfigFields.config.map((configEntry : configEntryFieldType, index : number) => (
                  <Fragment key={index}>
                    {configEntry.type === "boolean"  && (
                      <Toggle className="max-w-[45%]" pressed={actingValue.config[index]?.value as boolean} onPressedChange={(p : boolean) => {
                        setConfigValue(p, index);
                      }}>
                        {configEntry.name}
                      </Toggle>
                    )}
                    {configEntry.type === "string"  && (
                      <CompactInput className="w-[45%]" value={actingValue.config[index]?.value as string} placeholder={configEntry.name} onChange={(e: ChangeEvent<HTMLInputElement>) => {
                        setConfigValue(e.target.value, index);
                      }}/>
                    )}
                    {configEntry.type === "long_string"  && (
                      // <CompactInput className="w-[45%]" placeholder={configEntry.name}/>
                      <Textarea className="w-full resize-none" spellCheck={false} value={actingValue.config[index]?.value as string} placeholder={configEntry.name}
                        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
                          setConfigValue(e.target.value, index);
                      }}/>
                    )}
                    {configEntry.type === "number"  && (
                      <CompactInput className="w-[45%]" value={actingValue.config[index]?.value as number} placeholder={configEntry.name} type="number" onChange={(e: ChangeEvent<HTMLInputElement>) => {
                        // console.log("Number field set to:", [parseFloat(e.target.value)]);
                        setConfigValue(parseFloat(e.target.value), index);
                      }}/>
                    )}
                  </Fragment>
                ))}
              </>
            )}
          </div>
        </ScrollArea>

				<SheetFooter>
					<SheetClose asChild>
						<Button type="submit" className="w-full" onClick={() => onChange(actingValue)}>Save</Button>
					</SheetClose>
				</SheetFooter>
			</SheetContent>
		</Sheet>
	)
}