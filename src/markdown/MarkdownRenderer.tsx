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
import MarkdownTable from "./MarkdownTable";
import sanitizeMarkdown from "../hooks/sanitizeMarkdown";

type MarkdownRendererProps = {
  input: string,
  maxWidth: number,
  transparentDisplay?: boolean,
};

type MarkdownMapComponentProps = {
  token: Token,
  maxWidth: number,
  bubbleWidth: number,
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
      if (token.raw[0] != "#") {
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
      }

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
      return (<MarkdownTable bubbleWidth={props.bubbleWidth} maxWidth={props.maxWidth} header={token.header} rows={token.rows}/>);
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
            <MarkdownMapComponent bubbleWidth={props.bubbleWidth} maxWidth={props.maxWidth} key={k} token={v}/>
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
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }

}

export default function MarkdownRenderer(props: MarkdownRendererProps) {
  const normalTextFont = "Inter-Regular";
  const codeFont = "Consolas";
  const [markdownTokens, setMarkdownTokens] = useState<TokensList>([]);
  // const [maxWidth, setMaxWidth] = useState(40);
  const [bubbleWidth, setBubbleWidth] = useState(10);
  
  const { input } = props;
  const transparentDisplay = (props.transparentDisplay)?props.transparentDisplay:false;
  let oldTextLength = 0;
  let textIndexActiveMarkdownSegment = 0;
  let markdownSegmentAddresses = [];
  let textUpdating = false;
  let old_string_hash = 0;
  const lexer = new marked.Lexer();


  useEffect(() => {
    console.log("Bubble width:", bubbleWidth);
    console.log("MaxWidth:", props.maxWidth);
  }, [bubbleWidth, props.maxWidth]);

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
      let lexed_input = lexer.lex(sanitizeMarkdown(input));
      // console.log("LEXING");
      // console.log(input);
      // console.log(sanitizeMarkdown(input));
      // console.log(lexed_input)
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
      let lexed_input = lexer.lex(sanitizeMarkdown(input));
      // console.log("LEXING");
      // console.log(input);
      // console.log(lexed_input);
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
    <View
    >
      <View style={{
        maxWidth: "60vw",
        minWidth: 40,
        minHeight: 40,
        // width: "80svw",
        paddingRight: 50
      }}>
        <View 
          style={{
            flexDirection: "column",
            paddingHorizontal: 14,
            paddingVertical: transparentDisplay?0:6,
            backgroundColor: transparentDisplay?"none":"#39393C",
            // backgroundColor: "#1E1E1E",
            borderRadius: 10,
            alignSelf: "center",
            justifyContent: transparentDisplay?"center":"flex-start",
            maxWidth: "100%",
            minHeight: 40,
          }}
          onLayout={(event) => {
            setBubbleWidth(event.nativeEvent.layout.width);
          }}
        >
          {markdownTokens.map((v : Token, k : number) => (
            <MarkdownMapComponent bubbleWidth={bubbleWidth} maxWidth={props.maxWidth} key={k} token={v}/>
          ))}
        </View>
      </View>
    </View>
  );
}

const markdownStyles = StyleSheet.create({
  h1: {
    
  }
});
