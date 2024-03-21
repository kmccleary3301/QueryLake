"use client";
import { useEffect } from "react";
import { motion, stagger, useAnimate } from "framer-motion";
// import { useContextAction } from "@/app/context-provider";


export const TextGenerateEffect = ({
  words,
  className,
  staggerDelay = 0.4,
}: {
  words: string;
  className?: string
  staggerDelay?: number;
}) => {

  // const { setTheme } = useContextAction();

  // setTheme("dark");

  const [scope, animate] = useAnimate();
  let wordsArray = words.split(" ");
  useEffect(() => {
    animate(
      "span",
      {
        opacity: 1,
      },
      {
        duration: 1,
        delay: stagger(staggerDelay),
      }
    );
  }, [scope.current]);

  const renderWords = () => {
    return (
      <motion.div ref={scope}>
        {wordsArray.map((word, idx) => {
          return (
            <motion.span
              key={word + idx}
              className="dark:text-white text-black opacity-0"
            >
              {word}{" "}
            </motion.span>
          );
        })}
      </motion.div>
    );
  };

  return (
    <div className={className}>
      {renderWords()}
    </div>
  );
};
