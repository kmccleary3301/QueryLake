"use client";
import { useEffect } from "react";
import { stagger} from "framer-motion";
import { TextGenerateEffect } from "./text-generate-effect";

export const QueryLakeDisplay = () => {
  return (
    <>
		<TextGenerateEffect staggerDelay={0.05} words="QueryLake" className="text-2xl md:text-4xl lg:text-7xl text-white font-bold text-center"/>
		<TextGenerateEffect staggerDelay={0.05} words="An AI platform for everyone." className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center"/>
		<TextGenerateEffect staggerDelay={0.05} words="Create, deploy, and test an AI workflow in minutes." className="text-base md:text-lg mt-4 text-white font-normal inter-var text-center"/>
	</>
  );
};
