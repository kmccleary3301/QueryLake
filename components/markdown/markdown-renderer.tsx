"use client";
import { useState, useEffect, useRef, memo, useCallback } from "react";
import { marked, TokensList, Token, Tokens } from 'marked';
import MarkdownTextSplitter from "./markdown-text-splitter";
import MarkdownCodeBlock from "./markdown-code-block";
import stringHash from "@/hooks/stringHash";
import MarkdownTable from "./markdown-table";
import sanitizeMarkdown from "@/components/markdown/sanitizeMarkdown";
import "./prose.css"
import { cn } from "@/lib/utils";
import { markdownRenderingConfig } from "./configs";

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

function MarkdownMapComponent({
  className = "",
  token,
  unProcessedText,
  finished,
  config,
}:{
  className?: string,
  token: Token,
  unProcessedText: string,
  finished: boolean,
  config: markdownRenderingConfig,
}) {
  const defaultFontSize = 'text-base';

  switch (token.type) {
    case 'space':
      return (
        // <br className={cn("not-prose", className)}/>
        <></>
      );
    case 'code':
      return (
        <MarkdownCodeBlock
          className={className}
          finished={finished} 
          text={token.text} 
          lang={token.lang} 
          unProcessedText={unProcessedText}
        />
      );
    case 'heading':
      if (token.raw[0] != "#") {
        return (
          <p className={className}>
            <MarkdownTextSplitter selectable={true} className={`text-left ${defaultFontSize}`} text={token.text + unProcessedText} config={config}/>
          </p>
        );
      } else {
        switch (token.depth) {
          case 1:
            return (
              <h2 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
                {/* {token.text + props.unProcessedText} */}
              </h2>
            );
          case 2:
            return (
              <h3 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
                {/* {token.text + props.unProcessedText} */}
              </h3>
            );
          case 3:
            return (
              <h4 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
              </h4>
            );
          case 4:
            return (
              <h5 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
              </h5>
            );
          case 5:
            return (
              <h6 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
              </h6>
            );
          case 6:
            return (
              <h6 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText} config={config}/>
              </h6>
            );
        }
      }

    case 'table':
      if (token.type === "table") { // Literally just here to get rid of the type error.
        return (
          <MarkdownTable
            className={className}
            header={token.header} 
            rows={token.rows}
            unProcessedText={unProcessedText}
            config={config}
          />
        );
      }
    case 'hr':
      return (null);
    case 'blockquote':
      // console.log("Blockquote text:", token);
      return (
        <blockquote className={cn(className, "pl-6 flex flex-col space-y-2")}>
          {/* <MarkdownTextSplitter 
            selectable={true} 
            className={`text-left ${defaultFontSize}`} 
            text={token.text + unProcessedText}
            config={config}
          /> */}
          {(token.tokens)?(
            <>
              {token.tokens.map((v : Token, k : number) => (
                <MarkdownMapComponent
                  className={v.type === "list" ? "ml-[2rem]" : ""}
                  finished={finished}
                  key={k}
                  unProcessedText={""}
                  token={v}
                  config={config}
                />
              ))}
            </>
          ):(
            <MarkdownTextSplitter 
              selectable={true} 
              className={`text-left ${defaultFontSize}`} 
              text={token.text + unProcessedText}
              config={config}
            />
          )}
        </blockquote>
      );
    case 'list':
      if (token.ordered) {
        return (
          <ol className={cn("not-prose", className)}>
            {token.items.map((v : Tokens.ListItem, k : number) => (
              <MarkdownMapComponent
                finished={finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?unProcessedText:""}
                token={{...v, type: "list_item"}}
                config={config}
              />
            ))}
          </ol>
        );
      } else {
        return (
          <ul className={cn("not-prose", className)}>
            {token.items.map((v : Tokens.ListItem, k : number) => (
              <MarkdownMapComponent
                finished={finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?unProcessedText:""}
                token={{...v, type: "list_item"}}
                config={config}
              />
            ))}
          </ul>
        );
      }
    case 'list_item':
      const counter = (token.raw.match(/^([^\s]+) /) || [""])[0].trimStart().trimEnd();

      return (
        <li className={cn(className, "relative")} counter-text={counter + " "}>
          <MarkdownRenderer 
            unpacked
            input={token.text + unProcessedText} 
            finished={finished} 
            disableRender={false}
            config={config}
          />
        </li>
      );
    case 'paragraph':
      const lines = (token.text + unProcessedText).split("\n") || "";
      return (
        <span className={className}>
          {(lines.length > 1)?(
            <>
              {lines.map((line, i) => (
                <span className="pb-1" key={i}>
                  <MarkdownTextSplitter 
                    selectable={true} 
                    className={`text-left text-base text-gray-200`} 
                    text={line}
                    config={config}
                  />
                </span>
              ))}
            </>
          ):(
          
            <MarkdownTextSplitter 
              selectable={true} 
              className={`text-left text-base text-gray-200`} 
              text={lines[0]}
              config={config}
            />
          )}
        </span>
      );
    case 'html':
      return (null);
    case 'text':
      return (
        <span className={className}>
          <MarkdownTextSplitter 
            selectable={true} 
            className={`text-left text-base text-gray-200`} 
            text={token.text + unProcessedText}
            config={config}
          />
        </span>
      );
    default:
      return (
        <MarkdownMapComponentError type={token.type}/>
      );
  }
}

