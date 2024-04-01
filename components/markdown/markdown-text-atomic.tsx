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
        <strong>{props.textSeg.text}</strong>
      );
    case "italic":
      return (
        <em>{props.textSeg.text}</em>
      );
    case "bolditalic":
      return (
        <em><strong>{props.textSeg.text}</strong></em>
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
        <Link href={props.textSeg.link as string}>
          <Button variant="link" className="pl-0 pr-0 text-[#A68AEB]">
            <p className="prose">
              {props.textSeg.text}
            </p>
          </Button>
        </Link>
      );
  }
}