import * as fs from "fs";
import { INITIAL, parseRawGrammar, Registry } from "vscode-textmate";
import grammar from "./Python";
import python_code from "./testPythonFile";
// const oniguruma = require('vscode-oniguruma');  
import hljs from 'highlight.js';

export default function testTextMate() {
    
    console.log(hljs.highlight(python_code, {language: 'python'}));

    // const registry = new Registry({
    //     onigLib: vscodeOnigurumaLib,
    //     loadGrammar: (scopeName) => {
    //         if (scopeName === 'source.js') {
    //             // https://github.com/textmate/javascript.tmbundle/blob/master/Syntaxes/JavaScript.plist
    //             return readFile('./JavaScript.plist').then(data => vsctm.parseRawGrammar(data.toString()))
    //         }
    //         console.log(`Unknown scope name: ${scopeName}`);
    //         return null;
    //     }
    // });

    // registry.loadGrammar('source.js').then(grammar => {
    //     const text = [
    //         `function sayHello(name) {`,
    //         `\treturn "Hello, " + name;`,
    //         `}`
    //     ];
    //     let ruleStack = vsctm.INITIAL;
    //     for (let i = 0; i < text.length; i++) {
    //         const line = text[i];
    //         const lineTokens = grammar.tokenizeLine(line, ruleStack);
    //         console.log(`\nTokenizing line: ${line}`);
    //         for (let j = 0; j < lineTokens.tokens.length; j++) {
    //             const token = lineTokens.tokens[j];
    //             console.log(` - token from ${token.startIndex} to ${token.endIndex} ` +
    //               `(${line.substring(token.startIndex, token.endIndex)}) ` +
    //               `with scopes ${token.scopes.join(', ')}`
    //             );
    //         }
    //         ruleStack = lineTokens.ruleStack;
    //     }
    // });

//   const grammar_get = parseRawGrammar(grammar);
//   // const registry = new Registry({
//   //   loadGrammar: parseRawGrammar(grammar)
//   // });
//   grammar_get.
  
//   python_code
//   .split("\n")
//   .reduce((previousRuleStack, line) => {
//       console.info(`Tokenizing line: ${line}`);
//       const { ruleStack, tokens } = grammar_get.tokenizeLine(line, previousRuleStack);
//       tokens.forEach((token) => {
//           console.info(
//               ` - ${token.startIndex}-${token.endIndex} (${line.substring(
//                   token.startIndex,
//                   token.endIndex
//                   )}) with scopes ${token.scopes.join(", ")}`
//                   );
//               });
//               return ruleStack;
//           }, INITIAL);
              
  // python_code.split("\n").reduce((previousRuleStack, line) => {
  //               console.info(`Tokenizing line: ${line}`);
  //               const { ruleStack, tokens } = grammar.tokenizeLine(line, previousRuleStack);
  //               tokens.forEach((token) => {
  //                   console.info(
  //                       ` - ${token.startIndex}-${token.endIndex} (${line.substring(
  //                           token.startIndex,
  //                           token.endIndex
  //                           )}) with scopes ${token.scopes.join(", ")}`
  //                           );
  //                       });
  //                       return ruleStack;
  //                   }, INITIAL);
  //               },
  //               (error) => {
  //                   console.error(error);
  //               }
  //               );
  // fetch(raw)
  // .then(r => r.text())
  // .then(text => {
  //   console.log('text decoded:', text);
  // });
  // console.log(raw);
  // const showFile = async (e) => {
  //   e.preventDefault()
  //   const reader = new FileReader();
  //   reader.onload = async (e) => { 
  //     const text = (e.target.result)
  //     console.log(text);
  //     // alert(text)
  //   };
  //   reader.readAsText(e.target.files[0]);
  // }

  // showFile()
    // const registry = new Registry({
        
        // eslint-disable-next-line @typescript-eslint/require-await
        // loadGrammar: async (scopeName) => {
        //     const reader = new FileReader();
        //     if (scopeName === "source.ts") {
        //         return new Promise<string>((resolve, reject) =>
        //         fs.readFile("./grammars/TypeScript.tmLanguage", (error, data) =>
        //             error !== null ? reject(error) : resolve(data.toString())
        //             )
        //             ).then((data) => parseRawGrammar(data));
        //         }
        //         console.info(`Unknown scope: ${scopeName}`);
        //         return null;
        //     },
        // });
        
}