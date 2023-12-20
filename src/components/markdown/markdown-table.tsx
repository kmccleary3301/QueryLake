// import { Text, View, ScrollView, Animated } from "react-native";
// import { useState, useEffect } from "react";
// // import Katex from "react-native-katex";
// // import MarkdownTextAtomic from "./MarkdownTextAtomic";
// import MarkdownTextSplitter from "./MarkdownTextSplitter";
// import { Col, Grid } from "react-native-easy-grid";
import MarkdownTextSplitter from "./markdown-text-splitter";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

type textSegment = {
  text: string,
  containerHeight?: number,
}

type MarkdownTableProps = {
  header: textSegment[],
  rows: textSegment[][],
  unProcessedText?: string,
  fontSize?: number,
}

function MarkdownTable(props : MarkdownTableProps){

  return (
    <Table style={{minWidth: "100%"}}>
      <TableHeader>
        <TableRow>
          {(props.header).map((header : textSegment, index : number) => (
            <TableHead key={index}>{header.text}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {props.rows.map((row : textSegment[], row_index : number) => (
          <TableRow key={row_index}>
            {row.map((entry : textSegment, col_index : number) => (
              <TableCell key={col_index} style={{
                // display: "flex",
                // flexDirection: "row",
                // justifyContent: "flex-start",
                // alignItems: "flex-start",
              }}>
                <div style={{
                  // flexShrink: 1,
                  display: "flex",
                  // flexShrink: 1,
                  // flexGrow: 1,
                  // display: "flex",
                  // flexDirection: "row",
                  justifyContent: "flex-start",
                }}>
                  <MarkdownTextSplitter
                    text={entry.text}
                    style={{
                      fontSize: 14,
                      color: '#E8E3E3',
                      flexShrink: 1,
                    }}
                  />
                </div>
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}


export default MarkdownTable;