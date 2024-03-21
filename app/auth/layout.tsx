import { Metadata } from "next"
import { WavyBackground } from "./components/wavy-background";
import { QueryLakeDisplay } from "./components/display-text";

export const metadata: Metadata = {
  title: "Log-In/Register",
  description: "Log in or register for QueryLake",
}

export default function CoverTestPage({ children }:{ children: React.ReactNode }) {
  return (
    <>
      <div>
        <WavyBackground 
          className="w-full mx-0 h-full"
          containerClassName="transform-gpu w-full h-[calc(100vh-75px)]"
          canvasClassName="h-[calc(100vh-57px)] w-[calc(100vw)] blur-[3px]"
          blur={3}
          waveWidth={4} 
          waveCount={20} 
          waveAmplitude={0.34}
          wavePinchEnd={0}
          wavePinchMiddle={0.064}
          speed={2.5}
          backgroundFill="primary"
        >
          <div className="w-full h-full">
            <div/>
            <QueryLakeDisplay>
              {children}
            </QueryLakeDisplay>
          </div>
        </WavyBackground>
      </div>
    </>
  )
}
