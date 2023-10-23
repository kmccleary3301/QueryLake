import { useState, useRef, useEffect } from "react";
import {
  Text,
  View,
  Platform,
  StyleSheet
} from "react-native";
// import { Marked } from "marked";
import { marked, TokensList, Token, Tokens } from 'marked';
import MarkdownTextSplitter from "./MarkdownTextSplitter";
import MarkdownCodeBlock from "./MarkdownCodeBlock";
import stringHash from "../hooks/stringHash";
// import {KateX}

// marked.use({
//   renderer: {
//     codespan: (code) => {
//       if (code[0] == '$') {
//         return katex.renderToString(code.slice(1), {throwOnError: false})
//       }

//       return false
//     }
//   }
// })

// marked.use({
//   tokenizer: {
//     inlineText(src : string, inRawBlock) {
//       const cap = src.match(/^([`$]+|[^`$])(?:[\s\S]*?(?:(?=[\\<!\[`$*]|\b_|$)|[^ ](?= {2,}\n))|(?= {2,}\n))/);
//         if (cap) {
//           var text;
//           if (inRawBlock) {
//             text = this.options.sanitize ? this.options.sanitizer ? this.options.sanitizer(cap[0]) : cap[0] : cap[0];
//           } else {
//             text = cap[0];
//           }
//           return {
//             type: 'text',
//             raw: cap[0],
//             text: text
//           };
//        }
//   }
// }})

// function inlineText(src, inRawBlock, smartypants) {
//   const cap = src.match(/^([`$]+|[^`$])(?:[\s\S]*?(?:(?=[\\<!\[`$*]|\b_|$)|[^ ](?= {2,}\n))|(?= {2,}\n))/);
//     if (cap) {
//       var text;
//       if (inRawBlock) {
//         text = this.options.sanitize ? this.options.sanitizer ? this.options.sanitizer(cap[0]) : cap[0] : cap[0];
//       } else {
//         text = (this.options.smartypants ? smartypants(cap[0]) : cap[0]);
//       }
//       return {
//         type: 'text',
//         raw: cap[0],
//         text: text
//       };
//    }
//See here: https://marked.js.org/using_pro#tokenizer
// const tokenizer = {
//   codespan(src : string) {
//     const match = src.match(/^\$+([^\$\n]+?)\$+/);
//     if (match) {
//       return {
//         type: 'codespan',
//         raw: match[0],
//         text: match[1].trim()
//       };
//     }

//     // return false to use original codespan tokenizer
//     return false;
//   }
// };

// marked.use({ tokenizer });

// Run marked
// console.log(marked.parse('$ latex code $\n\n` other code `'));


const example_scope_parsed = [
  {
    "type": "h1",
    "content": {"type": "string", "data": "Introduction to Naive Bayes Classifier"}
  },
  {
    "type": "p", //tag for text
    "content": {"type": "string", "data": "The Naive Bayes classifier is a simple probabilistic classifier that is based on Bayes&#39; theorem. It is called &quot;naive&quot; because it assumes that the features are independent of each other, which is often not true in real-world datasets. Despite its simplicity, the Naive Bayes classifier has been shown to perform well in many applications, including text classification, image classification, and bioinformatics. In this set of notes, we will cover the basics of the Naive Bayes classifier, including how it works, how to train it, and how to use it for classification."},
  },
  {
    "type": "h2",
    "text": {"type": "string", "data": "How does Naive Bayes work?"}
  },
  {
    "type": "p", //tag for text
    "text": [
      {"type": "string", "data": "blah blah blah"},
      {"type": "latex_equation", "data": "P(y|x) = \\frac{P(x|y) \\cdot P(y)}{P(x)}"},
      {"type": "string", "data": "blah blah blah"},
    ]
  },
]

function scopeParser(string_in: string) {

}


type ChatBubbleProps = {
  input: string,
  transparentDisplay?: boolean,
};

