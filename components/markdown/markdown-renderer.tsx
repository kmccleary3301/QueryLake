"use client";
import { useState, useEffect, useRef, memo, useCallback } from "react";
import { marked, TokensList, Token, Tokens } from 'marked';
import MarkdownTextSplitter from "./markdown-text-splitter";
import MarkdownCodeBlock from "./markdown-code-block";
import stringHash from "@/hooks/stringHash";
import MarkdownTable from "./markdown-table";
import sanitizeMarkdown from "@/hooks/sanitizeMarkdown";
import "./prose.css"

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
    <div className="bg-red-600 rounded-lg items-center">
      <p className="text-lg text-red-600 p-2 text-center">
        {"Unfilled Markdown Component: "+props.type}
      </p>
    </div>
  );
}

function MarkdownMapComponent(props : MarkdownMapComponentProps) {
  const defaultFontSize = 'text-base';
  
  const { token } = props;

  switch (token.type) {
    case 'space':
      return (
        <br className="w-[2px] h-[3px] bg-red-500"/>
      );
    case 'code':
      return (
        <MarkdownCodeBlock finished={props.finished} text={token.text} lang={token.lang} unProcessedText={props.unProcessedText}/>
      );
    case 'heading':
      if (token.raw[0] != "#") {
        return (
          <p>
            <MarkdownTextSplitter selectable={true} className={`text-left ${defaultFontSize}`} text={token.text + props.unProcessedText}/>
          </p>
        );
      } else {
        switch (token.depth) {
          case 1:
            return (
              <h2>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h2>
            );
          case 2:
            return (
              <h3>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h3>
            );
          case 3:
            return (
              <h4>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h4>
            );
          case 4:
            return (
              <h5>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h5>
            );
          case 5:
            return (
              <h6>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h6>
            );
          case 6:
            return (
              <h6>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h6>
            );
        }
      }

    case 'table':
      if (token.type === "table") { // Literally just here to get rid of the type error.
        return (
          <MarkdownTable
          header={token.header} 
          rows={token.rows}
          unProcessedText={props.unProcessedText}
          />
          );
      }
    case 'hr':
      return (null);
    case 'blockquote':
      return (
        <blockquote>
          <MarkdownTextSplitter selectable={true} className={`text-left ${defaultFontSize}`} text={token.text + props.unProcessedText}/>
        </blockquote>
      );
    case 'list':

      if (token.ordered) {
        return (
          <ol className="">
            {token.items.map((v : Tokens.ListItem, k : number) => (
              <MarkdownMapComponent
                finished={props.finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?props.unProcessedText:""}
                token={{...v, type: "list_item"}}
              />
            ))}
          </ol>
        );
      } else {
        return (
          <ul className="">
            {token.items.map((v : Tokens.ListItem, k : number) => (
              <MarkdownMapComponent
                finished={props.finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?props.unProcessedText:""}
                token={{...v, type: "list_item"}}
              />
            ))}
          </ul>
        );
      }
    case 'list_item':
      return (
        <li className="">
          {/* <MarkdownTextSplitter selectable={true} className={`text-left text-base text-gray-200`} text={token.text + props.unProcessedText}/> */}
          <MarkdownRenderer 
            input={token.text + props.unProcessedText} 
            finished={props.finished} 
            disableRender={false}
          />
        </li>
      );
    case 'paragraph':
      return (
        <div>
          <MarkdownTextSplitter selectable={true} className={`text-left text-base text-gray-200`} text={token.text + props.unProcessedText}/>
        </div>
      );
    case 'html':
      return (null);
    case 'text':
      return (
        <span>
          <MarkdownTextSplitter selectable={true} className={`text-left text-base text-gray-200`} text={token.text + props.unProcessedText}/>
        </span>
      );
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }
}

const MarkdownRenderer = memo(function MarkdownRenderer({
  input,
  transparentDisplay,
  disableRender,
  finished,
} : {
  input: string,
  transparentDisplay?: boolean,
  disableRender?: boolean,
  finished: boolean,
}) {
  // const disableRender = (disableRender)?props.disableRender:false;
  const [unprocessedText, setUnprocessedText] = useState("");
	const lastUpdateTime = useRef(Date.now());
  const [markdownTokens, setMarkdownTokens] = useState<TokensList | Token[]>([]);
	const oldInputLength = useRef(0);
	const markdownTokenLength = useRef(0);
  const old_string_hash = useRef(0);
  const reRenderInterval = 250;
  const lexer = new marked.Lexer();

  const updateData = useCallback(() => {
    const new_string_hash = stringHash(input);
    if (new_string_hash === old_string_hash.current) {
      return;
    }
    if (markdownTokenLength.current === 0 || (Date.now() - lastUpdateTime.current > reRenderInterval)) {
      const lexed_input = lexer.lex(sanitizeMarkdown(input));
      // TODO: error occurs here: Error: Maximum update depth exceeded. This can happen when a component repeatedly calls setState inside componentWillUpdate or componentDidUpdate. React limits the number of nested updates to prevent infinite loops.
      setMarkdownTokens(lexed_input);
      // console.log("LEXED INPUT:", lexed_input);
      old_string_hash.current = stringHash(input);
      lastUpdateTime.current = Date.now();
      oldInputLength.current = input.length;
      setUnprocessedText("");
    } else {
      // textUpdating = true;
      setUnprocessedText(input.slice(oldInputLength.current));
    }
  }, [input])

  // useEffect(() => {
  //   updateData();
  // }, [input]);

  // useEffect(() => {
  //   const lexer = new marked.Lexer();
  //   const new_string_hash = stringHash(input);
  //   if (new_string_hash !== old_string_hash) {
  //     const lexed_input = lexer.lex(sanitizeMarkdown(input));
  //     setMarkdownTokens(lexed_input);
  //     set_old_string_hash(new_string_hash);
  //     oldInputLength.current = input.length;
  //     setUnprocessedText("");
  //   } else if (Date.now() - lastUpdateTime.current > reRenderInterval) {
  //     setUnprocessedText(input.slice(oldInputLength.current));
  //   }
  //   lastUpdateTime.current = Date.now();
  // }, [input, old_string_hash, reRenderInterval]);

  return (
    <>
      {(disableRender)?(
        <>
          {input.split('\n').map((line, i) => (
            <p key={i}>
              {line}
            </p>
          ))}
        </>
      ):(
        <div className="prose text-sm space-y-2 text-theme-primary whitespace-pre-wrap break-words">
          {lexer.lex(sanitizeMarkdown(input)).map((v : Token, k : number) => (
            <MarkdownMapComponent 
              key={k} 
              finished={finished || k < (markdownTokens.length - 1)}
              token={v} 
              unProcessedText={(k === markdownTokens.length - 1)?unprocessedText:""}
              disableHeadingPaddingTop={(k === 0)}
            />
          ))}
        </div>
      )}
    </>
  );
});

export default MarkdownRenderer;
