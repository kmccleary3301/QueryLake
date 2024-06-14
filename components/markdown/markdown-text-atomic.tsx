"use client";
import { cn } from "@/lib/utils";
import MarkdownLatex from "./markdown-latex";
import { fontConsolas } from '@/lib/fonts';
import Link from "next/link";
import { Button } from "@/registry/default/ui/button";
import { textSegment } from "./markdown-text-splitter";
import { CHAT_RENDERING_STYLE, OBSIDIAN_MARKDOWN_RENDERING_CONFIG } from "./configs";
import { useEffect } from "react";

export default function MarkdownTextAtomic({
  textSeg,
  config="obsidian"
}:{
  textSeg: textSegment,
  config?: "obsidian" | "chat"
}){

  const config_map = (config === "obsidian") ? OBSIDIAN_MARKDOWN_RENDERING_CONFIG : CHAT_RENDERING_STYLE;

  const text_segment_lookup = config_map[textSeg.type];

  switch(text_segment_lookup) {
    case "bold":
      return (
        <strong className="font-bold">{textSeg.text}</strong>
      );
    case "italic":
      return (
        <em>{textSeg.text}</em>
      );
    case "bolditalic":
      return (
        <em><strong className="font-bold">{textSeg.text}</strong></em>
      );
    case "regular":
      return (
        <>{textSeg.raw_text}</>
      );
    case "codespan":
      return (
        <code className={cn("", fontConsolas.className)}>
          {textSeg.text}
        </code>
      );
    case "strikethrough":
      return (
        <del>{textSeg.text}</del>
      );
    case "anchor":
      return (
        <a href={textSeg.link as string} className="p-0 m-0 text-[#A68AEB] underline-offset-4 hover:underline active:text-[#A68AEB]/90">
          {textSeg.text}
        </a>
      );
    case "newline_math":
      return (
        <MarkdownLatex textSeg={textSeg} type={"newline"}/>
      );
    case "inline_math":
      return (
        <MarkdownLatex textSeg={textSeg} type={"inline"}/>
      );
    default:
      return (
        <>{textSeg.raw_text}</>
      );
  }
}