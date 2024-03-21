"use client";
import { useEffect, useContext, ContextType } from "react";
import { motion, stagger as defaultStagger, useAnimate } from "framer-motion";
import { cn } from "@/lib/utils";
// import { useContextAction } from "@/app/context-provider";
// import ContextProvider, { Context } from "@/app/context-provider";


export const TextGenerateEffect = ({
  words,
  className,
  stagger = defaultStagger,
}: {
  words: string;
  className?: string;
  stagger?: (typeof defaultStagger) | ((n: number) => number | undefined);
}) => {

  // const { setTheme } = useContextAction();

  // setTheme("light");

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
        delay: stagger(0.1),
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

  // const context_get = useContext(Context) as ContextType<>;
  // const { sidebarState, setSidebarState } = useContext(Context);
  

  return (
    // <ContextProvider>
      
      <div className={cn("font-bold", className)}>
        <div className="mt-4">
          <div className=" dark:text-white text-black text-2xl leading-snug tracking-wide">
            {renderWords()}
          </div>
        </div>
      </div>
  );
};



function TextSubComponent() {
  return (
    <div>
      <TextGenerateEffect words="hello world" />
    </div>
  );
}