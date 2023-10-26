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

  
  const [columnWidthMargins, setColumnWidthMarginsState] = useState<number[]>([]);
  let columnWidthMarginsDirect : number[] = [];
  
  const [columnLimitReached, setColumnLimitReachedState] = useState<boolean[]>([]);
  let columnLimitReachedDirect : boolean[] = [];

  const [columnUtilizedWidths, setColumnUtilizedWidthState] = useState<number[]>([]);
  let columnUtilizedWidthsDirect : number[] = [];

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


  // useEffect(() => {
  //   setRowsCombined([props.header, ...props.rows]);
  //   setMaxColumnWidth(undefined);
  //   setFinalColumnLimits([]);
  //   columnCount = props.header.length;
  //   let flipped_array_tmp : tableEntry[][] = [];
  //   for (let i = 0; i < columnCount; i++) {
  //     let column_array_tmp = [{
  //       text: props.header[i].text,
  //       containerHeight: 20,
  //     }];
  //     flipped_array_tmp.push(column_array_tmp);
  //   }
  //   for (let i = 0; i < props.rows.length; i++) {
  //     for (let j = 0; j < columnCount; j++)
  //     flipped_array_tmp[j].push({
  //       text: props.rows[i][j].text,
  //       containerHeight: 20,
  //     });
  //   }
  //   setFlippedArray(flipped_array_tmp);

  //   let col_widths_tmp = [];
  //   for (let i = 0; i < props.header.length; i++) {
  //     col_widths_tmp.push(400);
  //   }
  //   setColumnPadding(col_widths_tmp);
  //   setLimitsFinalized(false);
  // }, [props.header, props.rows]);

  const setColumnLimitReached = (col_index : number, value : boolean) => {
    while (columnLimitReachedDirect.length <= col_index) { columnLimitReachedDirect.push(false); }
    columnLimitReachedDirect[col_index] = value;

    if (value) {
      let widthCollected = 0;
      for (let i = 0; i < props.header.length; i++) {
        if (!columnLimitReachedDirect[i]) {
          columnWidthMarginsDirect[i] -= 1;
          widthCollected += 1;
        }
      }
      columnWidthMarginsDirect[col_index] += widthCollected;
    }
    setColumnWidthMarginsState(columnWidthMarginsDirect)

  };

  useEffect(() => {
    setRowsCombined([props.header, ...props.rows]);
    console.log("Setting width margins to ", 0.96*props.bubbleWidth/props.header.length);
    columnWidthMarginsDirect = Array(props.header.length).fill(0.96*props.bubbleWidth/props.header.length);
    setColumnWidthMarginsState(columnWidthMarginsDirect);

    columnLimitReachedDirect = Array(props.header.length).fill(false);
    setColumnLimitReachedState(columnLimitReachedDirect);
  }, [props.header, props.rows]);


  // useEffect(() => {
  //   setRowsCombined([props.header, ...props.rows]);
  //   setMaxColumnWidth(undefined);
  //   setFinalColumnLimits([]);
  //   columnCount = props.header.length;
  //   let flipped_array_tmp : tableEntry[][] = [];
  //   for (let i = 0; i < columnCount; i++) {
  //     let column_array_tmp = [{
  //       text: props.header[i].text,
  //       containerHeight: 20,
  //     }];
  //     flipped_array_tmp.push(column_array_tmp);
  //   }
  //   for (let i = 0; i < props.rows.length; i++) {
  //     for (let j = 0; j < columnCount; j++)
  //     flipped_array_tmp[j].push({
  //       text: props.rows[i][j].text,
  //       containerHeight: 20,
  //     });
  //   }
  //   setFlippedArray(flipped_array_tmp);

  //   let col_widths_tmp = [];
  //   for (let i = 0; i < props.header.length; i++) {
  //     col_widths_tmp.push(400);
  //   }
  //   setColumnPadding(col_widths_tmp);
  //   setLimitsFinalized(false);
  // }, [props.header, props.rows]);

  useEffect(() => {
    console.log("New Row Heights Detected:");
    console.log(rowHeights);
    setRowHeightsDelayed(rowHeights);
  }, [rowHeights]);

  const updateRowHeight = (row_index : number, height : number) => {
    if (height < row_heights_simple[row_index]) { return; }
    row_heights_simple[row_index] = height;
    setRowHeights(row_heights_simple);
  };

  let layouts_processed = 0;

  const updateLayoutInitial = (col_index : number, row_index : number, value : number) => {
    if (get_layout_widths === undefined) { get_layout_widths = []; }
    while (get_layout_widths.length <= col_index) { get_layout_widths.push([]); }
    while (get_layout_widths[col_index].length <= row_index) { get_layout_widths[col_index].push(0); }

    layouts_processed += 1;
    get_layout_widths[col_index][row_index] = value;
    
    if (layouts_processed >= props.header.length*(props.rows.length+1)) { 
      calculateMaxColumnWidths(); 
      layouts_processed = 0;
    }

  };

  const calculateMaxColumnWidths = () => {
    if (maxColumnWidth === undefined) { return; }
    let final_width_limits = Array(props.header.length).fill(0);
    let max_width_used = [];
    for (let col_index = 0; col_index < props.header.length; col_index++) {
      let width_used = false;
      let max_width = 0;
      for (let row_index = 0; row_index <= props.rows.length; row_index++) {
        max_width = (get_layout_widths[col_index][row_index] >= max_width)?get_layout_widths[col_index][row_index]:max_width;
        if (get_layout_widths[col_index][row_index] >= maxColumnWidth/props.header.length) {
          width_used = true;
          max_width = maxColumnWidth/props.header.length;
          break;
        }
      }
      max_width_used.push({
        used: width_used,
        width: max_width
      });
    }
    let width_remaining = maxColumnWidth;
    let maxed_columns = props.header.length;
    for (let col_index = 0; col_index < props.header.length; col_index++) {
      if (!max_width_used[col_index].used) {
        width_remaining -= max_width_used[col_index].width;
        final_width_limits[col_index] = max_width_used[col_index].width;
        console.log("Width not used on column ", col_index, " width set to ", final_width_limits[col_index]);
        maxed_columns -= 1;
      }
    }

    for (let col_index = 0; col_index < props.header.length; col_index++) {
      if (max_width_used[col_index].used) {
        final_width_limits[col_index] = width_remaining/maxed_columns;
        console.log("Width used on column ", col_index, " width set to ", final_width_limits[col_index]);
      }
    }
    console.log("Final width limits");
    console.log(final_width_limits);
    setLimitsFinalized(true);
    setFinalColumnLimits(final_width_limits);
  };

  const tableEntryLayoutCallback = (col_index: number, row_index: number, width : number, height : number) => {
    if (columnUtilizedWidthsDirect[col_index] < width) {
      columnUtilizedWidthsDirect[col_index] = width;
      setColumnUtilizedWidthState(columnUtilizedWidthsDirect);
    }

    if (height >= fontSizeHeightBoundary + 2*tableEntryVerticalPadding) {
      setColumnLimitReached(col_index, true);
    }
  };

  return (
    <View
      style={{
        width: "100%",
        borderColor: "#00FF00",
        borderWidth: 1,
        paddingVertical: 10,
      }}
      onLayout={(event) => {
        // if (maxColumnWidth !== undefined) { return; }
        // console.log("Container Layout called.");
        // console.log(event.nativeEvent.layout.height);
        // setMaxColumnWidth(event.nativeEvent.layout.width);
      }}
    >
      <View style={{flexDirection: 'column'}}>
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
                    borderBottomColor: '#FFFF00',
                    borderBottomWidth: 1,
                    // borderTopColor: "#FF0000",
                    // borderTopWidth: (columnLimitReached[col_index])?1:0,

                    // borderTopWidth: 1,
                    // borderTopColor: "#4D4D56"
                  }}
                >
                  <View
                    id={"Entry Wrapper"}
                    style={{
                      borderColor: "#0000FF",
                      borderWidth: 1,

                      borderTopColor: (columnLimitReached[col_index])?"#FF0000":"#0000FF",
                      // borderTopWidth: 1,
                      // maxWidth: (limitsFinalized)?finalColumnLimits[col_index]:columnPadding[col_index]
                      maxWidth: "100%",
                    }}
                    onLayout={(event) => {
                      tableEntryLayoutCallback(col_index, row_index, event.nativeEvent.layout.width, event.nativeEvent.layout.height);
                    }}
                  >
                    <MarkdownTextSplitter
                      text={value.text}
                      style={{
                        fontFamily: "Inter-Regular", 
                        fontSize: fontSize,
                        textAlign: 'left',
                        color: '#E8E3E3',
                        // width: '100%',
                        paddingRight: tableEntryRightPadding,
                        paddingBottom: tableEntryVerticalPadding,
                        paddingTop: tableEntryVerticalPadding,
                        maxWidth: '100%',

                        borderColor: "#000000",
                        borderWidth: 1,
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
    </View>
  );
}


export default MarkdownTable;