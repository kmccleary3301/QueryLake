import {
  Text,
  View,
  ScrollView
} from "react-native";
import { TextInput } from "react-native-gesture-handler";
import hljs from 'highlight.js';
import { useEffect, useState } from "react";
import { defaultHTMLElementModels, RenderHTML } from "react-native-render-html";

type MarkdownCodeBlockProps = {
  text : string,
  lang?: string,
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
  input = input.replaceAll('\&#x27;', "\'");
  input = input.replaceAll('\&quot;', "\"");
  input = input.replaceAll('\&lt;', "\<");
  input = input.replaceAll('\&gt;', "\>");
  input = input.replaceAll('\&amp;', '&');
  return input;
}


function parseScopeTreeText(hljs_html : string) {
  /*
   * Let's not discuss this lmao.
   */

  console.log("HLJS HTML");
  console.log(hljs_html);
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
    console.log("match:", match[0]);
    if (match.index > 0) {
      let text = hljs_html.slice(index, index+match.index).split("\n");
      console.log("Text");
      console.log(text);
      for (let i = 0; i < text.length; i++) {
        let decoded = decode_html(text[i]);
        if (decoded.length > 0) {
          if (i !== 0) { 
            string_segments.push("\n") 
          }
          if (text[i].length > 0) {
            string_segments.push({
              scope: current_scope.slice(),
              content: decoded
            })
          }
        } else {
          string_segments.push("\n")
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
      console.log("Text");
      console.log(text);
      for (let i = 0; i < text.length; i++) {
        let decoded = decode_html(text[i]);
        if (decoded.length > 0) {
          if (i != 0) { 
            string_segments.push("\n")   
          }
          string_segments.push({
            scope: current_scope.slice(),
            content: decode_html(text[i])
          })
        } else {
          string_segments.push("\n")
        }
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
  const fontSize = 14;
  const [highlights, setHighlights] = useState<scoped_text[][]>([]);
  let textUpdating = false;
  let oldTextLength = 0;
  let [unprocessedText, setUnprocessedText] = useState([""]);

  useEffect(() => {
    setUnprocessedText(props.text.slice(oldTextLength).split("\n"));
    textUpdating = true;
  }, [props.text]);

  setInterval(() => {
    if (textUpdating) {
      let highlights_get = (props.lang)?hljs.highlight(props.text, {"language": props.lang}):hljs.highlightAuto(props.text);
      let scope_tree = parseScopeTreeText(highlights_get.value);
      console.log("HIGHLIGHTING");
      setHighlights(scope_tree);
      oldTextLength = props.text.length;
      textUpdating = false;
      setUnprocessedText([]);
    }
  }, 500);

  return (
    <View style={{paddingVertical: 20, paddingHorizontal: 10}}>
      <ScrollView style={{
        padding: 20,
        borderRadius: 10,
        backgroundColor: '#17181D',
        flexDirection: "column",
        // alignItems: 'baseline',
        maxWidth: '100%'
      }} horizontal={true} showsHorizontalScrollIndicator={false}>
      <View>
      {highlights.map((line: scoped_text[], line_number : number) => (//the value search command below finds index of first non whitespace character
        <View key={line_number} style={{
          flexDirection: 'row',
          flexShrink: 1,
          paddingVertical: 1,
          minHeight: 20, //Empty Line Height
        }}>
          {line.map((token_seg : scoped_text, token_number : number) => (
            <Text selectable={true} key={token_number} style={{color: "#D4D4D4"}}>
              <Text style={{
                color: (token_seg.scope.length > 0)?code_styling[token_seg.scope[token_seg.scope.length-1]]:code_styling["default"],
                fontFamily: 'Consolas',
                fontSize: fontSize,
              }}>
                {token_seg.content}
              </Text>

              {(line_number === highlights.length-1 && token_number === line.length -1) && (
                <Text style={{
                  color: code_styling["default"],
                  fontFamily: 'Consolas',
                  fontSize: fontSize,
                }}>
                  {unprocessedText[0]}
                </Text>
              )}
            </Text>
          ))}
        </View>
      ))}
      {unprocessedText.slice(0, unprocessedText.length-1).map((line: string, line_number : number) => (//the value search command below finds index of first non whitespace character
        <View key={line_number} style={{
          flexDirection: 'row',
          flexShrink: 1,
          paddingVertical: 1,
          minHeight: 20, //Empty Line Height
        }}>
          <Text style={{
            color: code_styling["default"],
            fontFamily: 'Consolas',
            fontSize: fontSize,
          }}>
            {line}
          </Text>

        </View>
      ))}
      </View>
        {/* <pre
          class="scrollbar-custom overflow-auto px-5 scrollbar-thumb-gray-500 hover:scrollbar-thumb-gray-400 dark:scrollbar-thumb-white/10 dark:hover:scrollbar-thumb-white/20"><code
            class="language-{lang}">{@html highlightedCode || code.replaceAll("<", "&lt;")}</code></pre> */}
      </ScrollView>
    </View>
  );
}