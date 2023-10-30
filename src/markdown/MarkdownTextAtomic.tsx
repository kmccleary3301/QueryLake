import { useState, useRef, useEffect } from "react";
import {
  Text,
  Linking
} from "react-native";
// import Katex from "react-native-katex";
// import 'katex/dist/katex.min.css';
// import Latex from 'react-latex';
// import '../katex/dist/katex.min.css';
// import { InlineMath, BlockMath } from 'react-katex';
// import * as katex from 'katex';
// import katex from "katex/dist/katex.mjs";
// import katex from "../katex/dist/katex";
// import '../../assets/katex.min.css';
// import Late
// import renderLatexInTextAsHTMLString from "react-latex-next/dist/renderLatex";
// import { InlineMath, BlockMath } from "../react-katex/src";
import MarkdownLatex from "./MarkdownLatex";
// import Kate

type textSegment = {
  text: string,
  link?: string
  type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline" | "codespan" | "anchor"
}

// function splitStringArrayRegex(stringArrayIn: string[], regexIn : RegExp) {
  
// }
type MarkdownTextAtomicProps = {
  textSeg : textSegment
}

export default function MarkdownTextAtomic(props : MarkdownTextAtomicProps){


  switch(props.textSeg.type) {
    case "mathjax_newline":
      return (
        <MarkdownLatex textSeg={props.textSeg} type={"newline"}/>
      );
    case "mathjax_inline":
      return (
        <Text style={{fontWeight: 'bold'}}>
          <MarkdownLatex textSeg={props.textSeg} type={"inline"}/>
        </Text>
      );
    case "bold":
      return (
        <Text selectable={true}><b>{props.textSeg.text}</b></Text>
      );
    case "italic":
      return (
        <Text selectable={true} style={{fontStyle: 'italic'}}>{props.textSeg.text}</Text>
      );
    case "bolditalic":
      return (
        <Text selectable={true} style={{fontStyle: 'italic'}}><b>{props.textSeg.text}</b></Text>
      );
    case "regular":
      return (
        <Text selectable={true}>{props.textSeg.text}</Text>
      );
    case "codespan":
      return (
        <Text style={{
          fontFamily: 'Consolas',
          fontStyle: 'italic',
        }} selectable={true}>
          {props.textSeg.text}
        </Text>
      );
    case "anchor":
      return (
        <Text style={{
          // fontStyle: 'italic',
          textDecorationLine: 'underline',
        }} selectable={true} onPress={() => {Linking.openURL(props.textSeg.link)}}>
          {props.textSeg.text}
        </Text>
      );
  }
}