// import {
//   Text,
//   View,
//   Platform
// } from "react-native";
// import katex from "../katex/dist/katex";
// import RenderHTML from "react-native-render-html";

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
  // const throwOnError = false;

  // let latex_html = katex.renderToString(props.textSeg.text, {
  //   output: 'mathml',
  //   throwOnError: throwOnError,
  //   displayMode: false
  // });
  // console.log(latex_html);

	return (
		<p>{props.textSeg.text}</p>
	);

  // try {
  //   if (props.type === "inline") {
  //     return (
  //       // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
  //       <span dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
  //         output: 'mathml',
  //         throwOnError: throwOnError,
  //         displayMode: false
  //       })}} style={{paddingTop: 10, paddingBottom: 10, width: '100%'}}/>
  //     );
  //   } else {
  //     return (
  //       // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
  //       <div style={{
  //         width: props.bubbleWidth-20,
  //         alignSelf: 'center'
  //       }}>
  //         <div dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
  //           output: 'mathml',
  //           throwOnError: throwOnError,
  //           displayMode: true
  //         })}} style={{paddingTop: 10, paddingBottom: 10, width: '100%'}}/>
  //       </div>
  //     );
  //   }
  // } catch (error) {
  //   return (
  //     <p>{props.textSeg.text}</p>
  //   );
  // }
}