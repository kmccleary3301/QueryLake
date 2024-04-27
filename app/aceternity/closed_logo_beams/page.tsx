import { Metadata } from "next"
import { BackgroundBeams } from "@/app/aceternity/background_beams/components/background-beams"
import { ClosedLogoBeams } from "./components/closed_logo_beams"

export const metadata: Metadata = {
  title: "Closed Logo Beams",
  description: "Closed logo beams built on example from Aceternity.",
}

export default function ClosedLogoBeamsPage() {
  return (
    <>
      <div className="h-[40rem] w-full rounded-md bg-neutral-950 relative flex flex-col items-center justify-center antialiased">
        <ClosedLogoBeams/>
      </div>
    </>
  )
}
