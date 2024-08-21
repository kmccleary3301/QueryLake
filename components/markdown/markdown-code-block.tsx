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
import { getLanguage, highlight } from '@/lib/shiki';
// import ScrollSection from '../manual_components/scrollable-bottom-stick/custom-scroll-section';
import { Copy } from 'lucide-react';
import { BundledLanguage } from 'shiki/langs';
import { useContextAction } from "@/app/context-provider";
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

export const handleCopy = (text : string) => {
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

export default function MarkdownCodeBlock({
  className = "",
  text,
  unProcessedText = "",
  lang,
  finished = true,
}:{
  className?: string,
  text : string,
  unProcessedText?: string,
  lang: string,
  finished?: boolean
}){

  const {
    shikiTheme
  } = useContextAction();

  // const handleCopy = (text : string) => {
  //   if (typeof window === 'undefined') {
  //     return;
  //   }

  //   try {
  //     window.navigator.clipboard.writeText(text);
  //     toast("Copied to clipboard");
  //   } catch (err) {
  //     toast("Failed to copy to clipboard");
  //   }
  // };

  // const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  const [unprocessedText, setUnprocessedText] = useState<string[]>([]);
  const [language, setLanguage] = useState<{value: BundledLanguage | "text", preview: string}>({value: "text", preview: "Text"});
  const [codeHTML, setCodeHTML] = useState<string>("");
  const [lineCount, setLineCount] = useState<number>(0);


	const lastRefreshTime = useRef(Date.now());
	const oldInputLength = useRef(0);

  const refreshInterval = 150; // In milliseconds

  useEffect(() => {
    setLineCount(text.split("\n").length);

    const language_get = getLanguage(lang);
    setLanguage(language_get);
    if (lang === "text") {
      setCodeHTML(text + unProcessedText);
      return;
    }
  
    let raw_code = text+unProcessedText;
    const unprocessed_text = raw_code.slice(oldInputLength.current);
    if (finished) {
      raw_code = text;
    }
    
    if (oldInputLength.current === 0 || (Date.now() - lastRefreshTime.current) > refreshInterval) {

      highlight(raw_code, shikiTheme.theme, language_get.value).then((html) => {
        setCodeHTML(html);
      });
      
    } else {
      setUnprocessedText(unprocessed_text.split("\n"));
    }
  }, [text, unProcessedText, finished, lang, shikiTheme]);

  return (
    <div className={cn(
      'not-prose rounded-lg flex flex-col font-consolas my-3 border border-input', 
      fontConsolas.className,
      className
    )} style={{
      backgroundColor: (shikiTheme.backgroundColor || "#000000"), 
      color: (shikiTheme.textColor || "#FFFFFF"),
      // "--border": "#FFFFFF"
    } as React.CSSProperties}>
      <div className='pr-5 pl-9 py-2 pb-1 rounded-t-md flex flex-row justify-between text-sm bg-input' style={{
        // color: (shikiTheme.backgroundColor || "#000000"), 
        // backgroundColor: (shikiTheme.textColor || "#FFFFFF"),
      }}>
        <p className='font-consolas h-8 text-center flex flex-col justify-center text-primary border-none'>{language.preview}</p>
        <Button className='m-0 h-8 text-primary hover:text-primary/75 active:text-primary/50 bg-transparent hover:bg-transparent active:bg-transparent' onClick={() => {
          handleCopy(text + unProcessedText);
        }}>
          <Copy className="w-4 h-4"/>
          <p className='pl-[9px]'>{"Copy"}</p>
        </Button>
      </div>
      <pre className="p-0 pt-1 flex flex-row rounded-lg text-sm ">
        <code className="pt-[0px] pb-[20px] pl-[7px] pr-[7px] !whitespace-pre select-none border-opacity-100 border-secondary">
          {Array(lineCount).fill(20).map((e, line_number: number) => (
            <span key={line_number}>
              {line_number + 1}
              {"\n"}
            </span>
          ))}
        </code>
        <ScrollAreaHorizontal className='min-w-auto'>
          {/* <pre>{text}</pre> */}
          {(codeHTML === "")?(
            <pre className='pl-[5px] pt-[0px] pb-[20px] pr-[8px]'>{text}</pre>
          ):(
            <div className='pl-[5px] pt-[0px] pb-[20px] pr-[8px]' dangerouslySetInnerHTML={{__html: codeHTML}}/>
          )}
        </ScrollAreaHorizontal>
      </pre>
    </div>
  );
}