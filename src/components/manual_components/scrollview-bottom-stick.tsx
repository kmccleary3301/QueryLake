// import { useRef } from 'react';
// import { ScrollView } from 'react-native-gesture-handler';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReactNode } from 'react';

type ScrollViewBottomStickProps = {
  animateScroll: boolean,
  showsVerticalScrollIndicator?: boolean,
  style?: object,
  children?: ReactNode,
  height_string: string
};

export default function ScrollViewBottomStick(props: ScrollViewBottomStickProps) {
  // const [userIsScrolling, setUserIsScrolling] = useState(false);
  // const [stickToBottom, setStickToBottom] = useState(true);
  // let stickToBottom = true;
  // const scrollViewRef = useRef(0);
  // let previousContentOffset = 0;
  
  // "h-72 w-48 rounded-md border"
  const height_string_make = "calc(90vh-200px)";

  // return (
  //   <div style={{
  //     // display: "flex",
  //     // flex: 1,
  //     width: "100%",
  //     height: 400,
  //     overflowY: "scroll",
  //     // maxHeight: "100%",
  //     flexFlow: "column",
  //     overflow: "auto"
  //   }}>
  //     {(props.children) && (
  //       props.children
  //     )}
  //   </div>
  // )

  return (
    // <div className="w-full px-[3%] flex flex-col flex-grow h-full"> {/* Set parent container to 100% height */}
      <div className={"flex flex-grow py-4 gap-x-4 items-start flex-1"} style={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "center"
      }}>
        <div className={"h-["+height_string_make+"]"} style={{
          position: "absolute"
        }}>
          <ScrollArea style={{overflow: "hidden"}} className={"overflow-hidden flex flex-col gap-y-4 overflow-y-auto h-[calc(100vh-57px)]"}>
            {(props.children) && (
              props.children
            )}
          </ScrollArea>
        </div>
      </div>
    // </div>
  );

  // return (
  //   <div className="flex flex-grow py-0 gap-x-4 items-start" style={{
  //     display: "flex",
  //     flexDirection: "column",
  //     flex: 5,
  //   }}>
  //     <div style={{
  //       // maxHeight: '100%',
  //       height: "100%",
  //       width: "100%",
  //       borderWidth: 2,
  //       borderColor: "#FF0000",
  //     }}>
  //       <ScrollArea className="flex-auto-1">
  //         {(props.children) && (
  //           props.children
  //         )}
  //       </ScrollArea>
  //     </div>
  //   </div>
  // );

  // return (
  //   <ScrollArea 
  //     ref={scrollViewRef}
  //     onContentSizeChange={(contentWidth, contentHeight) => {
  //       if (stickToBottom && scrollViewRef.current !== undefined) {
  //         scrollViewRef.current.scrollTo({y: contentHeight, animated: props.animateScroll});
  //       }
  //     }}
  //     scrollEventThrottle={16}
  //     onScroll={(e) => {
  //       // console.log(e);
  //       // console.log(e.nativeEvent.contentOffset);
  //       let current_y = e.nativeEvent.contentOffset.y;
  //       // console.log(current_y, bottomValue);
  //       let layoutHeight = e.nativeEvent.layoutMeasurement.height;
  //       let contentHeight = e.nativeEvent.contentSize.height;
  //       if ((current_y - previousContentOffset) < 0) {
  //         // setStickToBottom(false);
  //         stickToBottom = false;
  //       } else if (Math.abs(current_y + layoutHeight - contentHeight) <= 1) {
  //         // setStickToBottom(true);
  //         stickToBottom = true;
  //       }

  //       previousContentOffset = current_y;

  //     }}
  //     style={{
  //       flex: 5,
  //     }}
  //     showsVerticalScrollIndicator={props.showsVerticalScrollIndicator}
  //   >
  //     {(props.children) && (
  //       props.children
  //     )}
  //   </ScrollView>
  // );
}