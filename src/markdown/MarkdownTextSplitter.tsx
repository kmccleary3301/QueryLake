import { Text } from "react-native";
import { useState, useEffect } from "react";
import Katex from "react-native-katex";
import MarkdownTextAtomic from "./MarkdownTextAtomic";

type MarkdownTextSplitterProps = {
    selectable?: boolean,
    style?: React.CSSProperties,
    text: string,
}

type textSegment = {
    text: string,
    type: "regular" | "bold" | "italic" | "bolditalic" | "mathjax_newline" | "mathjax_inline"
}

// function splitStringArrayRegex(stringArrayIn: string[], regexIn : RegExp) {
    
// }
// type markdownTextSegmentRenderProps = {
//     textSeg : textSegment
// }

// function markdownTextSegmentRender(props : markdownTextSegmentRenderProps){

//     return (
//         <>
//         {(props.textSeg.type === "mathjax_inline") && (
//             <Katex expression={props.textSeg.text}/>
//         )}
//         {(props.textSeg.type !== "mathjax_inline") && (
//             <Text>{props.textSeg.text}</Text>
//         )}
//         </>
//     );
// }

export default function MarkdownTextSplitter(props : MarkdownTextSplitterProps){
    const [textSplit, setTextSplit] = useState<textSegment[]>([]);
    useEffect(() => {
        let match = props.text.match(/(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)/);
        let index = 0;
        let string_segments : textSegment[] = [];
        if (match === null) {
            string_segments.push({
                text: props.text,
                type: "regular"
            });
        }
        while (match !== null) {
            if (match.index > 0) {
                console.log()
                string_segments.push({
                    text: props.text.slice(index, index+match.index),
                    type: "regular"
                })
            }
            if (match[0].length > 3 && match[0].slice(0, 3) === "***") {
                string_segments.push({
                    text: match[0].slice(3, match[0].length-3),
                    type: "bolditalic"
                });
            }
            else if (match[0].length > 2 && match[0].slice(0, 2) === "**") {
                string_segments.push({
                    text: match[0].slice(2, match[0].length-2),
                    type: "bold"
                });
            }
            else if (match[0].length > 2 && match[0].slice(0, 2) === "$$") {
                string_segments.push({
                    text: match[0].slice(2, match[0].length-2),
                    type: "mathjax_newline"
                });
            }
            else if (match[0].length > 1 && match[0].slice(0, 1) === "*") {
                string_segments.push({
                    text: match[0].slice(1, match[0].length-1),
                    type: "italic"
                });
            }
            else if (match[0].length > 1 && match[0].slice(0, 1) === "$") {
                string_segments.push({
                    text: match[0].slice(1, match[0].length-1),
                    type: "mathjax_inline"
                });
            }
            let new_index = index+match[0].length+match.index;
            match = props.text.slice(new_index).match(/(\$\$.*?\$\$|\$.*?\$|\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*)/);
            index = new_index;
        }
        setTextSplit(string_segments);
    }, [props.text]);

    return (
        <Text selectable={true} style={(props.style)?props.style:{}}>
            {/* {props.text} */}
            {textSplit.map((v : textSegment, k : number) => (
                <MarkdownTextAtomic key={k} textSeg={v}/>
            ))}
        </Text>
    );
}