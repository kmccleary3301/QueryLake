import { ReactNode, StyleHTMLAttributes } from 'react';
// import { Button } from "../ui/button";
// import * as Icon from 'react-feather';

type ScrollViewBottomStickInnerProps = {
  showsVerticalScrollIndicator?: boolean,
  style?: StyleHTMLAttributes<HTMLDivElement>,
  children?: ReactNode,
  bottomMargin: number,
};

export default function ScrollViewBottomStickInner(props: ScrollViewBottomStickInnerProps) {
  // const scrollValue = useRef(0);

  // const [autoScroll, setAutoScroll] = useState(false);



  return (
    <div className="mx-auto flex h-full flex-col" style={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "flex-start",
      width: "100%",
    }}>
      <div className="group relative flex" style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        width: "100%",
      }} onScroll={(e) => {
        console.log("onScroll2: ", e);
      }}>
        <div style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          width: "100%",
        }} onScroll={(e) => {
          console.log("onScroll3: ", e);
        }}>
          <div style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            // width: "100%",
          }}>
            <div style={{height: 20}}/>
            <div>
              {(props.children) && (
                props.children
              )}
            </div>
            
            <div style={{height: props.bottomMargin}}/>
          </div>
        </div>
      </div>
        
      
    </div>
  );
}