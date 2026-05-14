"use client";

import * as React from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";

import { useThemeContextAction } from "@/app/theme-provider";
import { cn } from "@/lib/utils";

const Popover = PopoverPrimitive.Root;
const PopoverTrigger = PopoverPrimitive.Trigger;

const sharedClassName =
  "z-50 w-72 rounded-[16px] border border-border/80 bg-popover/[0.98] p-4 text-popover-foreground shadow-[0_18px_38px_hsl(var(--background)/0.28)] outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95";

const PopoverContent = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 6, ...props }, ref) => {
  const { themeStylesheet } = useThemeContextAction();

  return (
    <PopoverPrimitive.Portal>
      <PopoverPrimitive.Content
        ref={ref}
        align={align}
        sideOffset={sideOffset}
        style={themeStylesheet}
        className={cn(sharedClassName, className)}
        {...props}
      />
    </PopoverPrimitive.Portal>
  );
});
PopoverContent.displayName = PopoverPrimitive.Content.displayName;

const PopoverContentNoPortal = React.forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = "center", sideOffset = 6, ...props }, ref) => {
  const { themeStylesheet } = useThemeContextAction();

  return (
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      style={themeStylesheet}
      className={cn(sharedClassName, className)}
      {...props}
    />
  );
});
PopoverContentNoPortal.displayName = "PopoverContentNoPortal";

export { Popover, PopoverTrigger, PopoverContent, PopoverContentNoPortal };
