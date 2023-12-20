// import {
//   Text,
//   View,
//   Platform
// } from "react-native";
// import katex from "../katex/dist/katex";
// import * as katex from "katex";
import katex from "katex/dist/katex.mjs";
// import RenderHTML from "react-native-render-html";

import { useEffect } from "react";

// katex.__setFontMetrics("custom-Regular", {});
// katex.__setFontMetrics("Math-Italic", {}); // makeOrd turns all mathematics into "Math-Italic" regardless of requested font
// katex.__setFontMetrics("AMS-Regular", {});
// import React from 'react';
// import katex from 'katex';
// import markedKatex from "marked-katex-extension";
// import 'katex/dist/katex.min.css';

type MarkdownLatexProps = {
  textSeg : {text: string},
  type: "inline" | "newline"
}

export default function MarkdownLatex(props : MarkdownLatexProps){
  const throwOnError = false;
  
  useEffect(() => {
    console.log("Rendering to string:", katex.renderToString("x^2"))
  }, []);
  // let latex_html = katex.renderToString(props.textSeg.text, {
  //   output: 'mathml',
  //   throwOnError: throwOnError,
  //   displayMode: false
  // });
  // console.log(latex_html);

  useEffect(() => {
    console.log("MarkdownLatex got text:", props.textSeg.text);
  }, [props.textSeg.text]);

	// return (
	// 	<span>{props.textSeg.text}</span>
	// );

  try {
    if (props.type === "inline") {
      return (
        // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
        <span dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
          output: 'mathml',
          throwOnError: throwOnError,
          displayMode: false
        })}} style={{paddingLeft: 2, paddingRight: 2, paddingTop: 10, paddingBottom: 10, width: '100%'}}/>
      );
    } else {
      return (
        // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
        <div style={{
          display: "flex",
          flexGrow: 1,
        }}>
          <span>{"\n"}</span>
          <span dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
            output: 'mathml',
            throwOnError: throwOnError,
            displayMode: true
          })}} style={{
            paddingTop: 10, 
            paddingBottom: 10, 
            width: '100%', 
            display: "inline-block", 
            whiteSpace: "wrap",
            clear: "both",
            fontFamily: "Consolas"
          }}/>
        </div>
      );
    }
  } catch (error) {
    return (
      <p>{props.textSeg.text}</p>
    );
  }
}