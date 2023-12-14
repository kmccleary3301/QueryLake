import {
  Text,
  View,
  Platform
} from "react-native";
import katex from "../katex/dist/katex";
import RenderHTML from "react-native-render-html";

// katex.__setFontMetrics("custom-Regular", {});
// katex.__setFontMetrics("Math-Italic", {}); // makeOrd turns all mathematics into "Math-Italic" regardless of requested font
// katex.__setFontMetrics("AMS-Regular", {});

type MarkdownLatexProps = {
  textSeg : {text: string},
  type: "inline" | "newline",
  bubbleWidth: number
}

export default function MarkdownLatex(props : MarkdownLatexProps){
  const throwOnError = false;
  if (Platform.select({web: false, default: true})) {
    return (
      <Text selectable={true}>{props.textSeg.text}</Text>
    );
  }

  let latex_html = katex.renderToString(props.textSeg.text, {
    output: 'mathml',
    throwOnError: throwOnError,
    displayMode: false
  });
  // console.log(latex_html);

  try {
    if (props.type === "inline") {
      return (
        // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
        <span dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
          output: 'mathml',
          throwOnError: throwOnError,
          displayMode: false
        })}} style={{paddingTop: 10, paddingBottom: 10, width: '100%'}}/>
      );
    } else {
      return (
        // <RenderHTML contentWidth={20} source={{ html: latex_html}}/>
        <View style={{
          width: props.bubbleWidth-20,
          alignSelf: 'center'
        }}>
          <div dangerouslySetInnerHTML={{ __html: katex.renderToString(props.textSeg.text, {
            output: 'mathml',
            throwOnError: throwOnError,
            displayMode: true
          })}} style={{paddingTop: 10, paddingBottom: 10, width: '100%'}}/>
        </View>
      );
    }
  } catch (error) {
    return (
      <Text selectable={true}>{props.textSeg.text}</Text>
    );
  }
}