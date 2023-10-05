import { useState, useRef, useEffect } from "react";
import {
  Text,
  View,
  Platform,
  StyleSheet
} from "react-native";
// import Katex from "react-native-katex";
// import 'katex/dist/katex.min.css';
import Latex from 'react-latex';
// import '../katex/dist/katex.min.css';
// import { InlineMath, BlockMath } from 'react-katex';
// import * as katex from 'katex';
// import katex from "katex/dist/katex.mjs";
import katex from "../katex/dist/katex";
// import '../../assets/katex.min.css';
// import Late
import renderLatexInTextAsHTMLString from "react-latex-next/dist/renderLatex";
import { InlineMath, BlockMath } from "../react-katex/src";
import MarkdownLatex from "./MarkdownLatex";
// import Kate

type textSegment = {
  text: string,
  type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline"
}

// function splitStringArrayRegex(stringArrayIn: string[], regexIn : RegExp) {
  
// }
type MarkdownTextAtomicProps = {
  textSeg : textSegment
}

export default function MarkdownTextAtomic(props : MarkdownTextAtomicProps){

  return (
      <Text selectable={true}>
      {(props.textSeg.type === "mathjax_inline") && (
          // <Katex 
          //   expression={props.textSeg.text}
          //   // style={styles.katex}
          //   // inlineStyle={inlineStyle}
          //   displayMode={false}
          //   throwOnError={false}
          //   errorColor="#f00"
          //   macros={{}}
          //   colorIsTextColor={false}
          //   // onLoad={() => setLoaded(true)}
          //   // onError={() => console.error('Error')
          // />
          // <Latex delimiters={[
          //   { left: '$$', right: '$$', display: false},
          //   { left: '$', right: '$', display: false },
          // ]}>{"$"+props.textSeg.text+"$"}</Latex>
          // <InlineMath math={props.textSeg.text}/>
          <Text style={{fontWeight: 'bold'}}>

          <MarkdownLatex textSeg={props.textSeg} type={"inline"}/>
          </Text>
          // <Latex output={"mathml"}>{"$$a^2_a$$"}</Latex>
      )}
      {(props.textSeg.type === "mathjax_newline") && (
          // <Text selectable={true}>{props.textSeg.text}</Text>
          // <Latex output="Mathml">{"$$"+props.textSeg.text+"$$"}</Latex>
          // <Latex>{"$$a^2_a$$"}</Latex>
          // katex.render(props.textSeg.text)
          <MarkdownLatex textSeg={props.textSeg} type={"newline"}/>
          // <div dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
          //   output: 'mathml',
          //   throwOnError: false,
          //   displayMode: true
          // })}} />
      )}
      {(props.textSeg.type === "bold") && (
          <Text selectable={true}><b>{props.textSeg.text}</b></Text>
      )}
      {(props.textSeg.type === "italic") && (
          <Text selectable={true} style={{fontStyle: 'italic'}}>{props.textSeg.text}</Text>
      )}
      {(props.textSeg.type === "bolditalic") && (
          <Text selectable={true} style={{fontStyle: 'italic'}}><b>{props.textSeg.text}</b></Text>
      )}
      {(props.textSeg.type === "regular") && (
          <Text selectable={true}>{props.textSeg.text}</Text>
      )}
      </Text>
  );
}