import { ScrollArea } from "@/components/ui/scroll-area"

export default function DocsLayout({ 
	children 
} : {
	children: React.ReactNode
}) {
  
	return (
		<>
			<div className="w-full h-[calc(100vh)] flex flex-row justify-center">
				<ScrollArea className="w-full">
					<div className="flex flex-row justify-center">
						<div className="w-[85vw] md:w-[70vw] lg:w-[45vw] xl:w-[40vw]">
							{children}
							<div className="h-[100px]"/>
						</div>
					</div>
				</ScrollArea>
			</div>
		</>
	)
}