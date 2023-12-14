import { Text, View, ScrollView, Animated } from "react-native";
import { useState, useEffect } from "react";
// import Katex from "react-native-katex";
// import MarkdownTextAtomic from "./MarkdownTextAtomic";
import MarkdownTextSplitter from "./MarkdownTextSplitter";
import { Col, Grid } from "react-native-easy-grid";

type textSegment = {
  text: string,
  containerHeight?: number,
}

type tableEntry = {
  text: string,
  containerHeight?: number,
}

type MarkdownTableProps = {
  header: textSegment[],
  rows: textSegment[][],
  bubbleWidth: number,
  maxWidth: number,
  unProcessedText?: string,
  fontSize?: number,
}

function MarkdownTable(props : MarkdownTableProps){
  let columnCount = props.header.length;

  let row_heights_simple : number[] = Array(props.rows.length+1).fill(0);

  const [flippedArray, setFlippedArray] = useState<tableEntry[][]>([]);
  const [rowHeights, setRowHeights] = useState<number[]>([]);
  const [rowHeightsDelayed, setRowHeightsDelayed] = useState<number[]>([]);

  const [columnPadding, setColumnPadding] = useState<number[]>([]);
  const [maxColumnWidth, setMaxColumnWidth] = useState<number>();
  const [finalColumnLimits, setFinalColumnLimits] = useState<number[]>([]);
  const [limitsFinalized, setLimitsFinalized] = useState(false);

  const [rowsCombined, setRowsCombined] = useState<tableEntry[][]>([]);

  let get_layout_widths : number[][] = []; //column, then row.

  const fontSize = (props.fontSize !== undefined)?props.fontSize:14;
  const fontSizeHeightBoundary = fontSize*2;
  const tableEntryVerticalPadding = 5;
  const tableEntryRightPadding = 20;


  const [maxWidth, setMaxWidth] = useState(props.maxWidth);

  
  const [columnWidthMargins, setColumnWidthMarginsState] = useState<number[]>(Array(props.header.length).fill(0.92*props.bubbleWidth/props.header.length));
  let columnWidthMarginsDirect : number[] = Array(props.header.length).fill(0.92*props.bubbleWidth/props.header.length);
  
  const [columnLimitReached, setColumnLimitReachedState] = useState<boolean[]>(Array(props.header.length).fill(false));
  let columnLimitReachedDirect : boolean[] = Array(props.header.length).fill(false);

  const [columnUtilizedWidths, setColumnUtilizedWidthState] = useState<number[]>(Array(props.header.length).fill(0));
  let columnUtilizedWidthsDirect : number[] = Array(props.header.length).fill(0);

  useEffect(() => { 
    if (props.maxWidth < maxWidth) {
      const scaling_factor = props.maxWidth / maxWidth;
      for (let i = 0; i < props.header.length; i++) {
        columnWidthMarginsDirect[i] *= scaling_factor;
      }
    }

    setMaxWidth(props.maxWidth); 
  }, [props.maxWidth]);

  const setColumnWidthMargins = (col_index : number, value : number) => {
    // if (columnWidthMarginsDirect !== columnWidthMargins) {
    //   columnWidthMarginsDirect = columnWidthMargins;
    // }
    while (columnWidthMarginsDirect.length <= col_index) { columnWidthMarginsDirect.push(tableEntryRightPadding); }
    columnWidthMarginsDirect[col_index] = value;
    setColumnWidthMarginsState(columnWidthMarginsDirect);
  };


  const setColumnLimitReached = (col_index : number, value : boolean) => {
    while (columnLimitReachedDirect.length <= col_index) { columnLimitReachedDirect.push(false); }
    columnLimitReachedDirect[col_index] = value;

    if (value) {
      // console.log("Column limit reached, adding space");
      // console.log("Utilized widths", columnUtilizedWidthsDirect);
      // let widthCollected = 0;
      // for (let i = 0; i < props.header.length; i++) {
      //   if (!columnLimitReachedDirect[i]) {
      //     columnWidthMarginsDirect[i] -= 1;
      //     widthCollected += 1;
      //   }
      // }
      // columnWidthMarginsDirect[col_index] += widthCollected;
    }
    setColumnWidthMarginsState(columnWidthMarginsDirect);

  };

  useEffect(() => {

  }, [])
  let oldBubbleWidth = 40;

  useEffect(() => {
    let rows_combined_tmp = [props.header, ...props.rows];
    if (props.unProcessedText) { rows_combined_tmp[rows_combined_tmp.length - 1][rows_combined_tmp[0].length - 1].text += props.unProcessedText; }
    setRowsCombined([props.header, ...props.rows]);
    // console.log("Setting width margins to ", 0.92*props.bubbleWidth/props.header.length);
    columnWidthMarginsDirect = Array(props.header.length).fill(0.92*props.bubbleWidth/props.header.length);
    setColumnWidthMarginsState(columnWidthMarginsDirect);

    columnLimitReachedDirect = Array(props.header.length).fill(false);
    setColumnLimitReachedState(columnLimitReachedDirect);
    columnUtilizedWidthsDirect = Array(props.header.length).fill(0);
    setColumnUtilizedWidthState(columnUtilizedWidthsDirect);
  }, [props.header, props.rows]);

  useEffect(() => {
    if (props.bubbleWidth > oldBubbleWidth) {
      // console.log("Setting width margins to ", 0.92*props.bubbleWidth/props.header.length);
      columnWidthMarginsDirect = Array(props.header.length).fill(0.92*props.bubbleWidth/props.header.length);
      setColumnWidthMarginsState(columnWidthMarginsDirect);
    }
    oldBubbleWidth = props.bubbleWidth;
  }, [props.bubbleWidth]);

  useEffect(() => {
    // console.log("New Row Heights Detected:");
    // console.log(rowHeights);
    setRowHeightsDelayed(rowHeights);
  }, [rowHeights]);

  const tableEntryLayoutCallback = (col_index: number, row_index: number, width : number, height : number) => {
    // if (columnUtilizedWidthsDirect[col_index] < width) {
    //   columnUtilizedWidthsDirect[col_index] = width;
    //   setColumnUtilizedWidthState(columnUtilizedWidthsDirect);
      // if (columnUtilizedWidthsDirect[col_index] > width + 10) {
      //   setColumnWidthMargins(col_index, columnWidthMarginsDirect[col_index]-10);
      // }
    // }

    // console.log("Callback made with height:", height);
    // if (height >= (30)) {
    //   setColumnLimitReached(col_index, true);
    // }
  };

  return (
    <View style={{
      width: "100%",
      paddingVertical: 10,
      flexDirection: 'column'
    }}>
      {rowsCombined.map((row_value: textSegment[], row_index: number) => (
        <View 
          id={"Row Root Container"} 
          key={row_index} 
          style={{
            width: "100%",
            flexDirection: 'column',
          }}
        >
          {(row_index > 0) && (
            <View 
              id={"Divider"}
              style={{
                height: 1,
                backgroundColor: "#4D4D56",
                width: "100%"
              }}
            />
          )}
          <View
            id={"Row Wrapper"}
            style={{
              paddingHorizontal: 5,
              flexDirection: 'row'
            }}
          >
            {row_value.map((value : textSegment, col_index: number) => (
              // <View style={{flexDirection: 'column'}}>
              
              <View //This enforces the columns designated spacing so that everything lines up.
                id={"Entry-Column Alignment Spacer"}
                key={col_index}
                style={{
                  // width: (limitsFinalized)?finalColumnLimits[col_index]:columnPadding[col_index],
                  width: columnWidthMargins[col_index],
                  // width: "auto",
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'flex-start',
                  // borderBottomColor: '#FFFF00',
                  // borderBottomWidth: 1,
                }}
              >
                <View
                  id={"Entry Wrapper"}
                  style={{
                    // borderColor: "#0000FF",
                    // borderWidth: 1,

                    // borderTopColor: (columnLimitReached[col_index])?"#FF0000":"#0000FF",
                    maxWidth: "100%",
                  }}
                  onLayout={(event) => {
                    tableEntryLayoutCallback(col_index, row_index, event.nativeEvent.layout.width, event.nativeEvent.layout.height);
                  }}
                >
                  <MarkdownTextSplitter
                    bubbleWidth={props.bubbleWidth} 
                    text={value.text}
                    style={{
                      fontFamily: (row_index === 0)?"Inter-Bold":"Inter-Regular", 
                      fontSize: fontSize,
                      textAlign: 'left',
                      color: '#E8E3E3',
                      // width: '100%',
                      paddingRight: tableEntryRightPadding,
                      paddingBottom: tableEntryVerticalPadding,
                      paddingTop: tableEntryVerticalPadding,
                      maxWidth: '100%',

                      // borderColor: "#000000",
                      // borderWidth: 1,
                    }}
                  />
                </View>
              </View>
              // </View>
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}


export default MarkdownTable;