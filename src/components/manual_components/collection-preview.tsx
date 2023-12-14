// import {
//   View,
//   Text,
//   useWindowDimensions,
// 	Pressable,
// 	Animated,
// 	Easing
// } from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
import { useState, useEffect } from 'react';
// import { Feather } from '@expo/vector-icons';
// import AnimatedPressable from './AnimatedPressable';
// import globalStyleSettings from '../../globalStyleSettings';
import { motion, useAnimation } from "framer-motion";
import { Button } from '../ui/button';

type CollectionPreviewProps = {
  selectedPrior?: boolean,
	style?: React.CSSProperties,
	onToggleSelected?: (selected: boolean) => void,
	title: string,
	documentCount: number;
  onPress: () => void,
  parentSelected: boolean,
  parentMixedSelection: boolean,
}

export default function CollectionPreview(props: CollectionPreviewProps) {
  const [selected, setSelected] = useState((props.selectedPrior)?props.selectedPrior:false);

  useEffect(()=>{
    if (props.selectedPrior)
      setSelected(props.selectedPrior);
  }, [props.selectedPrior])
	const {title, documentCount} = props;

	const selectionCircleSize = useAnimation();

	useEffect(() => {
		selectionCircleSize.start({
			width: selected?11:0,
			height: selected?11:0,

			transition: { duration: 0.1 }
		});
  }, [selected, selectionCircleSize]);

  useEffect(() => {
    if (props.parentSelected) {
      setSelected(true);
    } else if (!props.parentMixedSelection && !props.parentMixedSelection) {
      setSelected(false);
    }
  }, [props.parentSelected, props.parentMixedSelection]);

	return (
		<div style={{
			...props.style,
			width: '100%',
			display: "flex",
			flexDirection: 'column',
			// justifyContent: 'space-around',
			// paddingVertical: 10,
			paddingLeft: 4,
			paddingRight: 4,
			// alignSelf: 'center',
		}}>
			<div style={{
				height: 40,
				borderRadius: 20,
				backgroundColor: "#23232D",
				display: "flex",
				flexDirection: 'row',
				paddingLeft: 8,
				paddingRight: -10,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}}>
        <div style={{display: "flex", flex:1, flexDirection: 'row'}}>
          <div style={{display: "flex", flexDirection: 'column', justifyContent: 'center', height: "100%"}}>
            <Button style={{
                width: 21,
                height: 21,
                borderRadius: 12,
                backgroundColor: "#7968D9",
                alignItems: 'center',
                justifyContent: 'center',
								display: "flex",
								padding: 0,
                // flexDirection: 'column',
                // paddingLeft: 1,
              }}
              onClick={() => {
                if (props.onToggleSelected) { props.onToggleSelected(!selected); }
                setSelected(selected => !selected);
            }}>
              {/* {selected && ( */}
							<motion.div animate={selectionCircleSize} style={{
								borderRadius: "50%",
								backgroundColor: "#23232D"
							}}/>
              {/* )} */}
            </Button>
          </div>
          <div style={{
            width: '100%',
            height: "100%",
						display: "flex",
            flexDirection: 'column',
            justifyContent: 'center',
            paddingLeft: 9,
          }}>
            <div style={{width: '83%', display: "flex", flexDirection: "row", justifyContent: "left"}}>
              <Button variant={"link"} style={{
                fontSize: 16,
                color: "#E8E3E3",
                textAlign: 'left',
								paddingTop: 0,
                paddingBottom: 0,
								paddingLeft: 0,
								paddingRight: 0
              }} onClick={props.onPress}>
                {title}
              </Button>
            </div>
          </div>
        </div>
				<div style={{display: "flex", flexDirection: 'column', justifyContent: 'center', paddingLeft: 5}}>
					{/* Notification count */}
					<div style={{
						// flexDirection: 'row',
						// justifyContent: 'flex-start',
						width: 45,
						paddingRight: 10,
						// alignSelf: 'flex-end',
					}}>
						<div style={{
							display: "flex",
							flexDirection: 'column',
							alignSelf: 'flex-end',
							// paddingHorizontal: 10,
							borderRadius: 10,
						}}>
							<p style={{
								backgroundColor: "#E8E3E3",
								color: "#1F1F28",
								fontSize: 11,
								textAlign: 'center',
								display: "flex",
								alignSelf: 'flex-end',
								borderRadius: 8,
								paddingTop: 2,
								paddingBottom: 2,
								paddingLeft: 6,
								paddingRight: 6,
								verticalAlign: 'bottom',
							}}>
								{(documentCount <= 999)?documentCount.toString():"999+"}
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}