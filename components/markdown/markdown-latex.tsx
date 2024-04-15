"use client";
import TeX from "@matejmazur/react-katex";
import "katex/dist/katex.min.css";

type MarkdownLatexProps = {
  textSeg : {text: string},
  type: "inline" | "newline"
}

export default function MarkdownLatex(props : MarkdownLatexProps){
  const throwOnError = false;

  try {
    if (props.type === "inline") {
      return <TeX math={props.textSeg.text} />;
    } else {
      return <TeX className="w-full" block math={props.textSeg.text} />;
    }
  } catch (error) {
    return (
      <p>{props.textSeg.text}</p>
    );
  }
}