const MarkdownRenderer = memo(function MarkdownRenderer({
  className = "",
  unpacked = false,
  input,
  transparentDisplay,
  disableRender = false,
  finished,
  config,
  list_in_block = false,
} : {
  className?: string,
  unpacked?: boolean,
  input: string,
  transparentDisplay?: boolean,
  disableRender?: boolean,
  finished: boolean,
  config: markdownRenderingConfig,
  list_in_block?: boolean
}) {
  const lexer = new marked.Lexer();
  // const lexed_input : Token[] = lexer.lex(sanitizeMarkdown(input));

  const [tokens, setTokens] = useState<Token[]>([]);

  const [unrenderedText, setUnrenderedText] = useState<string>("");
  const unusedRecentText = useRef<string>("");

  const last_render_time = useRef<number>(0);
  const rerender_timeout = useRef<NodeJS.Timeout>();
  const RENDER_INTERVAL = 25;

  // useEffect(() => {
  //   setTokens(lexer.lex(sanitizeMarkdown(input)))
  // })

  const bufferedText = useRef<string>("");

  useEffect(() => {
    // setTokens(lexer.lex(sanitizeMarkdown(input)));
    const time_until_next_render = 
        Math.max(0, RENDER_INTERVAL - (Date.now() - last_render_time.current));
    
    if (rerender_timeout.current) {
      clearTimeout(rerender_timeout.current);
    }

    const getTimeout = setTimeout(() => {
      // console.log("Delta text: ", new_buffer_text);
      // Update the last render time.
      last_render_time.current = Date.now(); 
      
      // Lex our tokens.
      const new_tokens = lexer.lex(sanitizeMarkdown(input));
      
      // Update the tokens.
      setTokens(new_tokens);
      
      // bufferedText.current = input;

      // setUnrenderedText("");
    }, time_until_next_render);

    rerender_timeout.current = getTimeout;

    // if (
    //   bufferedText.current !== input.slice(0, bufferedText.current.length) ||
    //   bufferedText.current.length === 0 && input.length > 0
    // ) {
    //   // Prefix mismatch, reset the tokens.
    //   // console.log("Prefix mismatch, resetting tokens.");
    //   bufferedText.current = input;
    //   // setTokens(lexer.lex(sanitizeMarkdown(input)));
    // } else if (tokens.length > 0) {
    //   // Let's parse only the recent text.
      
    //   const new_buffer_text = input.slice(bufferedText.current.length);
    //   // setUnrenderedText(new_buffer_text);


    //   const recent_token_text = tokens[tokens.length - 1].raw;
    //   const text_to_lex = recent_token_text + new_buffer_text;
      

    //   // TODO: account for trailing whitespaces and possibly other strings not used.

    //   const time_until_next_render = 
    //     Math.max(0, RENDER_INTERVAL - (Date.now() - last_render_time.current));

    //   if (rerender_timeout.current) {
    //     clearTimeout(rerender_timeout.current);
    //   }

    //   const getTimeout = setTimeout(() => {
    //     // console.log("Delta text: ", new_buffer_text);
    //     // Update the last render time.
    //     last_render_time.current = Date.now(); 
        
    //     // Lex our tokens.
    //     const new_tokens = lexer.lex(sanitizeMarkdown(text_to_lex));
        
    //     const end_whitespace_match = text_to_lex.match(/\s+$/);
    //     const end_whitespace = (end_whitespace_match)?end_whitespace_match[0]:"";
    //     if (new_tokens[new_tokens.length - 1]?.raw.match(/\s+$/)) {
    //       Error("Last token raw ends in a whitespace.");
    //     }
    //     unusedRecentText.current = end_whitespace;

    //     // Update the tokens.
    //     setTokens([...tokens.slice(
    //       // Remove the last token
    //       0, tokens.length - 1
    //     ), ...new_tokens]);
        
    //     bufferedText.current = input;

    //     // setUnrenderedText("");
    //   }, time_until_next_render);

    //   rerender_timeout.current = getTimeout;
    // } else {
    //   const new_tokens = lexer.lex(sanitizeMarkdown(input));
    //   const end_whitespace_match = input.match(/\s+$/);
    //   const end_whitespace = (end_whitespace_match)?end_whitespace_match[0]:"";
    //   if (new_tokens[new_tokens.length - 1]?.raw.match(/\s+$/)) {
    //     Error("Last token raw ends in a whitespace.");
    //   }
    //   unusedRecentText.current = end_whitespace;

    //   setTokens(new_tokens);

    //   bufferedText.current = input;
    // }

  }, [input]);

  return (
    <>
      {(disableRender)?(
        <>
          {input.split('\n').map((line, i) => (
            <p className="prose" key={i}>
              {line}
            </p>
          ))}
        </>
      ):(
        <>
        {unpacked?(
          <>
            {(
              // (unrenderedText.length > 0)?
              // [...tokens.slice(0, tokens.length-1), {
              //   ...tokens[tokens.length-1],
              //   raw: tokens[tokens.length-1].raw + unrenderedText,
              // }] :
              // tokens
              tokens
            ).map((v : Token, k : number) => (
              <MarkdownMapComponent
                className={
                  (tokens[0].type === "list" && v.type === "list")?
                    (tokens[0].ordered) ?
                      "ml-[1.25rem]" : 
                      "ml-[1.25rem]" :
                    (list_in_block) ?
                      "ml-[1.25rem]" :
                      ""
                }
                key={k} 
                finished={finished}
                token={v} 
                unProcessedText={""}
                config={config}
              />
            ))}
          </>
        ):(
          <div className={cn("prose markdown text-sm text-theme-primary space-y-3 flex flex-col", className)}>
            <MarkdownRenderer 
              className={className}
              unpacked={true}
              input={input} 
              transparentDisplay={transparentDisplay}
              disableRender={disableRender}
              finished={finished}
              config={config}
            />
          </div>
        )}
        </>
      )}
    </>
  );
});

export default MarkdownRenderer;
