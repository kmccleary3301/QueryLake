"use client"

import * as React from "react"
import { Check, ChevronsUpDown } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "./button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "./command"
import {
  Popover,
  PopoverContent,
  PopoverContentNoPortal,
  PopoverTrigger,
} from "./popover"
// import { ScrollArea } from "@radix-ui/react-scroll-area"
import { ScrollArea } from "./scroll-area"
import { HoverCardTrigger, HoverCard, HoverCardContent } from "./hover-card"

type valueType = {value: string, label: string, preview?: string};

export function ComboBox({
  values,
  onChange = () => {},
  placeholder = "Values...",
  searchPlaceholder = "Search...",
  defaultValue = undefined,
  value = "",
}:{
  values: valueType[],
  onChange?: (value: string, label: string) => void,
  placeholder?: string,
  searchPlaceholder?: string,
  defaultValue?: valueType | undefined,
  value?: string,
}) {
  const [open, setOpen] = React.useState(false)
  const [innerValue, setInnerValue] = React.useState(defaultValue?.value || value)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[200px] justify-between"
        >
          {innerValue
            ? values.find((e) => e.value === innerValue)?.label
            : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
          <CommandInput placeholder={searchPlaceholder} />
          <CommandEmpty>No framework found.</CommandEmpty>
          <CommandGroup>
            {values.map((e) => (
              <CommandItem
                key={e.value}
                value={e.value}
                onSelect={(currentValue) => {
                  setInnerValue(currentValue === innerValue ? "" : currentValue);
                  onChange(e.value, e.label);
                  setOpen(false)
                }}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    innerValue === e.value ? "opacity-100" : "opacity-0"
                  )}
                />
                {e.label}
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

export function ComboBoxScroll({
  values,
  onChange = () => {},
  placeholder = "Values...",
  searchPlaceholder = "Search...",
  defaultValue = undefined,
  value = "",
}:{
  values: valueType[],
  onChange?: (value: string, label: string) => void,
  placeholder?: string,
  searchPlaceholder?: string,
  defaultValue?: valueType | undefined,
  value?: string,
}) {
  const [open, setOpen] = React.useState(false)
  const [innerValue, setInnerValue] = React.useState(defaultValue?.value || value)

  return (
    <Popover open={open} onOpenChange={setOpen} modal={true}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[200px] justify-between"
        >
          {innerValue
            ? values.find((e) => e.value === innerValue)?.label
            : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <Command>
        <CommandInput placeholder={searchPlaceholder} />
          {/* <CommandInput placeholder={searchPlaceholder} />
          <CommandEmpty>No framework found.</CommandEmpty>
          <CommandGroup> */}
        {/* <ScrollArea className="h-[200px]">
            {values.map((e) => (
              <CommandItem
                key={e.value}
                value={e.value}
                onSelect={(currentValue) => {
                  setInnerValue(currentValue === innerValue ? "" : currentValue);
                  onChange(e.value, e.label);
                  setOpen(false)
                }}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    innerValue === e.value ? "opacity-100" : "opacity-0"
                  )}
                />
                {e.label}
              </CommandItem>
            ))}
        </ScrollArea> */}
          <ScrollArea className="h-[200px]">
            <CommandEmpty>Not found</CommandEmpty>
            <CommandGroup>
              {values.map((e) => (
                  <CommandItem
                    className="mr-[10px]"
                    key={e.value}
                    value={e.value}
                    onSelect={(currentValue) => {
                      setInnerValue(currentValue === innerValue ? "" : currentValue);
                      onChange(e.value, e.label);
                      setOpen(false)
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        innerValue === e.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {e.label}
                  </CommandItem>
                ))
              }
            </CommandGroup>
          </ScrollArea>
          {/* </CommandGroup> */}
        </Command>
      </PopoverContent>
    </Popover>
  )
}


export function ComboBoxScrollPreview({
  values,
  onChange = () => {},
  placeholder = "Values...",
  searchPlaceholder = "Search...",
  defaultValue = undefined,
  value = "",
}:{
  values: valueType[],
  onChange?: (value: string, label: string) => void,
  placeholder?: string,
  searchPlaceholder?: string,
  defaultValue?: valueType | undefined,
  value?: string,
}) {
  const [open, setOpen] = React.useState(false)
  const [innerValue, setInnerValue] = React.useState(defaultValue?.value || value)
  const [peekedPreview, setPeekedPreview] = React.useState("")


  return (
    <Popover open={open} onOpenChange={setOpen} modal={true}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[200px] justify-between"
        >
          {innerValue
            ? values.find((e) => e.value === innerValue)?.label
            : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[200px] p-0">
        <HoverCard>
          <HoverCardContent
            side="left"
            align="start"
            forceMount
            className="min-h-[280px]"
          >
            <div className="grid gap-2">
              <p>This is a test description</p>
              {peekedPreview ? (
                <p>{peekedPreview}</p>
              ) : null}
            </div>
          </HoverCardContent>
          <Command loop>
            <CommandList className="h-[var(--cmdk-list-height)] max-h-[400px]">
              <CommandInput placeholder={searchPlaceholder} />
              <CommandEmpty>No Models found.</CommandEmpty>
              <HoverCardTrigger />
              {/* {types.map((type) => (
                <CommandGroup key={type} heading={type}>
                  {models
                    .filter((model) => model.type === type)
                    .map((model) => (
                      <ModelItem
                        key={model.id}
                        model={model}
                        isSelected={selectedModel?.id === model.id}
                        onPeek={(model) => setPeekedModel(model)}
                        onSelect={() => {
                          setSelectedModel(model)
                          setOpen(false)
                        }}
                      />
                    ))}
                </CommandGroup>
              ))} */}
              <ScrollArea className="h-[200px]">
              <CommandGroup>
              {values.map((e) => (
                  <CommandItem
                    className="mr-[10px]"
                    key={e.value}
                    value={e.value}
                    onSelect={(currentValue) => {
                      setInnerValue(currentValue === innerValue ? "" : currentValue);
                      onChange(e.value, e.label);
                      setOpen(false)
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        innerValue === e.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {e.label}
                  </CommandItem>
                ))
              }
            </CommandGroup>
              </ScrollArea>
            </CommandList>
          </Command>
        </HoverCard>




        {/* <Command> */}
        {/* <CommandInput placeholder={searchPlaceholder} /> */}
          {/* <CommandInput placeholder={searchPlaceholder} />
          <CommandEmpty>No framework found.</CommandEmpty>
          <CommandGroup> */}
        {/* <ScrollArea className="h-[200px]">
            {values.map((e) => (
              <CommandItem
                key={e.value}
                value={e.value}
                onSelect={(currentValue) => {
                  setInnerValue(currentValue === innerValue ? "" : currentValue);
                  onChange(e.value, e.label);
                  setOpen(false)
                }}
              >
                <Check
                  className={cn(
                    "mr-2 h-4 w-4",
                    innerValue === e.value ? "opacity-100" : "opacity-0"
                  )}
                />
                {e.label}
              </CommandItem>
            ))}
        </ScrollArea> */}
          {/* <ScrollArea className="h-[200px]">
            <CommandEmpty>Not found</CommandEmpty>
            <CommandGroup>
              {values.map((e) => (
                  <CommandItem
                    className="mr-[10px]"
                    key={e.value}
                    value={e.value}
                    onSelect={(currentValue) => {
                      setInnerValue(currentValue === innerValue ? "" : currentValue);
                      onChange(e.value, e.label);
                      setOpen(false)
                    }}
                  >
                    <Check
                      className={cn(
                        "mr-2 h-4 w-4",
                        innerValue === e.value ? "opacity-100" : "opacity-0"
                      )}
                    />
                    {e.label}
                  </CommandItem>
                ))
              }
            </CommandGroup>
          </ScrollArea> */}
          {/* </CommandGroup> */}
        {/* </Command> */}
      </PopoverContent>
    </Popover>
  )
}


// export function ComboBoxScrollPreviewReference({ models, types, ...props }: ModelSelectorProps) {
//   const [open, setOpen] = React.useState(false)
//   const [selectedModel, setSelectedModel] = React.useState<Model>(models[0])
//   const [peekedModel, setPeekedModel] = React.useState<Model>(models[0])

//   return (
//     <div className="grid gap-2">
//       <HoverCard openDelay={200}>
//         <HoverCardTrigger asChild>
//           <Label htmlFor="model">Model</Label>
//         </HoverCardTrigger>
//         <HoverCardContent
//           align="start"
//           className="w-[260px] text-sm"
//           side="left"
//         >
//           The model which will generate the completion. Some models are suitable
//           for natural language tasks, others specialize in code. Learn more.
//         </HoverCardContent>
//       </HoverCard>
//       <Popover open={open} onOpenChange={setOpen} {...props}>
//         <PopoverTrigger asChild>
//           <Button
//             variant="outline"
//             role="combobox"
//             aria-expanded={open}
//             aria-label="Select a model"
//             className="w-full justify-between"
//           >
//             {selectedModel ? selectedModel.name : "Select a model..."}
//             <CaretSortIcon className="ml-2 h-4 w-4 shrink-0 opacity-50" />
//           </Button>
//         </PopoverTrigger>
//         <PopoverContent align="end" className="w-[250px] p-0">
//           <HoverCard>
//             <HoverCardContent
//               side="left"
//               align="start"
//               forceMount
//               className="min-h-[280px]"
//             >
//               <div className="grid gap-2">
//                 <h4 className="font-medium leading-none">{peekedModel.name}</h4>
//                 <div className="text-sm text-muted-foreground">
//                   {peekedModel.description}
//                 </div>
//                 {peekedModel.strengths ? (
//                   <div className="mt-4 grid gap-2">
//                     <h5 className="text-sm font-medium leading-none">
//                       Strengths
//                     </h5>
//                     <ul className="text-sm text-muted-foreground">
//                       {peekedModel.strengths}
//                     </ul>
//                   </div>
//                 ) : null}
//               </div>
//             </HoverCardContent>
//             <Command loop>
//               <CommandList className="h-[var(--cmdk-list-height)] max-h-[400px]">
//                 <CommandInput placeholder="Search Models..." />
//                 <CommandEmpty>No Models found.</CommandEmpty>
//                 <HoverCardTrigger />
//                 {types.map((type) => (
//                   <CommandGroup key={type} heading={type}>
//                     {models
//                       .filter((model) => model.type === type)
//                       .map((model) => (
//                         <ModelItem
//                           key={model.id}
//                           model={model}
//                           isSelected={selectedModel?.id === model.id}
//                           onPeek={(model) => setPeekedModel(model)}
//                           onSelect={() => {
//                             setSelectedModel(model)
//                             setOpen(false)
//                           }}
//                         />
//                       ))}
//                   </CommandGroup>
//                 ))}
//               </CommandList>
//             </Command>
//           </HoverCard>
//         </PopoverContent>
//       </Popover>
//     </div>
//   )
// }