type MarkdownMapComponentProps = {
  token: Token,
  key?: number,
  padLeft?: boolean,
}

type MarkdownMapComponentErrorProps = {
  type: string
}

function MarkdownMapComponentError(props : MarkdownMapComponentErrorProps) {
  return (
    <View style={{
      backgroundColor: "#FF0000",
      borderRadius: "10",
      alignItems: 'center'
    }}>
      <Text selectable={true} style={{
        fontSize: 18,
        color: "#FF0000",
        padding: 10,
        textAlign: 'center',
        textAlignVertical: 'center',
      }}>
        {"Unfilled Markdown Component: "+props.type}
      </Text>
    </View>
  );
}

type MarkdownParagraphComponentProps = {
  token: Token,
};

function MarkdownParagraphComponent(props : MarkdownParagraphComponentProps) {
  const normalTextFont = "YingHei3";
  switch (props.token.type) {
    case 'text': //Normal Case
      return (
        <MarkdownTextSplitter selectable={true} style={{
          fontFamily: normalTextFont,
          fontSize: 16,
          color: '#E8E3E3'
          }} text={props.token.text}/>
      );
    case 'strong': //Bold case
      return (
        <Text style={{
          fontFamily: 'YingHei4',
          fontSize: 16,
          color: '#E8E3E3'
        }}>
          {props.token.text}
        </Text>
      );
    case 'em': //Bold case
      return (
        <Text style={{
          fontFamily: normalTextFont,
          fontSize: 16,
          color: '#E8E3E3',
          fontStyle: 'italic'
        }}>
          {props.token.text}
        </Text>
      );
    case 'codespan': //Bold case
      return (
        <Text style={{
          fontFamily: 'Consolas',
          fontSize: 16,
          color: '#E8E3E3',
          fontStyle: 'italic',
          // backgroundColor: '#17181D',
          borderRadius: 3,
          paddingHorizontal: 2,
        }}>
          {props.token.raw}
        </Text>
      );
  }
}

