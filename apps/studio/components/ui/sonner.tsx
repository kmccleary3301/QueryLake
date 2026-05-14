"use client";

import { ThemeProviderWrapper } from "@/app/theme-provider";
import { useTheme } from "next-themes";
import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <ThemeProviderWrapper>
      <Sonner
        theme={theme as ToasterProps["theme"]}
        className="toaster group"
        toastOptions={{
          classNames: {
            toast:
              "group toast group-[.toaster]:rounded-[16px] group-[.toaster]:border group-[.toaster]:border-border/80 group-[.toaster]:bg-card/95 group-[.toaster]:text-foreground group-[.toaster]:shadow-[0_18px_38px_hsl(var(--background)/0.28)]",
            title: "group-[.toast]:text-[13px] group-[.toast]:font-medium",
            description: "group-[.toast]:text-[12px] group-[.toast]:leading-5 group-[.toast]:text-muted-foreground",
            actionButton:
              "group-[.toast]:border-none group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
            cancelButton:
              "group-[.toast]:border group-[.toast]:border-border/80 group-[.toast]:bg-card/70 group-[.toast]:text-muted-foreground",
          },
        }}
        {...props}
      />
    </ThemeProviderWrapper>
  );
};

export { Toaster };
