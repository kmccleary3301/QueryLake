import { useState, useEffect, useRef } from 'react';
import { ScrollView } from 'react-native-gesture-handler';

type ScrollViewBottomStickProps = {
  animateScroll: boolean,
  showsVerticalScrollIndicator?: boolean,
  style?: object,
  children?: any
};

export default function ScrollViewBottomStick(props: ScrollViewBottomStickProps) {
    // const [userIsScrolling, setUserIsScrolling] = useState(false);
    // const [stickToBottom, setStickToBottom] = useState(true);
    let stickToBottom = true;
    const scrollViewRef = useRef();
    let previousContentOffset = 0;

    return (
      <ScrollView 
        ref={scrollViewRef}
        onContentSizeChange={(contentWidth, contentHeight) => {
          if (stickToBottom) {
            scrollViewRef.current.scrollTo({y: contentHeight, animated: props.animateScroll});
          }
        }}
        scrollEventThrottle={16}
        onScroll={(e) => {
          // console.log(e);
          // console.log(e.nativeEvent.contentOffset);
          let current_y = e.nativeEvent.contentOffset.y;
          // console.log(current_y, bottomValue);
          let layoutHeight = e.nativeEvent.layoutMeasurement.height;
          let contentHeight = e.nativeEvent.contentSize.height;
          if ((current_y - previousContentOffset) < 0) {
            // setStickToBottom(false);
            stickToBottom = false;
          } else if (Math.abs(current_y + layoutHeight - contentHeight) <= 1) {
            // setStickToBottom(true);
            stickToBottom = true;
          }

          previousContentOffset = current_y;

        }}
        style={{
          flex: 5,
        }}
        showsVerticalScrollIndicator={props.showsVerticalScrollIndicator}
      >
        {(props.children) && (
          props.children
        )}
      </ScrollView>
    );
}