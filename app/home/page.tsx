"use client";
import "public/registry/themes.css"
import { Announcement } from "@/components/inherited/announcement"
import {
  PageActions,
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/inherited/page-header"
import { ThemeCustomizer } from "@/components/inherited/theme-customizer"
import { ThemeWrapper } from "@/components/inherited/theme-wrapper"
import { ThemesTabs } from "@/app/themes/tabs"
import { Button } from "@/registry/default/ui/button";
import Link from "next/link"
import { motion } from 'framer-motion';

// ...

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15
    }
  }
};

const childVariants = {
  hidden: { opacity: 1, scale: 1.2, filter: "blur(5px)" },
  show: { opacity: 1, scale: 1, filter: "blur(0px)", transition: { duration: 0.4} },
};

const buttonProps : {header : string, content : string, link : string}[] = [
  {
    header: "Documentation",
    content: "Need help or want ideas on what to do? View QueryLake documentation, written by Kyle McCleary.",
    link: "/docs"
  },
  {
    header: "API",
    content: "Manage your API keys and view your model usage.",
    link: "/platform/api"
  },
  {
    header: "Apps",
    content: "Use Querylake and its custom applications.",
    link: "/app"
  
  }
]


export default function HomePage() {
  return (
    <div className="w-full h-[calc(100vh-60px)] flex flex-col justify-center">
      <div className="w-full flex flex-row justify-center">
        <motion.div className="flex-shrink flex flex-col lg:flex-row justify-center space-y-2 lg:space-y-0 lg:space-x-2"
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >

          {buttonProps.map((button, index) => (
            <motion.div className="h-[160px] lg:h-[400px] w-[300px] " variants={childVariants} key={index}>
              <Link href={button.link}>
                <Button variant="ghost" className="h-full w-full rounded-xl overflow-auto whitespace-normal items-center py-2 lg:py-6 px-4 lg:px-8">
                  <div className="h-full w-full flex flex-col justify-center lg:justify-start space-y-3">
                    <p className="w-[90%] text-lg lg:text-xl text-left"><strong>{button.header}</strong></p>
                    <div className="bg-secondary rounded-full w-[90%] h-[2px]"/>
                    <p className="w-[90%] text-sm lg:text-base break-words text-left">{button.content}</p>
                  </div>
                </Button>
              </Link>
            </motion.div>
          ))}
          {/* <motion.div variants={childVariants}>
            <Link href="/docs">
              <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
                <p className="w-[260px] text-xl text-left">Documentation</p>
                <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
                <p className="w-[260px] text-base text-primary/80 break-words text-left">Need help or want ideas on what to do? View QueryLake documentation, written by Kyle McCleary.</p>
              </Button>
            </Link>
          </motion.div>
          <motion.div variants={childVariants}>
            <Link href="/api-keys">
              <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
                <p className="w-[260px] text-xl text-left">API</p>
                <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
                <p className="w-[260px] text-base break-words text-left">Manage your API keys and view your model usage.</p>
              </Button>
            </Link>
          </motion.div>
          <motion.div variants={childVariants}>
            <Link href="/chat">
              <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
                <p className="w-[260px] text-xl text-left">Apps</p>
                <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
                <p className="w-[260px] text-base break-words text-left">Use Querylake and its custom applications.</p>
              </Button>
            </Link>
          </motion.div> */}
        </motion.div>
      </div>
    </div>
  )
}

// export default function HomePage() {
//   return (
//     // <div className="container">
//       <div className="w-full h-[calc(100vh-60px)] flex flex-col justify-center">
//         <div className="w-full flex flex-row justify-center space-x-8">
//           <Link href="/docs">
//             <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
//               <p className="w-[260px] text-xl text-left">Documentation</p>
//               <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
//               <p className="w-[260px] text-md break-words text-left">Need help or want ideas on what to do? View QueryLake documentation, written by Kyle McCleary.</p>
//             </Button>
//           </Link>
//           <Link href="/api-keys">
//             <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
//               <p className="w-[260px] text-xl text-left">API</p>
//               <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
//               <p className="w-[260px] text-md break-words text-left">Manage your API keys and view your model usage.</p>
//             </Button>
//           </Link>
//           <Link href="/chat">
//             <Button variant="ghost" className="h-[400px] w-[300px] rounded-xl pt-8 flex flex-col overflow-auto whitespace-normal justify-start space-y-3">
//               <p className="w-[260px] text-xl text-left">Apps</p>
//               <div className="bg-secondary rounded-full w-[260px] h-[2px]"/>
//               <p className="w-[260px] text-md break-words text-left">Use Querylake and its custom applications.</p>
//             </Button>
//           </Link>
//         </div>
//       </div>
//     // </div>
//   )
// }
