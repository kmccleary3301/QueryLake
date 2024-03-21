"use client";
import { ScrollArea, ScrollAreaHorizontal, ScrollBar } from '@/registry/default/ui/scroll-area';
import hljs from 'highlight.js';
import { useEffect, useState, useRef, useCallback } from "react";
import { fontConsolas } from '@/lib/fonts';
import { cn } from '@/lib/utils';
import { Button } from '@/registry/default/ui/button';
import * as Icon from 'react-feather';
import { toast } from 'sonner';

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

type parser_segment = scoped_text | "\n";

function decode_html(input : string) {
  input = input.replaceAll('&#x27;', "'");
  input = input.replaceAll('&quot;', "\"");
  input = input.replaceAll('&lt;', "<");
  input = input.replaceAll('&gt;', ">");
  input = input.replaceAll('&amp;', '&');
  return input;
}


function parseScopeTreeText(hljs_html : string) {
  /*
   * Let's not discuss this lmao.
   */

  let match = hljs_html.match(/(<.*?>)/);
  const current_scope : string[] = [];
  let index = 0;
  const return_segments : scoped_text[][] = [];
  const string_segments : parser_segment[] = [];


  if (match === null) {
      string_segments.push({
        scope: [],
        content: hljs_html
      });
  }
  while (match !== null && match.index !== undefined) {
    // console.log("match:", match[0]);
    if (match.index > 0) {
      const text = hljs_html.slice(index, index+match.index).split("\n");
      // console.log("Text");
      // console.log(text);
      for (let i = 0; i < text.length; i++) {
        const decoded = decode_html(text[i]);
        if (decoded.length > 0) {
          if (i !== 0) { 
            string_segments.push("\n") 
          }
          if (text[i].length > 0) {
            string_segments.push({
              scope: current_scope.slice(),
              content: decoded
            })
          }
        } else if (i != 0) {
          string_segments.push("\n");
        }
      }
    }
    const match_open_scope = match[0].match(/(".*?")/);
    if (match_open_scope !== null) {
      current_scope.push(match_open_scope[0].slice(1, match_open_scope[0].length-1));
    } else {
      current_scope.pop();
    }
    const new_index = index+match[0].length+match.index;
    const new_match = hljs_html.slice(new_index).match(/(<.*?>)/);
    if (new_match === null && new_index < hljs_html.length) {
      const text = hljs_html.slice(new_index).split("\n");
      // console.log("Text");
      // console.log(text);
      for (let i = 0; i < text.length; i++) {
        const decoded = decode_html(text[i]);
        if (decoded.length > 0) {
          if (i != 0) { 
            string_segments.push("\n");
          }
          string_segments.push({
            scope: current_scope.slice(),
            content: decode_html(text[i])
          })
        } else if (i != 0) {
          string_segments.push("\n");
        }
      }
    } 
    match = new_match;
    index = new_index;
  }
  index = 0;
  let temp_segments : scoped_text[]  = [];
	for (let i = 0; i < string_segments.length; i++) {
		if (string_segments[i] === "\n") {
			// if (temp_segments.length > 0) {
			return_segments.push(temp_segments.slice());
			// }
			temp_segments = [];
			index = i;
		} else {
			const tmp_value : scoped_text = string_segments[i] as scoped_text;
			temp_segments.push(tmp_value);
		}
	}
  return_segments.push(temp_segments.slice());
  return return_segments;
}

