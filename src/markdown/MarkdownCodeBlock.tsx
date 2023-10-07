import {
  Text,
  View
} from "react-native";
import { TextInput } from "react-native-gesture-handler";
import hljs from 'highlight.js';
import { useEffect, useState } from "react";
import { defaultHTMLElementModels, RenderHTML } from "react-native-render-html";
  
type MarkdownCodeBlockProps = {
  text : string,
}

const tagsStyles = {
  ".hljs-keyword": {
    whiteSpace: 'normal',
    color: 'gray'
  },
  span: {
    color: 'green'
  }
}

type scoped_text = {
  scope: string[],
  content: string
};

type parser_segment = scoped_text | "\n";

function decode_html(input : string) {
  input = input.replace('&amp;', '&');
  input = input.replace('&lt;', "\<");
  input = input.replace('&gt;', "\>");
  input = input.replace('&quot;', "\"");
  return input;
}

function parseScopeTreeText(hljs_html : string) {
  /*
   * Let's not discuss this lmao.
   */

  let match = hljs_html.match(/(\<.*?\>)/);
  let current_scope : string[] = [];
  let index = 0;
  let return_segments : scoped_text[][] = [];
  let string_segments : parser_segment[] = [];
  if (match === null) {
      string_segments.push({
        scope: [],
        content: hljs_html
      });
  }
  while (match !== null) {
    if (match.index > 0) {
        let text = hljs_html.slice(index, index+match.index).split("\n");
        for (let i = 0; i < text.length; i++) {
          if (i !== 0) { 
            string_segments.push("\n") 
          }
          if (text[i].length > 0) {
            string_segments.push({
              scope: current_scope.slice(),
              content: decode_html(text[i])
            })
          }
        }
    }
    let match_open_scope = match[0].match(/(\".*?\")/);
    if (match_open_scope !== null) {
      current_scope.push(match_open_scope[0].slice(1, match_open_scope[0].length-1));
    } else {
      current_scope.pop();
    }
    let new_index = index+match[0].length+match.index;
    let new_match = hljs_html.slice(new_index).match(/(\<.*?\>)/);
    if (new_match === null && new_index < hljs_html.length) {
      let text = hljs_html.slice(new_index).split("\n");
      for (let i = 0; i < text.length; i++) {
        if (i != 0) { 
          string_segments.push("\n")   
        }
        string_segments.push({
          scope: current_scope.slice(),
          content: decode_html(text[i])
        })
      }
    } 
    match = new_match;
    index = new_index;
  }
  index = 0;
  let temp_segments : scoped_text[] = [];
  for (let i = 0; i < string_segments.length; i++) {
    if (string_segments[i] === "\n") {
      // if (temp_segments.length > 0) {
      return_segments.push(temp_segments.slice());
      // }
      temp_segments = [];
      index = i;
    } else {
      temp_segments.push(string_segments[i]);
    }
  }
  return_segments.push(temp_segments.slice());
  return return_segments;
}


const code_styling={
  "hljs-keyword": "#9CDCFE",
  "hljs-function": "#DCDCAA",
  "hljs-meta": "#CE9178",
  "hljs-comment": "#6A9955",
  "hljs-literal": "#569CD6",
  "hljs-string": "#CE9178",
  "hljs-title class_": "#32BBB0",
  "hljs-title function_": "#DCDCFF",
  "hljs-number": "#B5CEA8",
  "hljs-built_in": "#DCDCAA",
  "default": "#DCDCAA",
};

export default function MarkdownCodeBlock(props : MarkdownCodeBlockProps){
  // const throwOnError = false;
  // const highlights = hljs.highlightAuto(props.text);
  // const highlighted = hljs.highlightBlock;
  // console.log(highlights);null
  
  const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  const [lang, setLang] = useState<string | undefined>("");
  const [textLines, setTextLines] = useState<string[]>([]);
  // const highlights = hljs.highlightAuto(props.text);
  useEffect(() => {
    
    let highlights_get = hljs.highlightAuto(props.text);
    setLang(highlights_get.language);
    let text_lines = props.text.split("\n");
    setTextLines(text_lines);
    let highlights_make = [];
    console.log(highlights_get.value);
    let scope_tree = parseScopeTreeText(highlights_get.value);
    console.log(scope_tree);
    setHighlights(scope_tree);
    // console.log(highlights_get);
    // console.log(parseScopeTreeText(highlights_get.value));
    // setLang(hljs.getLanguage())
  }, [props.text]);

  // let relevance_scores = [highlights.map((value, key: number) => value.relevance)];
  // console.log(relevance_scores);
  return (
    <View style={{paddingVertical: 10}}>
      <View style={{
        padding: 20,
        borderRadius: 10,
        backgroundColor: '#17181D',
        flexDirection: "column",
        alignItems: 'baseline',
      }}>
      {highlights.map((line: scoped_text[], line_number : number) => (//the value search command below finds index of first non whitespace character
        <View key={line_number} style={{
          flexDirection: 'row',
          flexShrink: 1,
          paddingVertical: 1,
          minHeight: 20, //Empty Line Height
        }}>
          {line.map((token_seg : scoped_text, token_number : number) => (
            <Text key={token_number} style={{color: "#D4D4D4"}}>
              <Text style={{
                color: (token_seg.scope.length > 0)?code_styling[token_seg.scope[token_seg.scope.length-1]]:code_styling["default"],
                fontFamily: 'Consolas',
                fontSize: 16,
              }}>
                {token_seg.content}
              </Text>
            </Text>
          ))}
        </View>
      ))}
        {/* <pre
          class="scrollbar-custom overflow-auto px-5 scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20"><code
            class="language-{lang}">{@html highlightedCode || code.replaceAll("<", "&lt;")}</code></pre> */}
      </View>
    </View>
  );
}