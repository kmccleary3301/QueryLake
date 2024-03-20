


export default function HuggingFaceRemodel() {
	const testArray = Array(200).fill("Test 1 2 3");
	return (
		<div style={{
			display: "flex",
			flexDirection: "column",
			width: "100%",
		}}>
			
			<div style={{width:50, height:50, border: "2px solid #FF0000"}}/>
			<div className="scrollbar-custom mr-1 h-full overflow-x-auto" style={{
				// margin: 1,
				width: "100%",
				height: "full",
				overflowY: "auto",
			}}>
				<div className="mx-auto flex h-full max-w-3xl flex-col gap-6 px-5 pt-6 sm:gap-8 xl:max-w-4xl" style={{
					display: "flex",
					flexDirection: "column",
					justifyContent: "center",
					flex: 1,
				}}>
					<div className="group relative flex items-start justify-start gap-4 max-sm:text-sm" style={{
						display: "flex",
						flexDirection: "column",
						justifyContent: "flex-start"
					}}>
						{testArray.map((item, index) => (
							<p key={index}>{item}</p>
						))}
					</div>
				</div>
			</div>
			<div style={{width:50, height:50, border: "2px solid #FF0000"}}/>
		</div>
	);
}