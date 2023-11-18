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
import globalStyleSettings from "../../globalStyleSettings";

// monkey patch for marked 0.3.3 to preserve non-breaking spaces
// marked.Lexer.prototype.lex = function(src) {
//   src = src
//     .replace(/\r\n|\r/g, '\n')
//     .replace(/\t/g, '    ')
//     .replace(/\u2424/g, '\n');

//   return this.token(src, true);
// };

type MarkdownRendererProps = {
  input: string,
  maxWidth: number,
  bubbleWidth: number,
  transparentDisplay?: boolean,
  disableRender?: boolean,
};

type MarkdownMapComponentProps = {
  token: Token,
  maxWidth: number,
  bubbleWidth: number,
  unProcessedText: string,
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
        <MarkdownCodeBlock text={token.text} lang={token.lang} unProcessedText={props.unProcessedText}/>
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
            paddingTop: 20,
          }}>
            <MarkdownTextSplitter selectable={true} style={{
              fontFamily: normalTextFont,
              fontSize: defaultFontSize,
              color: '#E8E3E3'
              }} text={token.text + props.unProcessedText}/>
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
        <View style={{
          paddingTop: 20,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            paddingTop: 8,
            fontFamily: headingFont,
            fontSize: fontSizeGet,
            color: '#E8E3E3'
          }} text={token.text + props.unProcessedText}/>
        </View>
      );
    case 'table':
      return (
        <MarkdownTable 
          bubbleWidth={props.bubbleWidth} 
          maxWidth={props.maxWidth} 
          header={token.header} 
          rows={token.rows}
          unProcessedText={props.unProcessedText}
        />
      );
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
            <MarkdownMapComponent 
              bubbleWidth={props.bubbleWidth} 
              maxWidth={props.maxWidth} 
              key={k} 
              token={v}
              unProcessedText={(k === token.items.length-1)?props.unProcessedText:""}
            />
          ))}
        </View>
      );
    case 'list_item':
      return (
        <View style={{
          flexDirection: 'row',
          alignItems: "flex-start",
          paddingVertical: 4
        }}>
          <View style={{
            flexDirection: 'column',
            paddingTop: 6,
            paddingHorizontal: 6
          }}>
            <View style={{
              borderRadius: 3,
              width: 6,
              height: 6,
              // paddingTop: 8,
              // paddingHorizontal: 5,
              backgroundColor: '#E8E3E3'
            }}/>
            {/* <Text selectable={true} style={{
              fontFamily: normalTextFont, 
              fontSize: 16,
              width: 20,
              textAlign: 'center',
              color: '#74748B'
              }}>·</Text> */}
          </View>
          <MarkdownTextSplitter selectable={true} style={{
            fontFamily: normalTextFont,
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
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
            }} text={token.text + props.unProcessedText}/>
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
            }} text={token.text + props.unProcessedText}/>
        </View>
      );
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }

}

export default function MarkdownRenderer(props: MarkdownRendererProps) {
  // const normalTextFont = "Inter-Regular";
  // const codeFont = "Consolas";
  const [markdownTokens, setMarkdownTokens] = useState<TokensList>([]);
  // const [maxWidth, setMaxWidth] = useState(40);
  const disableRender = (props.disableRender)?props.disableRender:false;
  // const [oldTextLength, setOldTextLength] = useState(0);
  const [unprocessedText, setUnprocessedText] = useState("");
  const [oldInputLength, setOldInputLength] = useState(0);
  const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());

  
  const { input } = props;
  
  // let oldTextLength = 0;
  // let textIndexActiveMarkdownSegment = 0;
  // let markdownSegmentAddresses = [];
  let textUpdating = true;
  let old_string_hash = 0;

  
  const lexer = new marked.Lexer();

  const reRenderInterval = 250;

  useEffect(() => {
    let new_string_hash = stringHash(input);
    if (new_string_hash === old_string_hash) {
      textUpdating = false;
      return;
    }
    if (markdownTokens.length === 0 || (textUpdating && (Date.now() - lastUpdateTime > reRenderInterval))) {
      let lexed_input = lexer.lex(sanitizeMarkdown(input));
      setMarkdownTokens(lexed_input);
      console.log("LEXED", lexed_input);
      let lastTokenContentGrab = "";
      if (lexed_input[lexed_input.length - 1].hasOwnProperty('text')) { lastTokenContentGrab = lexed_input[lexed_input.length - 1].text; }
      else { lastTokenContentGrab = lexed_input[lexed_input.length - 1].raw; }
      old_string_hash = stringHash(input);
      setLastUpdateTime(Date.now());
      setOldInputLength(input.length);
      setUnprocessedText("");
    } else {
      textUpdating = true;
      setUnprocessedText(input.slice(oldInputLength));
    }
  }, [input]);

  return (
    <>
      {(disableRender)?(
        <Text style={{
          fontFamily: globalStyleSettings.chatRegularFont,
          fontSize: globalStyleSettings.chatDefaultFontSize,
          color: globalStyleSettings.colorText,
          maxWidth: props.maxWidth
        }}>
          {props.input}
        </Text>
      ):(
        <>
          {markdownTokens.map((v : Token, k : number) => (
            <MarkdownMapComponent 
              key={k} 
              bubbleWidth={props.bubbleWidth} 
              maxWidth={props.maxWidth} 
              token={v} 
              unProcessedText={(k === markdownTokens.length - 1)?unprocessedText:""}
            />
          ))}
        </>
      )}
    </>
    //     </View>
    //   </View>
    // </View>
  );
}

// const markdownStyles = StyleSheet.create({
//   h1: {
    
//   }
// });
