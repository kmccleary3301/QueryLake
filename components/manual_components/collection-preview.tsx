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
import { Button } from '@/registry/default/ui/button';
import Link from 'next/link';

type CollectionPreviewProps = {
  selectedPrior?: boolean,
	onToggleSelected?: (selected: boolean) => void,
	title: string,
	documentCount: number;
	collectionId: string,
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
		<div className={`w-full flex flex-col`}>
			<div className="h-7 rounded-full flex flex-row">
				<div className="flex flex-1 flex-row">
					<div className="flex flex-col justify-center h-full">
						<Button className="w-5 h-5 rounded-full bg-indigo-600 items-center justify-center flex p-0"
							onClick={() => {
								if (props.onToggleSelected) { props.onToggleSelected(!selected); }
								setSelected(selected => !selected);
						}}>
							<motion.div animate={selectionCircleSize} className="rounded-full bg-[#23232D]"/>
						</Button>
					</div>
					<div className="w-full h-full flex flex-col justify-center pl-2">
						<div className="w-[83%] flex flex-row justify-start">
							<Link href={`/collection/edit/${props.collectionId}`}>
								<Button variant={"link"} className="text-base text-left pt-0 pb-0 pl-0 pr-0" onClick={props.onPress}>
									{title}
								</Button>
							</Link>
						</div>
					</div>
				</div>
				<div className="flex flex-col justify-center pl-1 pr-[3px]">
					<div className="w-11">
						<div className="flex flex-col items-end rounded-md">
							<p className="bg-[#E8E3E3] text-[#1F1F28] text-xs text-center flex items-end rounded-full pt-0.5 pb-0.5 pl-1.5 pr-1.5 align-bottom">
								{(documentCount <= 999)?documentCount.toString():"999+"}
							</p>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}