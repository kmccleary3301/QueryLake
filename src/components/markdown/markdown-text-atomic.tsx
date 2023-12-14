
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
        <MarkdownLatex textSeg={props.textSeg} type={"newline"}/>
      );
    case "mathjax_inline":
      return (
        <p style={{fontWeight: 'bold'}}>
          <MarkdownLatex textSeg={props.textSeg} type={"inline"}/>
        </p>
      );
    case "bold":
      return (
        <p><b>{props.textSeg.text}</b></p>
      );
    case "italic":
      return (
        <p style={{fontStyle: 'italic'}}>{props.textSeg.text}</p>
      );
    case "bolditalic":
      return (
        <p style={{fontStyle: 'italic'}}><b>{props.textSeg.text}</b></p>
      );
    case "regular":
      return (
        <p>{props.textSeg.text}</p>
      );
    case "codespan":
      return (
        <p style={{
          fontFamily: 'Consolas',
          fontStyle: 'italic',
          paddingRight: 3,
        }}>
          {props.textSeg.text}
        </p>
      );
    case "anchor":
      return (
        <p style={{
          // fontStyle: 'italic',
          textDecorationLine: 'underline',
        }} onClick={() => {
					// Linking.openURL(props.textSeg.link)
					window.open(props.textSeg.link, '_blank');
				}}>
          {props.textSeg.text}
        </p>
      );
  }
}