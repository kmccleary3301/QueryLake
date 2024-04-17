"use client";
import { ScrollArea, ScrollAreaHorizontal, ScrollBar } from '@/registry/default/ui/scroll-area';
// import hljs from 'highlight.js';
// import { getHighlighter } from 'shiki';
import { useEffect, useState, useRef, useCallback } from "react";
import { fontConsolas } from '@/lib/fonts';
import { cn } from '@/lib/utils';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';
import { toast } from 'sonner';
import { highlight } from '@/lib/shiki';
import ScrollSection from '../manual_components/scrollable-bottom-stick/custom-scroll-section';
// import { renderToHtml } from "shiki";
// import codeToHTML
// import { codeToHtml } from 'shiki/index.mjs';
// import { Lang } from 'shiki';

const code_styling = new Map<string, string>([
  ["hljs-keyword", "#2E80FF"],
  ["hljs-function", "#DCDCAA"],
  ["hljs-meta", "#CE9178"],
  ["hljs-comment", "#6A9955"],
  ["hljs-params", "#8CDCF0"],
  ["hljs-literal", "#DF3079"],
  ["hljs-string", "#CE9178"],
  ["hljs-title class_", "#32BBB0"],
  ["hljs-title function_", "#DCDCAA"],
  ["hljs-number", "#DF3079"],
  ["hljs-built_in", "#DCDCAA"],
  ["hljs-type", "#4EC9B0"],
  ["default", "#DCDCAA"],
]);

type MarkdownCodeBlockProps = {
  text : string,
  unProcessedText: string,
  lang: string,
  finished: boolean
}

type scoped_text = {
  scope: string[],
  content: string
};

export default function MarkdownCodeBlock({
  className = "",
  text,
  unProcessedText,
  lang,
  finished,
}:{
  className?: string,
  text : string,
  unProcessedText: string,
  lang: string,
  finished: boolean
}){
  const handleCopy = (text : string) => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.navigator.clipboard.writeText(text);
      toast("Copied to clipboard");
    } catch (err) {
      toast("Failed to copy to clipboard");
    }
  };

  // const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  const [unprocessedText, setUnprocessedText] = useState<string[]>([]);
  const [language, setLanguage] = useState<string>("Unknown");
  const [codeHTML, setCodeHTML] = useState<string>("");
  const [lineCount, setLineCount] = useState<number>(0);


	const lastRefreshTime = useRef(Date.now());
	const oldInputLength = useRef(0);

  const refreshInterval = 250; // In milliseconds

  useEffect(() => {
    setLineCount(text.split("\n").length);
    setLanguage(lang);
    if (lang === "text") {
      // const scope_tree = (props.text + props.unProcessedText).split("\n").map((line: string) => {
      //   return [{
      //     scope: [],
      //     content: line
      //   }];
      // });
      // setHighlights(scope_tree);
      setCodeHTML(text + unProcessedText);
      return;
    }
  
    let raw_code = text+unProcessedText;
    const unprocessed_text = raw_code.slice(oldInputLength.current);
    if (finished) {
      raw_code = text;
    }
  
    if (oldInputLength.current === 0 || (Date.now() - lastRefreshTime.current) > refreshInterval) {

      highlight(raw_code, 'nord', lang).then((html) => {
        setCodeHTML(html);
      });
      
    } else {
      setUnprocessedText(unprocessed_text.split("\n"));
    }
  }, [text, unProcessedText, finished, lang]);

  return (
    <div className={cn(
      'not-prose rounded-lg bg-[#0E0E0E] flex flex-col font-consolas text-white my-3', 
      fontConsolas.className,
      className
    )}>
      <div className='mr-5 ml-9 my-1 flex flex-row justify-between text-sm'>
        <p className='font-consolas h-8 text-center flex flex-col justify-center border-none'>{language}</p>
        <Button className='m-0 h-8' variant="ghost" onClick={() => {
          handleCopy(text + unProcessedText);
        }}>
          <Icon.Clipboard className='w-[17px]'/>
          <p className='pl-[5px]'>{"Copy"}</p>
        </Button>
      </div>
      <div className='w-auto h-[1px] bg-secondary'/>
      <pre className="p-0 flex flex-row rounded-lg text-sm ">
        <code className="pt-[5px] pb-[20px] pl-[7px] pr-[7px] text-white/50 !whitespace-pre select-none border-opacity-100 border-secondary">
          {/* {Array(highlights.length + (props.finished ? 0 : unprocessedText.slice(1, unprocessedText.length - 1).length)).fill(20).map((e, line_number: number) => (
              <>
                {line_number + 1}
                {"\n"}
              </>
          ))} */}
          {Array(lineCount).fill(20).map((e, line_number: number) => (
              <span key={line_number}>
                {line_number + 1}
                {"\n"}
              </span>
          ))}
        </code>
        {/* <div className='w-[2px] h-auto bg-secondary'/>
        <div className='w-[4px] h-auto'/> */}
        {/* <div className="flex flex-col overflow-y-hidden overflow-x-auto w-full justify-start"> */}
        <ScrollAreaHorizontal className='min-w-auto'>
          <div className='pl-[10px] pt-[5px] pb-[20px]'>
            <code className='pt-[20px] pb-[20px] font-consolas text-sm !whitespace-pre cursor-text'>
              {(!finished) && (
                <>
                  {unprocessedText.slice(1, unprocessedText.length - 1).map((line: string, line_number: number) => (
                    <>
                      <span key={line_number} className="text-sm" style={{color : code_styling.get("default")}}>
                        {line}
                      </span>
                      {"\n"}
                    </>
                  ))}
                </>
              )}
              <code className='bg-transparent' dangerouslySetInnerHTML={{__html: codeHTML}}></code>
            </code>
          </div>
          {/* <ScrollBar orientation="horizontal" /> */}
        </ScrollAreaHorizontal>
        {/* </div> */}
      </pre>
    </div>
  );
}