function MarkdownMapComponent(props : MarkdownMapComponentProps) {
  const normalTextFont = "Inter-Regular";
  const headingFont = "Inter-Bold";
  const defaultFontSize = 14;
  const codeFont = "Consolas";
  const headerFontSizes = {
    1: 36,
    2: 32,
    3: 28,
    4: 24,
    5: 20,
    6: 16,
  }
  
  
  const { token } = props;
    
  switch (token.type) {
    case 'space':
      return (
        <View style={{
          height: 5
        }}>

        </View>
      );
    case 'code':
      return (
        <MarkdownCodeBlock text={token.text} lang={token.lang}/>
      );
    case 'heading':
      let fontSizeGet = 30 - 3*token.depth;
      // if (token.hasOwnProperty("tokens")) {
      //   return (
      //     <Text>
      //     {token["tokens"].map((k: Number, v: Token) => (
      //       <Text style={{
      //         fontFamily: normalTextFont,
      //         fontSize: fontSizeGet,
      //         paddingLeft: 3*token.depth,
      //         color: '#E8E3E3'
      //       }}>
      //         {v.text}
      //       </Text>
          
      //     ))}
      //     </Text>
      //   );
      // }
      return (
        // <Text selectable={true} style={{
        //   fontFamily: "YingHei5",
        //   fontSize: fontSizeGet,
        //   color: '#E8E3E3'
        // }}>
        //   {token.text}
        // </Text>
        <MarkdownTextSplitter selectable={true} style={{
          paddingTop: 8,
          fontFamily: headingFont,
          fontSize: fontSizeGet,
          color: '#E8E3E3'
        }} text={token.text}/>
      );
    case 'table':
      return (null);
    case 'hr':
      return (null);
    case 'blockquote':
      return (null);
    case 'list':
      return (
        <View style={{
          paddingLeft: 3
        }}>
          {token.items.map((v : Tokens.ListItem, k : number) => (
            <MarkdownMapComponent key={k} token={v}/>
          ))}
        </View>
      );
    case 'list_item':
      return (
        <View style={{
          flexDirection: 'row'
        }}>
          <View style={{
            flexDirection: 'column'
          }}>
            <Text selectable={true} style={{
              fontFamily: normalTextFont, 
              fontSize: 16,
              width: 20,
              textAlign: 'center',
              color: '#E8E3E3'
              }}>·</Text>
          </View>
          <MarkdownTextSplitter selectable={true} style={{
            fontFamily: normalTextFont,
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text}/>
        </View>
      );
    case 'paragraph':
      return (
        <View style={{
          flexDirection: 'row',
          paddingLeft: (props.padLeft)?10:0,
          paddingBottom: 5,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            fontFamily: normalTextFont,
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text}/>
        </View>
      );
    case 'html':
      return (null);
    case 'text':
      return (null);
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }

}

export default function MarkdownRenderer(props: ChatBubbleProps) {
  const normalTextFont = "Inter-Regular";
  const codeFont = "Consolas";
  const [markdownTokens, setMarkdownTokens] = useState<TokensList>([]);
  
  const { input } = props;
  const transparentDisplay = (props.transparentDisplay)?props.transparentDisplay:false;
  let oldTextLength = 0;
  let textIndexActiveMarkdownSegment = 0;
  let markdownSegmentAddresses = [];
  let textUpdating = false;
  let old_string_hash = 0;
  const lexer = new marked.Lexer();


  // useEffect(() => {

  // }, [input]);

  useEffect(() => {
    // if (input.length === oldTextLength) {
    //   return;
    // }
    
    // let lexed_input = lexer.lex(input);
    // // console.log(lexed_input);
    // setMarkdownTokens(lexed_input);
    let new_string_hash = stringHash(input);
    if (new_string_hash === old_string_hash) {
      textUpdating = false;
      return;
    }
    if (markdownTokens.length === 0) {
      let lexed_input = lexer.lex(input);
      console.log(lexed_input)
      setMarkdownTokens(lexed_input);
      old_string_hash = stringHash(input);
    } else {
      textUpdating = true;
      let lexed_input = markdownTokens;
      if (lexed_input[lexed_input.length-1].text) {
        lexed_input[lexed_input.length-1].text += input.slice(oldTextLength, input.length);
      } else {
        lexed_input[lexed_input.length-1].raw += input.slice(oldTextLength, input.length);
      }
      setMarkdownTokens(lexed_input);
    }
  }, [input]);

  setInterval(() => {
    if (textUpdating) {
      // let new_string_hash = stringHash(input);
      let lexed_input = lexer.lex(input);
      console.log("LEXING");
      setMarkdownTokens(lexed_input);
      textUpdating = false;
      oldTextLength = input.length;
    }
  }, 250);


  // const getMarkdownText = (input_text : string) => {
  //   var rawMarkup = marked.parse(input_text);
  //   // console.log(rawMarkup);
  //   return { __html: rawMarkup };
  // }

  return (
    <View style={{
      maxWidth: "100%",
      minWidth: 40,
      minHeight: 40,
      // width: "80svw",
      paddingRight: 50
    }}>
      <View style={{
        flexDirection: "column",
        paddingHorizontal: 14,
        paddingVertical: transparentDisplay?0:6,
        backgroundColor: transparentDisplay?"none":"#39393C",
        // backgroundColor: "#1E1E1E",
        borderRadius: 10,
        alignSelf: "center",
        justifyContent: transparentDisplay?"center":"flex-start",
        width: "100%",
        minHeight: 40,
      }}>
        {markdownTokens.map((v : Token, k : number) => (
          <MarkdownMapComponent key={k} token={v}/>
        ))}
      </View>
    </View>
  );
}

const markdownStyles = StyleSheet.create({
  h1: {
    
  }
});
