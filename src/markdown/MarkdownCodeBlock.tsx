import {
  Text,
  View
} from "react-native";
import { TextInput } from "react-native-gesture-handler";
import hljs from 'highlight.js';
  
type MarkdownCodeBlockProps = {
  text : string,
}

export default function MarkdownCodeBlock(props : MarkdownCodeBlockProps){
  const throwOnError = false;
  const highlights = hljs.highlightAuto(props.text);
  // const highlighted = hljs.highlightBlock;
  console.log(highlights);
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
      <div id='code'>
        <div dangerouslySetInnerHTML={{ __html: highlights.value}} />
      </div>
      
      </View>
  );
}