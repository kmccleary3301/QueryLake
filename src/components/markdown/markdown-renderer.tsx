import { useState, useEffect, useRef } from "react";
// import {
//   Text,
//   View,
//   Platform,
//   StyleSheet
// } from "react-native";
// import { Marked } from "marked";
import { marked, TokensList, Token, Tokens } from 'marked';
import MarkdownTextSplitter from "./markdown-text-splitter";
import MarkdownCodeBlock from "./markdown-code-block";
import markedKatex from "marked-katex-extension";
import stringHash from "@/hooks/stringHash";
import MarkdownTable from "./markdown-table";
import sanitizeMarkdown from "@/hooks/sanitizeMarkdown";

marked.use(
	markedKatex({
		throwOnError: false,
	})
);

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
  transparentDisplay?: boolean,
  disableRender?: boolean,
  finished: boolean,
};

type MarkdownMapComponentProps = {
  token: Token,
  unProcessedText: string,
  key?: number,
  padLeft?: boolean,
  disableHeadingPaddingTop?: boolean,
  finished: boolean,
}

type MarkdownMapComponentErrorProps = {
  type: string
}

function MarkdownMapComponentError(props : MarkdownMapComponentErrorProps) {
  return (
    <div style={{
      backgroundColor: "#FF0000",
      borderRadius: "10",
      alignItems: 'center'
    }}>
      <p style={{
        fontSize: 18,
        color: "#FF0000",
        padding: 10,
        textAlign: 'center',
        // textAlignVertical: 'center',
      }}>
        {"Unfilled Markdown Component: "+props.type}
      </p>
    </div>
  );
}

// function MarkdownParagraphComponent(props : MarkdownParagraphComponentProps) {
//   const normalTextFont = "YingHei3";
//   switch (props.token.type) {
//     case 'text': //Normal Case
//       return (
//         <MarkdownTextSplitter bubbleWidth={props.bubbleWidth} selectable={true} style={{
//           fontFamily: normalTextFont,
//           fontSize: 16,
//           color: '#E8E3E3'
//           }} text={props.token.text}/>
//       );
//     case 'strong': //Bold case
//       return (
//         <Text style={{
//           fontFamily: 'YingHei4',
//           fontSize: 16,
//           color: '#E8E3E3'
//         }}>
//           {props.token.text}
//         </Text>
//       );
//     case 'em': //Bold case
//       return (
//         <Text style={{
//           fontFamily: normalTextFont,
//           fontSize: 16,
//           color: '#E8E3E3',
//           fontStyle: 'italic'
//         }}>
//           {props.token.text}
//         </Text>
//       );
//     case 'codespan': //Bold case
//       return (
//         <Text style={{
//           fontFamily: 'Consolas',
//           fontSize: 16,
//           color: '#E8E3E3',
//           fontStyle: 'italic',
//           // backgroundColor: '#17181D',
//           borderRadius: 3,
//           paddingHorizontal: 2,
//         }}>
//           {props.token.raw}
//         </Text>
//       );
//   }
// }

