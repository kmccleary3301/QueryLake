
// import MarkdownLatex from "./MarkdownLatex";
import MarkdownLatex from "./markdown-latex";

type textSegment = {
  text: string,
  link?: string
  type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline" | "codespan" | "anchor"
}

// function splitStringArrayRegex(stringArrayIn: string[], regexIn : RegExp) {
  
// }
type MarkdownTextAtomicProps = {
  textSeg : textSegment,
}

export default function MarkdownTextAtomic(props : MarkdownTextAtomicProps){


  switch(props.textSeg.type) {
    case "mathjax_newline":
      return (
        <div id="text-atomic-mathjax-newline" style={{
          fontWeight: 'bold', 
          display: "flex", 
          flexGrow: 1, 
          flexDirection: "row", 
          justifyContent: "center"
        }}>
          <MarkdownLatex textSeg={props.textSeg} type={"newline"}/>
        </div>
      );
    case "mathjax_inline":
      return (
        <span id="text-atomic-mathjax-inline" style={{fontWeight: 'bold'}}>
          <MarkdownLatex textSeg={props.textSeg} type={"inline"}/>
        </span>
      );
    case "bold":
      return (
        <p id="text-atomic-bold" style={{textAlign: "left"}}><b>{props.textSeg.text}</b></p>
      );
    case "italic":
      return (
        <span id="text-atomic-italic" style={{fontStyle: 'italic', textAlign: "left"}}>{props.textSeg.text}</span>
      );
    case "bolditalic":
      return (
        <span id="text-atomic-bold-italic" style={{fontStyle: 'italic', textAlign: "left"}}><b>{props.textSeg.text}</b></span>
      );
    case "regular":
      return (
        <span id="text-atomic-regular" style={{textAlign: "left"}}>{props.textSeg.text}</span>
      );
    case "codespan":
      return (
        <span id="text-atomic-codespan" style={{
          fontFamily: 'Consolas',
          fontStyle: 'italic',
          paddingRight: 3,
          textAlign: "left"
        }}>
          {props.textSeg.text}
        </span>
      );
    case "anchor":
      return (
        <span id="text-atomic-anchor" style={{
          // fontStyle: 'italic',
          textDecorationLine: 'underline',
          textAlign: "left",
        }} onClick={() => {
					// Linking.openURL(props.textSeg.link)
					window.open(props.textSeg.link, '_blank');
				}}>
          {props.textSeg.text}
        </span>
      );
  }
}