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
}:{
  className?: string,
  token: Token,
  unProcessedText: string,
  finished: boolean,
}) {
  const defaultFontSize = 'text-base';

  switch (token.type) {
    case 'space':
      return (
        <br className={cn("w-[2px] h-[1px] bg-red-500", className)}/>
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
            <MarkdownTextSplitter selectable={true} className={`text-left ${defaultFontSize}`} text={token.text + unProcessedText}/>
          </p>
        );
      } else {
        switch (token.depth) {
          case 1:
            return (
              <h2 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h2>
            );
          case 2:
            return (
              <h3 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
                {/* {token.text + props.unProcessedText} */}
              </h3>
            );
          case 3:
            return (
              <h4 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
              </h4>
            );
          case 4:
            return (
              <h5 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
              </h5>
            );
          case 5:
            return (
              <h6 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
              </h6>
            );
          case 6:
            return (
              <h6 className={className}>
                <MarkdownTextSplitter selectable={true} text={token.text + unProcessedText}/>
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
          />
        );
      }
    case 'hr':
      return (null);
    case 'blockquote':
      return (
        <blockquote className={className}>
          <MarkdownTextSplitter selectable={true} className={`text-left ${defaultFontSize}`} text={token.text + unProcessedText}/>
        </blockquote>
      );
    case 'list':

      if (token.ordered) {
        return (
          <ol className={cn("not-prose w-auto", className)}>
            {token.items.map((v : Tokens.ListItem, k : number) => (
              <MarkdownMapComponent
                finished={finished}
                key={k}
                unProcessedText={(k === token.items.length-1)?unProcessedText:""}
                token={{...v, type: "list_item"}}
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
          />
        </li>
      );
    case 'paragraph':
      return (
        <p className={className}>
          <MarkdownTextSplitter 
            selectable={true} 
            className={`text-left text-base text-gray-200`} 
            text={token.text + unProcessedText}
          />
        </p>
      );
    case 'html':
      return (null);
    case 'text':
      return (
        <span className={className}>
          <MarkdownTextSplitter selectable={true} className={`text-left text-base text-gray-200`} text={token.text + unProcessedText}/>
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
} : {
  className?: string,
  unpacked?: boolean,
  input: string,
  transparentDisplay?: boolean,
  disableRender?: boolean,
  finished: boolean,
}) {
  const lexer = new marked.Lexer();

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
        <>
        {unpacked?(
          <>
            {lexer.lex(sanitizeMarkdown(input)).map((v : Token, k : number) => (
              <MarkdownMapComponent 
                key={k} 
                finished={finished}
                token={v} 
                unProcessedText={""}
              />
            ))}
          </>
        ):(
          <div className={cn("prose markdown text-sm text-theme-primary whitespace-pre-wrap break-words", className)}>
            <MarkdownRenderer 
              className={className}
              unpacked={true}
              input={input} 
              transparentDisplay={transparentDisplay}
              disableRender={disableRender}
              finished={finished}
            />
          </div>
        )}
        </>
      )}
    </>
  );
});

export default MarkdownRenderer;
