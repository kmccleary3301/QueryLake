import { Metadata } from "next"
import { NodesNav } from "./nodes-nav"

export const metadata: Metadata = {
  title: "Examples",
  description: "Check out some examples app built using the components.",
}

interface ExamplesLayoutProps {
  children: React.ReactNode,
  searchParams: object
}

export default function NodesLayout({ children, searchParams }: ExamplesLayoutProps) {
  return (
    <>
      <div>
        {/* <section>
          <div className="overflow-hidden rounded-[0.5rem] border bg-background shadow-md md:shadow-xl">
            
          </div>
        </section> */}
        <div className="absolute z-50 w-full flex flex-row justify-center pt-3 pb-3 pointer-events-none">
          <div className="pointer-events-auto">
            <NodesNav/>
          </div>
        </div>
        {children}
      </div>
    </>
  )
}
