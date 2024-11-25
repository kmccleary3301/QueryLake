import { ScrollArea } from "@/components/ui/scroll-area"

export default function DocsLayout({ 
	children 
} : {
	children: React.ReactNode
}) {
  
	return (
		<>
			<div 
				className="w-full h-[calc(100vh)] absolute" 
				style={{
					"--container-width": "100%"
				} as React.CSSProperties}
			>
      <div className="w-full h-[calc(100vh)]">
        <ScrollArea className="w-full h-screen">
          <div className="flex flex-row justify-center">
            <div className="w-[min(var(--container-width),70vw)] lg:w-[min(var(--container-width),55vw)] xl:w-[min(var(--container-width),40vw)] border-blue-500 border-2">
              <div className="px-[3rem]">
								{children}

							</div>
							
              <div className="h-[100px]"/>
            </div>
          </div>
        </ScrollArea>
      </div>
			</div>
    </>
	)
}