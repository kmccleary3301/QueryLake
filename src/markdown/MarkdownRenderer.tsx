import { useState, useRef, useEffect } from "react";
import {
  Text,
  View,
  Platform,
  StyleSheet
} from "react-native";
// import { Marked } from "marked";
import { marked, TokensList, Token, Tokens } from 'marked';


const lexer = new marked.Lexer();
//See here: https://marked.js.org/using_pro#tokenizer
const tokenizer = {
  codespan(src : string) {
    const match = src.match(/^\$+([^\$\n]+?)\$+/);
    if (match) {
      return {
        type: 'codespan',
        raw: match[0],
        text: match[1].trim()
      };
    }

    // return false to use original codespan tokenizer
    return false;
  }
};

marked.use({ tokenizer });

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
      <Text style={{
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
      let fontSizeGet = (token.depth === 1)?36:32 - 4*token.depth;
      return (
        <Text style={{
          fontFamily: normalTextFont,
          fontSize: fontSizeGet,
          paddingLeft: 2*token.depth,
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
          paddingLeft: 10
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
            <Text style={{
              fontFamily: normalTextFont, 
              fontSize: 11,
              width: 20,
              textAlign: 'center'
              }}>·</Text>
          </View>
          <Text style={{
            fontFamily: normalTextFont,
            fontSize: 11
            }}>{token.text}</Text>
        </View>
      );
    case 'paragraph':
      return (
        <View style={{
          flexDirection: 'row',
          paddingLeft: 10
        }}>
          <Text style={{
            fontFamily: normalTextFont,
            fontSize: 11
            }}>{token.text}</Text>
        </View>
      );
    case 'html':
      return (null);
    case 'text':
      return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
    // case 'space':
    //   return (null);
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
  useEffect(() => {

    let lexed_input = lexer.lex(input);
    console.log(lexed_input);
    setMarkdownTokens(lexed_input);
  }, []);
  // console.log([marked.parse(input)]);
  // console.log("Lexer");

  const getMarkdownText = (input_text : string) => {
    var rawMarkup = marked.parse(input_text);
    console.log(rawMarkup);
    return { __html: rawMarkup };
  }

  return (
    <View style={{
      flexDirection: "column",
      padding: 10,
      backgroundColor: "#FFFFFF",
      borderRadius: 20,
      alignSelf: "center",
      alignItems: '',
      justifyContent: 'flex-start',

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
  );
}

const markdownStyles = StyleSheet.create({
  h1: {
    
  }
});
