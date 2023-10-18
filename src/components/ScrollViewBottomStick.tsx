import { useState, useEffect, useRef } from 'react';
import { ScrollView } from 'react-native-gesture-handler';

type ScrollViewBottomStickProps = {
  showsVerticalScrollIndicator?: boolean,
  style?: object,
  children?: any
};

export default function ScrollViewBottomStick(props: ScrollViewBottomStickProps) {
    const [userIsScrolling, setUserIsScrolling] = useState(false);
    const [stickToBottom, setStickToBottom] = useState(true);
    const scrollViewRef = useRef();

    return (
      <ScrollView 
        ref={scrollViewRef}
        onContentSizeChange={(contentWidth, contentHeight) => {
          if (stickToBottom) {
            scrollViewRef.current.scrollTo({y: contentHeight, animated: true});
          }
        }}
        scrollEventThrottle={16}
        onScroll={(e) => {
          console.log(e);
          console.log(e.nativeEvent.contentOffset);
          let current_y = e.nativeEvent.contentOffset.y;
          // console.log(current_y, bottomValue);
          let layoutHeight = e.nativeEvent.layoutMeasurement.height;
          let contentHeight = e.nativeEvent.contentSize.height;
          if (stickToBottom && Math.abs(current_y + layoutHeight - contentHeight) > 20) {
            // setStickToBottom(false);
          } else if (Math.abs(current_y + layoutHeight - contentHeight) <= 1) {
            setStickToBottom(true);
          }
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