"use client";
import { cn } from "@/lib/utils";
import MarkdownLatex from "./markdown-latex";
import { fontConsolas } from '@/lib/fonts';
import Link from "next/link";
import { Button } from "@/registry/default/ui/button";
import { textSegment } from "./markdown-text-splitter";

type MarkdownTextAtomicProps = {
  textSeg : textSegment,
}

export default function MarkdownTextAtomic(props : MarkdownTextAtomicProps){


  switch(props.textSeg.type) {
    case "mathjax_newline":
      return (
        <MarkdownLatex textSeg={props.textSeg} type={"newline"}/>
      );
    case "mathjax_inline":
      return (
        <MarkdownLatex textSeg={props.textSeg} type={"inline"}/>
      );
    case "bold":
      return (
        <strong className="font-bold">{props.textSeg.text}</strong>
      );
    case "italic":
      return (
        <em>{props.textSeg.text}</em>
      );
    case "bolditalic":
      return (
        <em><strong className="font-bold">{props.textSeg.text}</strong></em>
      );
    case "regular":
      return (
        <>{props.textSeg.text}</>
      );
    case "codespan":
      return (
        <code className={cn("", fontConsolas.className)}>
          {props.textSeg.text}
        </code>
      );
    case "strikethrough":
      return (
        <del>{props.textSeg.text}</del>
      );
    case "anchor":
      return (
        <a href={props.textSeg.link as string} className="p-0 m-0 text-[#A68AEB] underline-offset-4 hover:underline active:text-[#A68AEB]/90">
            {props.textSeg.text}
        </a>
      );
  }
}