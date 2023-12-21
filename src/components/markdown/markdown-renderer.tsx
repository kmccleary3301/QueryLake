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

function MarkdownMapComponent(props : MarkdownMapComponentProps) {
  const defaultFontSize = 16;
  
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
          <p style={{
						display: "flex",
            flexDirection: 'row',
            justifyContent: "left",
            textAlign: "left",
            paddingLeft: (props.padLeft)?10:0,
            paddingTop: (props.disableHeadingPaddingTop)?0:(30 - 3*token.depth)*0.75,
            paddingBottom: (props.disableHeadingPaddingTop)?0:10
          }}>
            <MarkdownTextSplitter selectable={true} style={{
              // fontFamily: normalTextFont,
							textAlign: "left",
              fontSize: defaultFontSize,
              color: '#E8E3E3'
              }} text={token.text + props.unProcessedText}/>
          </p>
        );
      }

      return (
        <span style={{
          paddingTop: (props.disableHeadingPaddingTop)?0:30,
          textAlign: "left",
          paddingLeft: 3*(token.depth-1),
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            paddingTop: 8,
            // fontFamily: headingFont,
            fontSize: 30 - 3*token.depth,
            color: '#E8E3E3'
          }} text={token.text + props.unProcessedText}/>
        </span>
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
        <div id="markdown-map-component-list" style={{
          display: "flex",
          flexDirection: 'column',
          flexGrow: 1,
          alignItems: "flex-start",
          // textAlign: "left",
          paddingLeft: 3,
        }}>
          {token.items.map((v : Tokens.ListItem, k : number) => (
            <span key={k} id="markdown-map-component-list-item" style={{
              textAlign: "left", 
              display: "flex", 
              flex: 1,
              width: "100%",
              // flexDirection: "row", 
              paddingTop: 15,
              flexGrow: 1,
            }}>
              {(token.ordered)?(
                <span style={{
                  textAlign: "left",
                  userSelect: "none",
                  paddingLeft: 3,
                  paddingTop: 4,
                  color: "#E8E3E3",
                  opacity: 0.5,
                  width: 20,
                }}>
                  {k+1+". "}
                </span>
              ):(
                <span style={{
                  textAlign: "left",
                  userSelect: "none",
                  paddingLeft: 3,
                  paddingTop: 12,
                  width: 20,
                  opacity: 0.5
                }}>
                  <div style={{
                    borderRadius: 3,
                    width: 6,
                    height: 6,
                    // paddingTop: 8,
                    // paddingHorizontal: 5,
                    backgroundColor: '#E8E3E3'
                  }}/>
                </span>
              )}
              <MarkdownMapComponent
                finished={props.finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?props.unProcessedText:""}
                token={{...v, type: "list_item"}}
              />
            </span>
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
        <span style={{
					// display: "flex",
          // flexDirection: 'row',
          textAlign: "left",
          paddingLeft: (props.padLeft)?10:0,
          paddingBottom: 5,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            // fontFamily: normalTextFont,
						textAlign: "left",
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
        </span>
      );
    case 'html':
      return (null);
    case 'text':
      return (
        <span style={{
					// display: "flex",
          // flexDirection: 'row',
          textAlign: "left",
          paddingLeft: (props.padLeft)?10:0,
          paddingBottom: 5,
        }}>
          <MarkdownTextSplitter selectable={true} style={{
            // fontFamily: normalTextFont,
						textAlign: "left",
            fontSize: defaultFontSize,
            color: '#E8E3E3'
            }} text={token.text + props.unProcessedText}/>
        </span>
      );
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }

}

export default function MarkdownRenderer(props: MarkdownRendererProps) {
  const disableRender = (props.disableRender)?props.disableRender:false;
  const [unprocessedText, setUnprocessedText] = useState("");
	const lastUpdateTime = useRef(Date.now());
  const [markdownTokens, setMarkdownTokens] = useState<TokensList | Token[]>([]);
	const oldInputLength = useRef(0);

	const markdownTokenLength = useRef(0);
  
  const { input } = props;
  
  const [old_string_hash, set_old_string_hash] = useState(0);


	


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
      console.log("LEXED INPUT:", lexed_input);
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
					textAlign: "left",
					fontSize: 16,
          color: "#E8E3E3",
          // maxWidth: 400,
					textWrap: "wrap",
          display: "flex",
          width: "100%"
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
  );
}
