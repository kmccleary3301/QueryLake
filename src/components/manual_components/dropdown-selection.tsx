"use client"
 
import { useState } from "react"
import { CaretSortIcon, CheckIcon } from "@radix-ui/react-icons"
 
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

export type formValueType = string | string[];

export type formEntryType = {
	label : string,
	value : formValueType
}

type DropDownSelectionProps = {
  values: formEntryType[],
  defaultValue: formEntryType,
  setSelection: (value : formEntryType) => void,
  selection: formEntryType
};

export function DropDownSelection(props : DropDownSelectionProps) {
  const [open, setOpen] = useState(false);
  // const [value, setValue] = useState<formValueType>(props.defaultValue.value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-[400px] justify-between"
        >
          {props.selection
            ? props.values.find((framework) => framework.value === props.selection.value)?.label
            : "Select framework..."}
          <CaretSortIcon className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0">
        <Command>
          <CommandInput placeholder="Search framework..." className="h-9" />
          <CommandEmpty>No framework found.</CommandEmpty>
          <CommandGroup>
            {props.values.map((framework : formEntryType) => (
              <CommandItem
                key={framework.value}
                value={framework.value}
                onSelect={() => {
                  // setValue(framework.value === props.selection.value ? "" : framework.value);
                  props.setSelection(framework);
                  setOpen(false)
                }}
              >
                {framework.label}
                <CheckIcon
                  className={cn(
                    "ml-auto h-4 w-4",
                    props.selection.value === framework.value ? "opacity-100" : "opacity-0"
                  )}
                />
              </CommandItem>
            ))}
          </CommandGroup>
        </Command>
      </PopoverContent>
    </Popover>
  )
}