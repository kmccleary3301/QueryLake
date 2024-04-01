"use client";
import { useState, useEffect, useRef } from "react";
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
              <h1>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h1>
            );
          case 2:
            return (
              <h2>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h2>
            );
          case 3:
            return (
              <h3>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h3>
            );
          case 4:
            return (
              <h4>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h4>
            );
          case 5:
            return (
              <h5>
                <MarkdownTextSplitter selectable={true} text={token.text + props.unProcessedText}/>
              </h5>
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
      // console.log("LEXED INPUT:", lexed_input);
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
        <p>
          {props.input}
        </p>
      ):(
        <div className="prose text-sm space-y-3 text-theme-primary">
          {markdownTokens.map((v : Token, k : number) => (
            <MarkdownMapComponent 
              key={k} 
              finished={props.finished || k < (markdownTokens.length - 1)}
              token={v} 
              unProcessedText={(k === markdownTokens.length - 1)?unprocessedText:""}
              disableHeadingPaddingTop={(k === 0)}
            />
          ))}
        </div>
      )}
    </>
  );
}