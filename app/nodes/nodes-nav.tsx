"use client"

import Link from "next/link"
import { useSearchParams } from 'next/navigation'
import { usePathname } from "next/navigation"

import {
  Tabs,
  TabsList,
  TabsTrigger,
} from "@/registry/default/ui/tabs"
import { motion } from 'framer-motion';
import { ScrollArea } from "@radix-ui/react-scroll-area"


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
    <motion.div
      initial={{ height: 20 }}
      whileHover={{ height: "auto" }}
      transition={{ duration: 0.3 }}
    >
      <ScrollArea>
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
      </ScrollArea>
    </motion.div>
  );

}