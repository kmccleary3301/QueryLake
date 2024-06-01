import "@/styles/globals.css"
import { Metadata } from "next"

import { siteConfig } from "@/config/site"
import { fontSans } from "@/lib/fonts"
import { cn } from "@/lib/utils"
import { Analytics } from "@/components/inherited/analytics"
// import { ThemeProvider } from "@/components/inherited/providers"
import { ThemeProvider } from "./theme-provider";
import { SiteFooter } from "@/components/inherited/site-footer"
import { SiteHeader } from "@/components/inherited/site-header"
import { TailwindIndicator } from "@/components/inherited/tailwind-indicator"
import { ThemeSwitcher } from "@/components/inherited/theme-switcher"
import { Toaster as DefaultToaster } from "@/registry/default/ui/toaster"
import { Toaster as NewYorkSonner } from "@/registry/new-york/ui/sonner"
import { Toaster as NewYorkToaster } from "@/registry/new-york/ui/toaster"
import { ContextProvider } from "./context-provider"
// import { ThemeWrapper } from "@/components/inherited/theme-wrapper"
import SidebarController from "@/components/sidebar/sidebar"

// import { useRouter } from "next/navigation"
// import { AppProps } from "next/app"
// import { AppProps, useRouter } from 'next/app'
// import { AnimatePresence } from 'framer-motion'

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s - ${siteConfig.name}`,
  },
  metadataBase: new URL(siteConfig.url),
  description: siteConfig.description,
  keywords: [
    "Next.js",
    "React",
    "Tailwind CSS",
    "Server Components",
    "Radix UI",
  ],
  authors: [
    {
      name: "shadcn",
      url: "https://shadcn.com",
    },
  ],
  creator: "shadcn",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteConfig.url,
    title: siteConfig.name,
    description: siteConfig.description,
    siteName: siteConfig.name,
    images: [
      {
        url: siteConfig.ogImage,
        width: 1200,
        height: 630,
        alt: siteConfig.name,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.name,
    description: siteConfig.description,
    images: [siteConfig.ogImage],
    creator: "@shadcn",
  },
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon-16x16.png",
    apple: "/apple-touch-icon.png",
  },
  manifest: `${siteConfig.url}/site.webmanifest`,
}

export const viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "white" },
    { media: "(prefers-color-scheme: dark)", color: "black" },
  ],
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  // const router = useRouter();
  // const pageKey = router.as;

  return (
    <>
      <html lang="en" suppressHydrationWarning>
        <head />
        <body
          className={cn(
            "min-h-screen bg-background font-soehne antialiased",
            fontSans.className
          )}
        >
          {/* <ThemeWrapper> */}
          {/* <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            // disableTransitionOnChange
          > */}
            <div vaul-drawer-wrapper="">
              <ContextProvider 
                userData={undefined} 
                selectedCollections={new Map()}
                toolchainSessions={new Map()}
              >
              <ThemeProvider>
              <div className="relative flex h-screen w-screen flex-row bg-background">
                {/* <div className="flex flex-col w-[200px] h-full border border-blue-500"/> */}
                <SidebarController />
                <div className="relative flex h-screen w-full flex-col bg-background text-foreground">
                  {/* <SiteHeader /> */}
                  {/* <AnimatePresence initial={false} mode="popLayout"> */}
                    {/* <main className="flex-1">{children}</main> */}
                      {children}
                    
                  {/* </AnimatePresence> */}
                  {/* <SiteFooter /> */}
                </div>
              </div>
              </ThemeProvider>
              </ContextProvider>
            </div>
            <TailwindIndicator />
            <ThemeSwitcher />
            <Analytics />
            <NewYorkToaster />
            <DefaultToaster />
            <NewYorkSonner />
          {/* </ThemeProvider> */}
          {/* </ThemeWrapper> */}
        </body>
      </html>
    </>
  )
}