export default function MarkdownCodeBlock(props : MarkdownCodeBlockProps){
  // const fontSize = 14;

  const handleCopy = useCallback((text : string) => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.navigator.clipboard.writeText(text);
      toast("Copied to clipboard");
    } catch (err) {
      toast("Failed to copy to clipboard");
    }
  }, []);

  const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  const [unprocessedText, setUnprocessedText] = useState<string[]>([]);
  const [language, setLanguage] = useState<string>("Unknown");

	const lastRefreshTime = useRef(Date.now());
	const oldInputLength = useRef(0);

  const refreshInterval = 250; // In milliseconds

  useEffect(() => {
    // setRawCode(raw_code);

    if (props.lang === "text") {
      setLanguage("text");
      const scope_tree = (props.text + props.unProcessedText).split("\n").map((line: string) => {
        return [{
          scope: [],
          content: line
        }];
      });
      setHighlights(scope_tree);
      return;
    }


    let raw_code = props.text+props.unProcessedText;
    const unprocessed_text = raw_code.slice(oldInputLength.current);
    if (props.finished) {
      raw_code = props.text;
    }

    // console.log("Highlighting raw code:", raw_code)
    // setLineOffsets(getLineOffsets(raw_code));
    if (oldInputLength.current === 0 || (Date.now() - lastRefreshTime.current) > refreshInterval) {
      const highlights_get = (props.lang)?hljs.highlight(props.text, {"language": props.lang}):hljs.highlightAuto(raw_code.replaceAll(/\n[\s|\t]+/g, "\n"));
      setLanguage((props.lang)?props.lang:(highlights_get.language?highlights_get.language:"Unknown"));
      
      const scope_tree = parseScopeTreeText(highlights_get.value);
      setHighlights(scope_tree);
      // console.log("Highlights:", scope_tree);
      // setLastRefreshTime(Date.now());
      // setOldInputLength(raw_code.length);
			lastRefreshTime.current = Date.now();
			oldInputLength.current = raw_code.length;
    } else {
      setUnprocessedText(unprocessed_text.split("\n"));
    }
  }, [props.text, props.unProcessedText, props.finished, props.lang]);

  return (
    <div className={cn('not-prose rounded-lg bg-[#0E0E0E] flex flex-col font-consolas', fontConsolas.className)}>
      <div className='w-auto mr-5 ml-9 my-1 flex flex-row justify-between text-sm'>
        <p className='font-consolas h-8 text-center flex flex-col justify-center border-none'>{language}</p>
        <Button className='m-0 h-8' variant="ghost" onClick={() => {
          handleCopy(props.text + props.unProcessedText);
        }}>
          <Icon.Clipboard className='w-[17px]'/>
          <p className='pl-[5px]'>{"Copy"}</p>
        </Button>
      </div>
      <div className='w-auto h-[1px] bg-secondary'/>
      <pre className="p-0 flex flex-row rounded-lg text-sm ">
        <code className="pt-[5px] pb-[20px] pl-[7px] pr-[7px] text-primary/50 !whitespace-pre select-none border-r-[2px] border-opacity-100 border-secondary">
          {Array(highlights.length + (props.finished ? 0 : unprocessedText.slice(1, unprocessedText.length - 1).length)).fill(20).map((e, line_number: number) => (
              <>
                {line_number + 1}
                {"\n"}
              </>
          ))}
        </code>
        {/* <div className='w-[2px] h-auto bg-secondary'/>
        <div className='w-[4px] h-auto'/> */}
        <ScrollAreaHorizontal className="flex flex-col overflow-y-hidden">
          <div className='pl-[10px] pt-[5px] pb-[20px]'>
            <code className='pt-[20px] pb-[20px] font-consolas text-sm !whitespace-pre cursor-text'>
              {highlights.map((line: scoped_text[], line_number: number) => (
                <>
                  {line.map((token_seg: scoped_text, token_number: number) => (
                    <>
                      {(token_seg.scope[token_seg.scope.length-1] === undefined) ? (
                        <>
                          {token_seg.content}
                        </>
                      ) : (
                        <span key={token_number} id={`hljs ${token_seg.scope[token_seg.scope.length-1]}`} style={{
                          color: (token_seg.scope.length > 0) ?
                                  code_styling.get(token_seg.scope[token_seg.scope.length-1]) :
                                  code_styling.get("default")
                        }}>
                          {token_seg.content}
                        </span>
                      )}
      
                      {(line_number === highlights.length - 1 && token_number === line.length - 1 && unprocessedText.length > 0 && !props.finished) && (
                        <span className="font-consolas text-sm whitespace-pre">
                          {unprocessedText[0]}
                        </span>
                      )}
                    </>
                  ))}
                  {"\n"}
                </>
              ))}
              {(!props.finished) && (
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
            </code>
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollAreaHorizontal>
      </pre>
    </div>
  );
}