function MarkdownMapComponent(props : MarkdownMapComponentProps) {
  // const normalTextFont = "Inter-Regular";
  // const headingFont = "Inter-Bold";
  const defaultFontSize = 14;
  // const codeFont = "Consolas";
  // const headerFontSizes = {
  //   1: 36,
  //   2: 32,
  //   3: 28,
  //   4: 24,
  //   5: 20,
  //   6: 16,
  // };
  
  
  const { token } = props;

  switch (token.type) {
    case 'space':
      return (
        <div style={{
          height: 5
        }}>

        </div>
      );
    case 'code':
      return (
        <MarkdownCodeBlock finished={props.finished} text={token.text} lang={token.lang} unProcessedText={props.unProcessedText}/>
      );
    case 'heading':
      
      
      if (token.raw[0] != "#") {
        return (
          <div style={{
						display: "flex",
            flexDirection: 'row',
            paddingLeft: (props.padLeft)?10:0,
            paddingTop: (props.disableHeadingPaddingTop)?0:30,
          }}>
            <MarkdownTextSplitter selectable={true} style={{
              // fontFamily: normalTextFont,
							textAlign: "left",
              fontSize: defaultFontSize,
              color: '#E8E3E3'
              }} text={token.text + props.unProcessedText}/>
          </div>
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
        <div style={{
          paddingTop: (props.disableHeadingPaddingTop)?0:30,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            paddingTop: 8,
            // fontFamily: headingFont,
            fontSize: 30 - 3*token.depth,
            color: '#E8E3E3'
          }} text={token.text + props.unProcessedText}/>
        </div>
      );
    case 'table':
      return (
        <MarkdownTable 
          // bubbleWidth={props.bubbleWidth} 
          // maxWidth={props.maxWidth} 
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
        <div style={{
          paddingLeft: 3
        }}>
          {token.items.map((v : Tokens.ListItem, k : number) => (
            <MarkdownMapComponent 
              finished={props.finished}
              key={k} 
              token={v}
              unProcessedText={(k === token.items.length-1)?props.unProcessedText:""}
            />
          ))}
        </div>
      );
    case 'list_item':
      return (
        <div style={{
					display: "flex",
          flexDirection: 'row',
          alignItems: "flex-start",
          paddingTop: 4,
					paddingBottom: 4,
        }}>
          <div style={{
						display: "flex",
            flexDirection: 'column',
            paddingTop: 10,
            paddingLeft: 6,
						paddingRight: 6,
          }}>
            <div style={{
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
          </div>
          <MarkdownTextSplitter selectable={true} style={{
            // fontFamily: normalTextFont,
						textAlign: "left",
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
        </div>
      );
    case 'paragraph':
      return (
        <div style={{
					display: "flex",
          flexDirection: 'row',
          paddingLeft: (props.padLeft)?10:0,
          paddingBottom: 5,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            // fontFamily: normalTextFont,
						textAlign: "left",
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
        </div>
      );
    case 'html':
      return (null);
    case 'text':
      return (
        <div style={{
					display: "flex",
          flexDirection: 'row',
          paddingLeft: (props.padLeft)?10:0,
          paddingBottom: 5,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            // fontFamily: normalTextFont,
						textAlign: "left",
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
        </div>
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
  // const [maxWidth, setMaxWidth] = useState(40);
  const disableRender = (props.disableRender)?props.disableRender:false;
  // const [oldTextLength, setOldTextLength] = useState(0);
  const [unprocessedText, setUnprocessedText] = useState("");
  // const [oldInputLength, setOldInputLength] = useState(0);
  // const [lastUpdateTime, setLastUpdateTime] = useState(Date.now());
	const lastUpdateTime = useRef(Date.now());
  const [markdownTokens, setMarkdownTokens] = useState<TokensList | Token[]>([]);
	const oldInputLength = useRef(0);

	const markdownTokenLength = useRef(0);
  
  const { input } = props;
  
  // let oldTextLength = 0;
  // let textIndexActiveMarkdownSegment = 0;
  // let markdownSegmentAddresses = [];
  // let textUpdating = true;
  const [old_string_hash, set_old_string_hash] = useState(0);

	// const options: marked.MarkedOptions = {
	// 	...defaults,
	// 	gfm: true,
	// 	breaks: true,
	// };

	


  const reRenderInterval = 250;

  useEffect(() => {
		
		const lexer = new marked.Lexer();
    const new_string_hash = stringHash(input);
    if (new_string_hash === old_string_hash) {
      return;
    }
    if (markdownTokenLength.current === 0 || (Date.now() - lastUpdateTime.current > reRenderInterval)) {
      const lexed_input = lexer.lex(sanitizeMarkdown(input));
      setMarkdownTokens(lexed_input);
      set_old_string_hash(stringHash(input));
      lastUpdateTime.current = Date.now();
      oldInputLength.current = input.length;
      setUnprocessedText("");
    } else {
      // textUpdating = true;
      setUnprocessedText(input.slice(oldInputLength.current));
    }
  }, [input, old_string_hash]);

  return (
    <>
      {(disableRender)?(
        <p style={{
          // fontFamily: globalStyleSettings.chatRegularFont,
          // fontSize: globalStyleSettings.chatDefaultFontSize,
					textAlign: "left",
					fontSize: 16,
          color: "#E8E3E3",
          maxWidth: 400,
					textWrap: "wrap",
        }}>
          {props.input}
        </p>
      ):(
        <>
          {markdownTokens.map((v : Token, k : number) => (
            <MarkdownMapComponent 
              key={k} 
              finished={props.finished || k < (markdownTokens.length - 1)}
              token={v} 
              unProcessedText={(k === markdownTokens.length - 1)?unprocessedText:""}
              disableHeadingPaddingTop={(k === 0)}
            />
          ))}
        </>
      )}
    </>
    //     </div>
    //   </div>
    // </div>
  );
}

// const markdownStyles = StyleSheet.create({
//   h1: {
    
//   }
// });
