// import {
//   Text,
//   View,
//   ScrollView
// } from "react-native";
// import { TextInput } from "react-native-gesture-handler";
import hljs from 'highlight.js';
import { useEffect, useState, useRef } from "react";
// import { defaultHTMLElementModels, RenderHTML } from "react-native-render-html";
// import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area"

type MarkdownCodeBlockProps = {
  text : string,
  unProcessedText: string,
  lang?: string,
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

  console.log("HLJS HTML");
  console.log(hljs_html);
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

const code_styling = new Map<string, string>([
  ["hljs-keyword", "#9CDCFE"],
  ["hljs-function", "#DCDCAA"],
  ["hljs-meta", "#CE9178"],
  ["hljs-comment", "#6A9955"],
  ["hljs-literal", "#569CD6"],
  ["hljs-string", "#CE9178"],
  ["hljs-title class_", "#32BBB0"],
  ["hljs-title function_", "#DCDCFF"],
  ["hljs-number", "#B5CEA8"],
  ["hljs-built_in", "#DCDCAA"],
  ["default", "#DCDCAA"],
]);

export default function MarkdownCodeBlock(props : MarkdownCodeBlockProps){
  const fontSize = 14;
  const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  const [lineOffsets, setLineOffsets] = useState<number[]>([]);
  // let textUpdating = false;
  // let oldTextLength = 0;
  const [unprocessedText, setUnprocessedText] = useState<string[]>([]);
  // const [oldInputLength, setOldInputLength] = useState(0);
  // const [rawCode, setRawCode] = useState(props.text+props.unProcessedText);
  // const [lastRefreshTime, setLastRefreshTime] = useState(Date.now());

	const lastRefreshTime = useRef(Date.now());
	const oldInputLength = useRef(0);

  const refreshInterval = 250; // In milliseconds

  useEffect(() => {
    // setRawCode(raw_code);
    let raw_code = props.text+props.unProcessedText;
    const unprocessed_text = raw_code.slice(oldInputLength.current);
    if (props.finished) {
      raw_code = props.text;
    }

    console.log("Highlighting raw code:", raw_code)
    setLineOffsets(getLineOffsets(raw_code));
    if (oldInputLength.current === 0 || (Date.now() - lastRefreshTime.current) > refreshInterval) {
      const highlights_get = (props.lang)?hljs.highlight(props.text, {"language": props.lang}):hljs.highlightAuto(raw_code.replaceAll(/\n[\s|\t]+/g, "\n"));
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

  const getLineOffsets = (string_in : string) => {
    const lines = string_in.split("\n");
    const lineOffsets = [];
    // console.log("Splitting lines:", [string_in], lines);
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const beginning_match = line.match(/^[\s]*/);
      if (beginning_match === null) {
        lineOffsets.push(0);
        continue;
      }
      const tab_count = beginning_match[0].split("\t").length - 1;
      const space_count = beginning_match[0].split(" ").length - 1;
      // console.log([beginning_match[0]])
      // console.log("Line", [line], "match:", [beginning_match[0]], [tab_count, space_count]);
      lineOffsets.push(2*tab_count + space_count);
    }
    // console.log("Total offsets:", lineOffsets);
    return lineOffsets;
  };

  return (
    <div style={{
			paddingTop: 10,
			paddingBottom: 10,
			paddingLeft: 10,
			paddingRight: 10,
      display: 'flex',
      flexDirection: "row",
      borderRadius: 10,
      backgroundColor: '#17181D',
		}}>
      <div style={{display: "flex", flexDirection: "column"}}>
      {Array(highlights.length + (props.finished?0:unprocessedText.slice(1, unprocessedText.length-1).length)).fill(20).map((e, line_number : number) => (
        <span key={line_number} style={{
					display: 'flex',
          flexDirection: 'row',
          flexShrink: 1,
					paddingTop: 1,
					paddingBottom: 1,
          // paddingLeft: lineOffsets[line_number] * 4,
          minHeight: e, //Empty Line Height, literally just using e to avoid the warning "e is unused".
        }}>
          <span style={{
            userSelect: "none",
            color: "#E8E3E3",
            opacity: 0.5,
            fontSize: fontSize,
            whiteSpace: "pre",
            width: 30,
            height: 25,
            paddingTop: 3,
            textAlign: "right",
            paddingLeft: 0,
            paddingRight: 5,
          }}>{line_number}</span></span>
      ))}
      </div>
      <ScrollArea style={{
        // padding: 20,
        paddingBottom: 20,
				display: 'flex',
        flexDirection: "column",
        // alignItems: 'baseline',
        maxWidth: '100%'
      }}>
      <div>
      {highlights.map((line: scoped_text[], line_number : number) => (//the value search command below finds index of first non whitespace character
        <span key={line_number} style={{
					display: 'flex',
          flexDirection: 'row',
          flexShrink: 1,
					paddingTop: 1,
					paddingBottom: 1,
          // paddingLeft: lineOffsets[line_number] * 4,
          paddingLeft: 10,
          minHeight: 20, //Empty Line Height
        }}>
          <span style={{
            userSelect: "none",
            color: "#E8E3E3",
            opacity: 0.5,
            fontSize: fontSize,
            whiteSpace: "pre",
            height: 25,
            paddingTop: 3,
          }}/>
          {/* <span style={{whiteSpace: "pre"}}>{Array(lineOffsets[line_number]).fill(" ").join("")}</span> */}
          {line.map((token_seg : scoped_text, token_number : number) => (
            <span key={token_number} style={{color: "#D4D4D4"}}>
              <span style={{
                color: (token_seg.scope.length > 0)?code_styling.get(token_seg.scope[token_seg.scope.length-1]):code_styling.get("default"),
                fontFamily: 'Consolas',
                fontSize: fontSize,
                whiteSpace: "pre",
                // paddingRight: 10,
              }}>
                {token_seg.content}
              </span>

              {(line_number === highlights.length-1 && token_number === line.length -1 && unprocessedText.length > 0 && !props.finished) && (
                <span style={{
                  color: code_styling.get("default"),
                  fontFamily: 'Consolas',
                  fontSize: fontSize,
                  whiteSpace: "pre",
                }}>
                  {unprocessedText[0]}
                </span>
              )}
            </span>
          ))}
        </span>
      ))}
      {(!props.finished) && (
        <>
        {unprocessedText.slice(1, unprocessedText.length-1).map((line: string, line_number : number) => (//the value search command below finds index of first non whitespace character
          <span key={line_number} style={{
						display: 'flex',
            flexDirection: 'row',
            flexShrink: 1,
            textAlign: 'left',
						paddingTop: 1,
						paddingBottom: 1,
            paddingLeft: lineOffsets[line_number + highlights.length] * 10,
            minHeight: 20, //Empty Line Height
          }}>
            <span style={{
              color: code_styling.get("default"),
              fontFamily: 'Consolas',
              fontSize: fontSize,
            }}>
              {line}
            </span>

          </span>
        ))}
        </>
      )}
      </div>
        {/* <pre
          class="scrollbar-custom overflow-auto px-5 scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20"><code
            class="language-{lang}">{@html highlightedCode || code.replaceAll("<", "&lt;")}</code></pre> */}
			<ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}