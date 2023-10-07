import {
  Text,
  View
} from "react-native";
import { TextInput } from "react-native-gesture-handler";
import hljs from 'highlight.js';
import { useEffect, useState } from "react";
  
type MarkdownCodeBlockProps = {
  text : string,
}

export default function MarkdownCodeBlock(props : MarkdownCodeBlockProps){
  // const throwOnError = false;
  // const highlights = hljs.highlightAuto(props.text);
  // const highlighted = hljs.highlightBlock;
  // console.log(highlights);
  const [highlights, setHighlights] = useState("");
  const [lang, setLang] = useState("");
  // const highlights = hljs.highlightAuto(props.text);
  useEffect(() => {
    setHighlights(hljs.highlightAuto(props.text).value);
    // setLang(hljs.getLanguage())
  }, [props.text]);

  // let relevance_scores = [highlights.map((value, key: number) => value.relevance)];
  // console.log(relevance_scores);
  return (
      <View style={{
        padding: 10,
        borderRadius: 10,
        // backgroundColor: '#17181D'
      }}>
      {/* <TextInput

      /> */}
      {/* <div id='code'>
        <div dangerouslySetInnerHTML={{ __html: highlights.value}} />
      </div> */}
      <code lang="python" dangerouslySetInnerHTML={{__html: highlights}}/>
        {/* <pre
          class="scrollbar-custom overflow-auto px-5 scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20"><code
            class="language-{lang}">{@html highlightedCode || code.replaceAll("<", "&lt;")}</code></pre> */}
      </View>
  );
}