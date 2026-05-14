import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[10px] border text-[12px] font-medium tracking-[0.02em] transition-[transform,background-color,border-color,color,box-shadow,opacity] duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/45 focus-visible:ring-offset-0 disabled:pointer-events-none disabled:opacity-45",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.10),0_12px_24px_hsl(var(--background)/0.22)] hover:-translate-y-px hover:bg-primary/95 hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.10),0_14px_28px_hsl(var(--background)/0.26)] active:translate-y-0 active:shadow-[inset_0_1px_0_rgba(255,255,255,0.10),0_8px_18px_hsl(var(--background)/0.18)]",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.08),0_10px_22px_hsl(var(--background)/0.18)] hover:-translate-y-px hover:bg-destructive/[0.92] active:translate-y-0",
        outline:
          "border-border/80 bg-card/[0.78] text-foreground shadow-[inset_0_1px_0_hsl(var(--foreground)/0.03)] hover:-translate-y-px hover:border-[hsl(var(--ql-accent-amber)/0.45)] hover:bg-accent/55 hover:text-foreground active:translate-y-0",
        secondary:
          "border-border/70 bg-secondary/[0.72] text-secondary-foreground shadow-[inset_0_1px_0_hsl(var(--foreground)/0.03)] hover:-translate-y-px hover:bg-secondary/[0.88] active:translate-y-0",
        ghost:
          "border-transparent bg-transparent text-muted-foreground hover:bg-accent/65 hover:text-foreground active:bg-accent/90",
        link: "border-transparent bg-transparent px-0 text-foreground underline-offset-4 hover:text-[hsl(var(--ql-accent-amber))] hover:underline",
        transparent:
          "border-transparent bg-transparent text-foreground shadow-none hover:bg-transparent hover:text-foreground/80 active:bg-transparent",
      },
      size: {
        default: "h-9 px-3.5 py-2",
        sm: "h-8 rounded-[9px] px-2.5 py-1.5 text-[11px]",
        lg: "h-10 px-4.5 py-2.5 text-[13px]",
        icon: "h-9 w-9 rounded-[10px] p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };
