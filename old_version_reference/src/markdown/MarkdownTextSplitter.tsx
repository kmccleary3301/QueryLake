import { Text } from "react-native";
import { useState, useEffect } from "react";
// import Katex from "react-native-katex";
import MarkdownTextAtomic from "./MarkdownTextAtomic";

function parseText(text : string) {
  let match = text.match(/(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|\`.*?\`|\[.*?\]\(.*?\))/);
  let index = 0;
  let string_segments : textSegment[] = [];
  if (match === null) {
      string_segments.push({
          text: text,
          type: "regular"
      });
  }
  while (match !== null) {
      if (match.index > 0) {
          // console.log()
          string_segments.push({
              text: text.slice(index, index+match.index),
              type: "regular"
          })
      }
      if (match[0].length > 6 && match[0].slice(0, 3) === "***") {
          string_segments.push({
              text: match[0].slice(3, match[0].length-3),
              type: "bolditalic"
          });
      }
      else if (match[0].length > 4 && match[0].slice(0, 2) === "**") {
          string_segments.push({
              text: match[0].slice(2, match[0].length-2),
              type: "bold"
          });
      }
      else if (match[0].length > 4 && match[0].slice(0, 2) === "$$") {
          string_segments.push({
              text: match[0].slice(2, match[0].length-2),
              type: "mathjax_newline"
          });
      }
      else if (match[0].length > 4 && match[0].slice(0, 1) === "\[" && match[0].length > 2) {
          let text = match[0].match(/\[.*?\]/)[0];
          text = text.slice(1, text.length-1);
          let link = match[0].match(/\(.*?\)/)[0];
          link = link.slice(1, link.length-1);
          string_segments.push({
              text: text,
              link: link,
              type: "anchor"
          });
      }
      else if (match[0].length > 2 && match[0].slice(0, 1) === "*") {
          string_segments.push({
              text: match[0].slice(1, match[0].length-1),
              type: "italic"
          });
      }
      else if (match[0].length > 2 && match[0].slice(0, 1) === "$") {
          string_segments.push({
              text: match[0].slice(1, match[0].length-1),
              type: "mathjax_inline"
          });
      }
      else if (match[0].length > 2 && match[0].slice(0, 1) === "\`") {
          string_segments.push({
              text: match[0].slice(1, match[0].length-1),
              type: "codespan"
          });
      } else {
          string_segments.push({
              text: match[0],
              type: "regular"
          });
      }
      let new_index = index+match[0].length+match.index;
      let new_match = text.slice(new_index).match(/(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|\`.*?\`|\[.*?\]\(.*?\))/);
      if (new_match === null && new_index < text.length) {
          string_segments.push({
              text: text.slice(new_index),
              type: "regular"
          })
      }
      
      match = new_match;
      index = new_index;
  }
  return string_segments;
}

type MarkdownTextSplitterProps = {
    selectable?: boolean,
    style?: React.CSSProperties,
    text: string,
    bubbleWidth: number,
}

type textSegment = {
    text: string,
    link?: string
    type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline" | "codespan" | "anchor"
}

export default function MarkdownTextSplitter(props : MarkdownTextSplitterProps){
  const [textSplit, setTextSplit] = useState<textSegment[]>([]);
  useEffect(() => {
    let string_segments = parseText(props.text);
    setTextSplit(string_segments);
  }, [props.text]);
  return (
    <Text selectable={true} style={(props.style)?props.style:{}}>
      {textSplit.map((v : textSegment, k : number) => (
        <MarkdownTextAtomic key={k} textSeg={v} bubbleWidth={props.bubbleWidth}/>
      ))}
    </Text>
  );
}