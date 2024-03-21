"use client"

import Link from "next/link"
import { useSearchParams } from 'next/navigation'
import { usePathname } from "next/navigation"
import { ArrowRightIcon } from "@radix-ui/react-icons"
import { useRouter } from 'next/router'

import { cn } from "@/lib/utils"
import { ScrollArea, ScrollBar } from "@/registry/new-york/ui/scroll-area"

import { Button } from "@/registry/default/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/registry/default/ui/card"
import { Input } from "@/registry/default/ui/input"
import { Label } from "@/registry/default/ui/label"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/registry/default/ui/tabs"
import { json } from "stream/consumers"


const examples = [
  {
    name: "Node Editor",
    href: "/nodes/node_editor"
  },
  {
    name: "Display Editor",
    href: "/nodes/display_editor"
  }
]

interface ExamplesNavProps extends React.HTMLAttributes<HTMLDivElement> {}

export function NodesNav({ className, ...props }: ExamplesNavProps) {
  const pathname = usePathname() || "";
  
  // Get searchParams as an Object
  // const searchParams = useSearchParams();
  // const allParams = Object.fromEntries(searchParams?.entries() || []); 
  
  const searchParamsString = useSearchParams()?.toString() || undefined;
  const linkAppend = searchParamsString ? `?${searchParamsString}` : "";

  return (
    <Tabs defaultValue={pathname} onValueChange={(value : string) => {console.log("Value changed to", value)}}>
      <TabsList className="grid w-full grid-cols-2">
        {examples.map((example, index) => (
          <TabsTrigger key={index} value={example.href}>
            <Link href={example.href+linkAppend}>
              {example.name}
            </Link>
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  );

}