"use client";
import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { get } from "http";

// function getPathLength(pathData : string) {
//   // Create a new SVG path element
//   const pathElement = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  
//   // Set the "d" attribute to your path data
//   pathElement.setAttribute('d', pathData);
  
//   // Get the length of the path
//   const pathLength = pathElement.getTotalLength();
  
//   return pathLength;
// }

const draw = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: (i : number) => {
    const delay = 1 + i * 0.5;
    return {
      pathLength: 1,
      opacity: 1,
      transition: {
        pathLength: { delay, type: "spring", duration: 1, bounce: 0 },
        opacity: { delay, duration: 0.01 }
      }
    };
  }
};

export const ClosedLogoBeams = React.memo(
  ({ className }: { className?: string }) => {

    // const paths = [
    //   "M380.844 297.529c.787 84.752 74.349 112.955 75.164 113.314-.622 1.988-11.754 40.191-38.756 79.652-23.343 34.117-47.568 68.107-85.731 68.811-37.499.691-49.557-22.236-92.429-22.236-42.859 0-56.256 21.533-91.753 22.928-36.837 1.395-64.889-36.891-88.424-70.883-48.093-69.53-84.846-196.475-35.496-282.165 24.516-42.554 68.328-69.501 115.882-70.192 36.173-.69 70.315 24.336 92.429 24.336 22.1 0 63.59-30.096 107.208-25.676 18.26.76 69.517 7.376 102.429 55.552-2.652 1.644-61.159 35.704-60.523 106.559Z",
    //   "M310.369 89.418C329.926 65.745 343.089 32.79 339.498 0 311.308 1.133 277.22 18.785 257 42.445c-18.121 20.952-33.991 54.487-29.709 86.628 31.421 2.431 63.52-15.967 83.078-39.655Z"
    // ];
    const paths = [
      "m.81.81v78.67h71.09v-17.21H29.05V.8H.81h0Z",
      "m98.28,0c-13.13,0-23.8,8.05-23.8,17.95v29.99h55.78v7.58c0,3.22-3.68,5.84-8.2,5.84h-47.57v17.31h60.13c13.18,0,23.9-8.05,23.9-17.95v-30.09h-55.78v-7.48c0-3.17,3.71-5.84,8.11-5.84h47.67V.81h-60.22,0Z",
      "m119.3,0v55.52c0,3.27-3.68,5.94-8.2,5.94h-19.51V1h-27.97v78.48h60.04c13.13,0,23.81-8.05,23.81-17.95V.81h-28.16,0Z",
    ];
    return (
      <div
        className={cn(
          "absolute  h-full w-full inset-0  [mask-size:40px] [mask-repeat:no-repeat] flex items-center justify-center",
          className
        )}
      >
        <svg
          className=" z-0 h-full w-full pointer-events-none absolute "
          // width="100%"
          // height="100%"
          // viewBox="0 0 696 316"
          // fill="none"
          // xmlns="http://www.w3.org/2000/svg"
          fillOpacity={0}
          xmlns="http://www.w3.org/2000/svg" 
          height={(82.281*0.5).toString()} 
          viewBox="0 0 247.35 80.28" 
          width={(249.35*0.5).toString()}
        >
            <path
              d={paths.join("")}
              stroke="url(#paint0_radial_242_278)"
              strokeOpacity="0.05"
              strokeWidth="1"
            ></path>
          
          
          {paths.map((path, index) => (
            <motion.path
              key={`path-` + index}
              d={path}
              stroke={`url(#linearGradient-${index})`}
              strokeOpacity="0.4"
              strokeWidth="0.5"
            ></motion.path>
          ))}
          <defs>
            {paths.map((path, index) => (
              <motion.linearGradient
                id={`linearGradient-${index}`}
                x1="100%"
                x2="100%"
                y1="100%"
                y2="100%"
                scale={0.5}
                key={`gradient-${index}`}
                animate={{
                  x1: ["0%", "100%"],
                  x2: ["0%", "0%"],
                  y1: ["0%", "100%"],
                  y2: ["0%", `0%`],
                }}
                transition={{
                  duration: (Math.random() * 5 + 1),
                  ease: "easeInOut",
                  repeat: Infinity,
                  // delay: Math.random() * 10,
									delay: 0,
                }}
              >
                <stop stopColor="#18CCFC" stopOpacity="0"></stop>
                <stop stopColor="#18CCFC"></stop>
                <stop offset="32.5%" stopColor="#6344F5"></stop>
                <stop offset="100%" stopColor="#AE48FF" stopOpacity="0"></stop>
              </motion.linearGradient>
            ))}

            <radialGradient
              id="paint0_radial_242_278"
              cx="0"
              cy="0"
              r="1"
              gradientUnits="userSpaceOnUse"
              gradientTransform="translate(352 34) rotate(90) scale(555 1560.62)"
            >
              <stop offset="0.0666667" stopColor="var(--neutral-300)"></stop>
              <stop offset="0.243243" stopColor="var(--neutral-300)"></stop>
              <stop offset="0.43594" stopColor="white" stopOpacity="0"></stop>
            </radialGradient>
          </defs>
        </svg>
      </div>
    );
  }
);

ClosedLogoBeams.displayName = "BackgroundBeams";
