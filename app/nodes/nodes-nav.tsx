"use client"

import Link from "next/link"
import { useSearchParams } from 'next/navigation'
import { usePathname } from "next/navigation"
import { useState, useRef, useEffect } from "react"
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
  
  const searchParamsString = useSearchParams()?.toString() || undefined;
  const linkAppend = searchParamsString ? `?${searchParamsString}` : "";

  const [hover, setHover] = useState(false);

  // const divRef = useRef<HTMLDivElement>(null);

  // const scrollToBottom = () => {
  //   const div = divRef.current;
  //   if (div) {
  //     div.scrollTop = div.scrollHeight;
  //   }
  // };

  // useEffect(() => {
  //   scrollToBottom();
  // }, [hover]); // add any other dependencies that could change the content of the div

  return (
    <div className="">
      <motion.div
        className="overflow-hidden bg-secondary rounded-b-md"
        initial={{ height: 20 }}
        animate={ (hover) ? 
          { height: 'auto'} : 
          { height: 10}
        }
        transition={{ duration: 0.2 }}
        onHoverStart={() => setHover(true)}
        onHoverEnd={() => setHover(false)}
        // onChange={()=>{scrollToBottom();}}
        // ref={divRef}
      >
        <div className="pb-2 pt-2">
          {/* <motion.div
            className="w-auto bg-secondary"
            animate={ (hover) ? 
              { height: 0, borderRadius: "10px"} : 
              { height: 10, borderRadius: "0px 0px 10px 10px"}
            }
            transition={{ duration: 0.2, delay: 0.01 }}
          >
          </motion.div> */}
            <Tabs defaultValue={pathname} onValueChange={(value : string) => {console.log("Value changed to", value)}}>
              <TabsList className="grid w-full grid-cols-2 rounded-none">
                {examples.map((example, index) => (
                  <TabsTrigger key={index} value={example.href}>
                    <Link href={example.href+linkAppend}>
                      {example.name}
                    </Link>
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
        </div>
      </motion.div>
    </div>
  );
}