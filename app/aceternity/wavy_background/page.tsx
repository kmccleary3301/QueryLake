import { Metadata } from "next"
// import { BackgroundBeams } from "@/app/aceternity/background_beams/components/background-beams"
import { WavyBackground } from "./components/wavy-background"
import { TextGenerateEffect } from "../text_generate_effect/components/text-generate-effect";
import { stagger } from "framer-motion";
import { QueryLakeDisplay } from "./components/display-text";

export const metadata: Metadata = {
  title: "Background Beams",
  description: "Background beams example from Aceternity.",
}

const LSULogoSVG = [
  "m340.55 617.76v-0.64375-61.648-0.64375h0.64375 55.584 0.64375v0.64375 12.483 0.64375h-0.64375-33.633v48.522 0.64375h-0.64375-21.308-0.64375z",
  "m78.627-0.002c-10.501 0-19.044-6.4421-19.044-14.361v-23.348-0.64375h0.64375 43.978v-6.0609c0-2.5761-2.9439-4.6719-6.5641-4.6719h-37.414-0.64375v-0.64376-12.562-0.64374h0.64375 47.459c10.544 0 19.12 6.4421 19.12 14.361v23.428 0.64375h-0.64375-43.978v5.9812c0 2.5336 2.9688 4.6734 6.4859 4.6734h37.492 0.64375v0.64374 12.561 0.64375h-0.64375-47.536z",
  "m95.441 0v-0.64375-43.77c0-2.6199-2.9452-4.75-6.5641-4.75h-15.612v48.367 0.64375h-0.64376-21.086-0.64375v-0.64375-61.495-0.64374h0.64375 47.387c10.503 0 19.047 6.4421 19.047 14.361v47.931 0.64375h-0.64375-21.241-0.64375z"
];


export default function WavyBackgroundPage() {
  

  return (
    <>
      <WavyBackground className="max-w-4xl mx-auto pb-20 pt-20 h-full" 
        blur={5} 
        waveWidth={3} 
        waveCount={20} 
        waveAmplitude={180}
        wavePinch={0}
        speed={4}
      >
        <div id="spacing div" className="h-full flex flex-col justify-between items-center">
          <div/>
          <div>
            {/* <p className="text-2xl md:text-4xl lg:text-7xl text-white font-bold text-center">
              QueryLake
            </p>
            <p className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center">
              An AI platform for everyone.
            </p>
            <p className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center">
              Create, deploy, and test an AI workflow in minutes.
            </p> */}
            {/* <TextGenerateEffect words="QueryLake" className="text-2xl md:text-4xl lg:text-7xl text-white font-bold text-center"/>
            <TextGenerateEffect words="An AI platform for everyone." className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center"/>
            <TextGenerateEffect words="Create, deploy, and test an AI workflow in minutes." className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center"/> */}
          
            <QueryLakeDisplay/>
          </div>
          
          <div className="flex justify-center items-end mt-8">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              height={(82.281*0.5).toString()} 
              viewBox="0 0 249.35339 82.281128" 
              width={(249.35*0.5).toString()}
            >
              <g transform="matrix(1.25 0 0 -1.25 -424 774.12)">
                <path 
                  d={LSULogoSVG.join(" ")}
                  fill="currentColor"
                />
              </g>
            </svg>
          </div>
        </div>
      </WavyBackground>
    </>
  )
}
