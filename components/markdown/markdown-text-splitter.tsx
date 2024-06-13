"use client";
import { useState, useEffect } from "react";
import MarkdownTextAtomic from "./markdown-text-atomic";
import { cn } from "@/lib/utils";

const escape_replace = [
	[/\%/g, "%"],
	[/\\\*/g, "*"],
	[/\\\`/g, "`"],
	[/\\\$/g, "$"]
]

function escape_text(text : string) {
	for (let i = 0; i < escape_replace.length; i++) {
		text = text.replaceAll(escape_replace[i][0], `-%${i}%-`);
	}
	return text;
}

function unescape_text(text : string) {
	for (let i = escape_replace.length - 1; i >= 0; i--) {
		text = text.replaceAll(`-%${i}%-`, escape_replace[i][1] as string);
	}
	return text;
}


function parseText(text : string) {
	text = escape_text(text);

	const all_md_patterns = /(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|\~\~.*?\~\~|`.*?`|\[.*?\]\(.*?\))/;
  let match : RegExpMatchArray | null = text.match(all_md_patterns);
  let index = 0;
  const string_segments : textSegment[] = [];
  if (match === null) {
      string_segments.push({
          text: unescape_text(text),
          type: "regular"
      });
  }
  while (match !== null && match !== undefined && match.index !== undefined) {
		// console.log("match:", match);
		if (match.index > 0) {
			// console.log()
			string_segments.push({
				text: unescape_text(text.slice(index, index+match.index)),
				type: "regular"
			})
		}
		if (match[0].length > 6 && match[0].slice(0, 3) === "***") {
			string_segments.push({
				text: unescape_text(match[0].slice(3, match[0].length-3)),
				type: "bolditalic"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "**") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
				type: "bold"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "$$") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
				type: "mathjax_newline"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "~~") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
				type: "strikethrough"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 1) === "[" && match[0].length > 2) {
			const linkMatch = match[0].match(/\([^\)]*\)$/);
			
			if (linkMatch) {
				const textMatch = match[0].slice(0, match[0].length - linkMatch[0].length);
				let text = textMatch;
				text = text.slice(1, text.length - 1);
				let link = linkMatch[0];
				link = link.slice(1, link.length - 1);
				string_segments.push({
					text: text,
					link: link,
					type: "anchor"
				});
			}
		}
		else if (match[0].length > 2 && match[0].slice(0, 1) === "*") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
				type: "italic"
			});
		}
		
		else if (match[0].length > 2 && match[0].slice(0, 1) === "$" && match[0][match[0].length-2] !== " " && match[0][1] !== " ") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
				type: "mathjax_inline"
			});
		}
		else if (match[0].length > 2 && match[0].slice(0, 1) === "`") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
				type: "codespan"
			});
		} else {
			string_segments.push({
				text: unescape_text(match[0]),
				type: "regular"
			});
		}
		// if (match === undefined) {}
		const new_index = index+match[0].length+match.index;
		const new_match = text.slice(new_index).match(all_md_patterns);
		if (new_match === null && new_index < text.length) {
			string_segments.push({
				text: unescape_text(text.slice(new_index)),
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
    className?: string,
    text: string,
}

export type textSegment = {
    text: string,
    link?: string
    type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline" | "codespan" | "anchor" | "strikethrough"
}

export default function MarkdownTextSplitter(props : MarkdownTextSplitterProps){
//   const [textSplit, setTextSplit] = useState<textSegment[]>([]);
//   useEffect(() => {
//     const string_segments = parseText(props.text);
//     // console.log("Text splitter got text:", props.text, string_segments);
//     setTextSplit(string_segments);
//   }, [props.text]);

  return (
    <>
      {parseText(props.text).map((v : textSegment, k : number) => (
        <MarkdownTextAtomic key={k} textSeg={v}/>
      ))}
    </>
  );
}