"use client";
import { useState, useEffect } from "react";
import MarkdownTextAtomic from "./markdown-text-atomic";
import { cn } from "@/lib/utils";
import { segment_types } from "./configs";

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

const all_md_patterns = /(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|\~\~.*?\~\~|`.*?`|\[.*?\]\(.*?\)|\\\[.*?\\\]|\\\(.*?\\\))/;

function parseText(text : string) {
	text = escape_text(text);

  let match : RegExpMatchArray | null = text.match(all_md_patterns);
  let index = 0;
  const string_segments : textSegment[] = [];
  if (match === null) {
    string_segments.push({
      text: unescape_text(text),
      raw_text: unescape_text(text),
      type: "regular"
    });
  }
  while (match !== null && match !== undefined && match.index !== undefined) {
		// console.log("match:", match);
		if (match.index > 0) {
			// console.log()
			string_segments.push({
				text: unescape_text(text.slice(index, index+match.index)),
        raw_text: unescape_text(text.slice(index, index+match.index)),
				type: "regular"
			})
		}
		if (match[0].length > 6 && match[0].slice(0, 3) === "***") {
			string_segments.push({
				text: unescape_text(match[0].slice(3, match[0].length-3)),
        raw_text: unescape_text(match[0]),
				type: "bolditalic"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "**") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
        raw_text: unescape_text(match[0]),
				type: "bold"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "$$") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
        raw_text: unescape_text(match[0]),
				type: "double_dollar"
			});
		}
		else if (match[0].length > 4 && match[0].slice(0, 2) === "~~") {
			string_segments.push({
				text: unescape_text(match[0].slice(2, match[0].length-2)),
        raw_text: unescape_text(match[0]),
				type: "strikethrough"
			});
		}
    else if (match[0].length > 4 && unescape_text(match[0].slice(0, 2)) === "\\\[") {
      string_segments.push({
        text: unescape_text(match[0].slice(2, match[0].length-2)),
        raw_text: unescape_text(match[0]),
				type: "escaped_square_brackets"
      });
      console.log("Got square brackets:", string_segments[string_segments.length-1]);
    }
    else if (match[0].length > 4 && unescape_text(match[0].slice(0, 2)) === "\\\[") {
      string_segments.push({
        text: unescape_text(match[0].slice(2, match[0].length-2)),
        raw_text: unescape_text(match[0]),
				type: "escaped_parentheses"
        });
      console.log("Got parentheses:", string_segments[string_segments.length-1]);
    }
		else if (match[0].length > 4 && match[0].slice(0, 1) === "[" && match[0].length > 2) {
      // Link case.

			const linkMatch = match[0].match(/\([^\)]*\)$/);
			
			if (linkMatch) {
				const textMatch = match[0].slice(0, match[0].length - linkMatch[0].length);
				let text = textMatch;
				text = text.slice(1, text.length - 1);
				let link = linkMatch[0];
				link = link.slice(1, link.length - 1);
				string_segments.push({
					text: text,
          raw_text: unescape_text(match[0]),
					link: link,
					type: "anchor"
				});
			}
		}
		else if (match[0].length > 2 && match[0].slice(0, 1) === "*") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
        raw_text: unescape_text(match[0]),
				type: "italic"
			});
		}
		else if (match[0].length > 2 && match[0].slice(0, 1) === "$" && match[0][match[0].length-2] !== " " && match[0][1] !== " ") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
        raw_text: unescape_text(match[0]),
				type: "single_dollar"
			});
		}
		else if (match[0].length > 2 && match[0].slice(0, 1) === "`") {
			string_segments.push({
				text: unescape_text(match[0].slice(1, match[0].length-1)),
        raw_text: unescape_text(match[0]),
				type: "codespan"
			});
		} else {
			string_segments.push({
				text: unescape_text(match[0]),
        raw_text: unescape_text(match[0]),
				type: "regular"
			});
		}


		// if (match === undefined) {}
		const new_index = index+match[0].length+match.index;
		const new_match = text.slice(new_index).match(all_md_patterns);
		if (new_match === null && new_index < text.length) {
      console.log("Pushing remaining text:", text.slice(new_index));
			string_segments.push({
				text: unescape_text(text.slice(new_index)),
        raw_text: unescape_text(text.slice(new_index)),
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
    raw_text: string,
    link?: string
    type: segment_types
}

export default function MarkdownTextSplitter({
  selectable = true,
  className = "",
  text,
  config = "obsidian",
}:{
  selectable?: boolean,
  className?: string,
  text: string,
  config?: "obsidian" | "chat",
}){

  const segments = parseText(text);

  useEffect(() => {
    console.log("segments", segments);
  }, [text])

  return (
    <>
      {segments.map((v : textSegment, k : number) => (
        <MarkdownTextAtomic key={k} textSeg={v} config={config}/>
      ))}
    </>
  );
}