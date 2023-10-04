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
console.log(marked.parse('$ latex code $\n\n` other code `'));


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
};

type MarkdownMapComponentProps = {
  token: Token,
  key?: number,
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



function MarkdownMapComponent(props : MarkdownMapComponentProps) {
  const normalTextFont = "YingHei4";
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
      return (null);
    case 'heading':
      let fontSizeGet = 36 - 3*token.depth;
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
        <Text selectable={true} style={{
          fontFamily: normalTextFont,
          fontSize: fontSizeGet,
          color: '#E8E3E3'
        }}>
          {token.text}
        </Text>
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
              fontSize: 14,
              width: 20,
              textAlign: 'center',
              color: '#E8E3E3'
              }}>·</Text>
          </View>
          <MarkdownTextSplitter selectable={true} style={{
            fontFamily: normalTextFont,
            fontSize: 14,
            color: '#E8E3E3'
            }} text={token.text}/>
        </View>
      );
    case 'paragraph':
      return (
        <View style={{
          flexDirection: 'row',
          paddingLeft: 10
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            fontFamily: normalTextFont,
            fontSize: 14,
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
  const normalTextFont = "Inter";
  const codeFont = "Consolas";
  const [markdownTokens, setMarkdownTokens] = useState<TokensList>([]);
  
  const { input } = props;
  const lexer = new marked.Lexer();

  // useEffect(() => {

  // }, [input]);

  useEffect(() => {
    let lexed_input = lexer.lex(input);
    console.log(lexed_input);
    setMarkdownTokens(lexed_input);
  }, [input]);
  // console.log([marked.parse(input)]);
  // console.log("Lexer");

  const getMarkdownText = (input_text : string) => {
    var rawMarkup = marked.parse(input_text);
    console.log(rawMarkup);
    return { __html: rawMarkup };
  }

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
      padding: 10,
      backgroundColor: "#39393C",
      // backgroundColor: "#1E1E1E",
      borderRadius: 20,
      alignSelf: "center",
      justifyContent: 'flex-start',
      width: "100%",
    }}>
      {/* <Text style={{fontFamily: normalTextFont}}> */}
      {/* <div dangerouslySetInnerHTML={getMarkdownText(input)} />; */}

        {/* <Text style={{
          fontSize: 18,
          fontFamily: normalTextFont,
          color: '#000000',
          padding: 20
        }}>
        {input}
      </Text> */}
      {/* </Text> */}
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
