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
} from "./command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./popover"

type valueType = {value: string, label: string};

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
