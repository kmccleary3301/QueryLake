"use client";
import { ScrollAreaHorizontal } from "@/components/ui/scroll-area";
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
      return (
        // <div className="items-center w-auto">
          <ScrollAreaHorizontal>
            <TeX as={"span"} block className="word-break whitespace-pre-wrap" math={props.textSeg.text} />
          </ScrollAreaHorizontal>
        // </div>
      );
    }
  } catch (error) {
    return (
      <p>{props.textSeg.text}</p>
    );
  }
}