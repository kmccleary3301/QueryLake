import { ReactNode } from 'react';

type ScrollViewBottomStickProps = {
  showsVerticalScrollIndicator?: boolean,
  style?: object,
  children?: ReactNode,
  bottomMargin: number,
};

export default function ScrollViewBottomStick(props: ScrollViewBottomStickProps) {
  return (
    <div className="mx-auto flex h-full flex-col" style={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      width: "100%",
    }}>
      <div className="group relative flex" style={{
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        width: "100%",
      }}>
        <div style={{
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          width: "100%",
        }}>
          <div style={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            // width: "100%",
          }}>
            <div style={{height: 1000}}/>
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