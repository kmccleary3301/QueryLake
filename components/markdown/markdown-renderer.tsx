"use client";
import { useState, useEffect, useRef, memo, useCallback } from "react";
import { marked, TokensList, Token, Tokens } from 'marked';
import MarkdownTextSplitter from "./markdown-text-splitter";
import MarkdownCodeBlock from "./markdown-code-block";
import stringHash from "@/hooks/stringHash";
import MarkdownTable from "./markdown-table";
import sanitizeMarkdown from "@/hooks/sanitizeMarkdown";
import "./prose.css"
import { cn } from "@/lib/utils";

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
  config = "obsidian",
}:{
  className?: string,
  token: Token,
  unProcessedText: string,
  finished: boolean,
  config?: "obsidian" | "chat",
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
      console.log("Blockquote text:", token);
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
      return (
        <li className={className}>
          {/* <MarkdownTextSplitter selectable={true} className={`text-left text-base text-gray-200`} text={token.text + props.unProcessedText}/> */}
          <MarkdownRenderer 
            unpacked={true}
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
                <p className="pb-1" key={i}>
                  <MarkdownTextSplitter 
                    selectable={true} 
                    className={`text-left text-base text-gray-200`} 
                    text={line}
                    config={config}
                  />
                </p>
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
  config = "obsidian",
  list_in_block = false,
} : {
  className?: string,
  unpacked?: boolean,
  input: string,
  transparentDisplay?: boolean,
  disableRender?: boolean,
  finished: boolean,
  config?: "obsidian" | "chat"
  list_in_block?: boolean
}) {
  const lexer = new marked.Lexer();
  const lexed_input = lexer.lex(sanitizeMarkdown(input));

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
            {lexed_input.map((v : Token, k : number) => (
              <MarkdownMapComponent
                className={
                  (lexed_input[0].type === "list" && v.type === "list")?
                    (lexed_input[0].ordered) ?
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
          <div className={cn("prose font-geist-sans markdown text-sm text-theme-primary space-y-3 flex flex-col", className)}>
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
