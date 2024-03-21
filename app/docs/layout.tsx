import { ScrollArea } from "@/registry/default/ui/scroll-area"

export default function DocsLayout({ 
	children 
} : {
	children: React.ReactNode
}) {
	return (
		<>
			<div className="w-full h-[calc(100vh-60px)] flex flex-row justify-center">
				<ScrollArea className="w-full">
					<div className="flex flex-row justify-center">
						<div className="w-[85vw] md:w-[70vw] lg:w-[45vw]">
							{children}
							<div className="h-[100px]"/>
						</div>
					</div>
				</ScrollArea>
			</div>
		</>
	)
}