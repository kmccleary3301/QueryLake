// import {
//   View,
//   Text,
//   useWindowDimensions,
// 	Pressable,
// 	Animated,
// 	Easing,
// 	ScrollView,
// } from 'react-native';
// import SwitchSelector from "react-native-switch-selector";
import { useEffect, useState, ReactNode } from 'react';
// import { Feather } from '@expo/vector-icons';
// import CollectionPreview from './CollectionPreview';
// import globalStyleSettings from '../../globalStyleSettings';
// import { Button } from '../ui/button';
// import { Accordion } from '../ui/accordion';
// import {
//   // Accordion,
//   AccordionContent,
//   AccordionItem,
//   AccordionTrigger,
// } from "@/components/ui/accordion"
// import { Checkbox } from "@/components/ui/checkbox"
import { selectedCollectionsType } from '@/globalTypes';
// import { CheckedState } from '@radix-ui/react-checkbox';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { motion, useAnimation } from "framer-motion";
// import { Button } from '../ui/button';
import * as Icon from 'react-feather';
import CollectionPreview from '@/components/manual_components/collection-preview';

type collectionType = {
  title: string,
  items: number,
  hash_id: string,
  type: string,
}

type CollectionWrapperProps = {
	onToggleCollapse?: (opened: boolean) => void,
	onToggleSelected?: (selected: boolean) => void,
	children?: ReactNode,
	title: string,
  collections: collectionType[],
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
  setCollectionSelected: (collection_hash_id : string, value : boolean) => void,
  collectionSelected: selectedCollectionsType
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(false);
	// const [selected, setSelected] = useState(false);
	// const [viewScrollable, setViewScrollable] = useState(false);
	const navigate = useNavigate();
	const [selected, setSelected] = useState(false);
  const [mixedSelection, setMixedSelection] = useState(true);
	// const {children, title} = props;
	
	// const selectionCircleSize = useRef(new Animated.Value(0)).current;
	// const boxHeight = useRef(new Animated.Value(42));


	const controlHeight = useAnimation();
	const selectionCircleSize = useAnimation();

	useEffect(() => {
		controlHeight.set({
			height: 42
		});
	}, [controlHeight]);

	useEffect(() => {
		controlHeight.start({
			height: (opened && props.collections.length > 0)?(props.collections.length*45+48):42,
			transition: { duration: 0.4 }
		});
  }, [opened, props.collections, controlHeight]);

  useEffect(() => {
    // Animated.timing(selectionCircleSize, {
    //   toValue: selected?11:0,
    //   duration: 100,
		// 	easing: Easing.elastic(1),
    //   useNativeDriver: false,
    // }).start();
		selectionCircleSize.start({
			width: selected?11:0,
			height: selected?11:0,

			transition: { duration: 0.1 }
		});
  }, [selected, selectionCircleSize]);


	useEffect(() => {
		console.log("PROP COLLECTIONS:", props.collections);
	}, [props.collections]);

	// return (
		// <AccordionItem value="item-1">
		// 	<AccordionTrigger>
		// 		{/* <Checkbox onCheckedChange={(checked: CheckedState) => {
		// 			const selected_value : boolean = (checked.valueOf() === true)?true:false;
		// 			setMixedSelection(false);
		// 			setSelected(selected_value);
		// 			for (let i = 0; i < props.collections.length; i++) {
		// 				const col_get : collectionType = props.collections[i];
		// 				props.setCollectionSelected(col_get.hash_id, selected_value);
		// 			}
		// 		}} id="terms1" /> */}
		// 		<p style={{
		// 			fontSize: 16,
		// 			color: "#FFFFFF",
		// 			textAlign: 'left',
		// 			height: 25,
		// 		}}>
		// 			{props.title}
		// 		</p>
		// 	</AccordionTrigger>
		// 	<AccordionContent>
		// 		<>
		// 			{props.collections.map((value : collectionType, index : number) => {
		// 				<div key={index}>
		// 					<Checkbox onCheckedChange={(checked: CheckedState) => {
		// 						const selected_value : boolean = (checked.valueOf() === true)?true:false;
		// 						setMixedSelection(false);
		// 						props.setCollectionSelected(value.hash_id, selected_value);
		// 						if (selected && !selected_value) {
		// 							// selected_values[index][1](false);
		// 							setMixedSelection(true);
		// 							setSelected(false);
		// 						}
		// 						// if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
		// 					}} id="terms1" />
		// 					<p 
		// 					// onClick={() => {
		// 					// 	navigate("/collection");
		// 					// }} 
		// 					style={{
		// 						fontSize: 16,
		// 						color: "#FFFFFF",
		// 						textAlign: 'left',
		// 						height: 25,
		// 					}}>
		// 						{value.title}
		// 					</p>
		// 				</div>
		// 			})}
		// 			<p>{"Test message"}</p>
		// 		</>
		// 	</AccordionContent>
		// </AccordionItem>
	// );

	return (
		<motion.div animate={controlHeight} style={{
			width: "100%",
			backgroundColor: "#39393C",
			display: "flex",
			flexDirection: 'column',
			borderRadius: 20,
			paddingTop: 8,
			overflow: "hidden"
		}}>
		{/* // <Accordion> */}
			<div style={{
				// height: 200,
				display: "flex",
				flexDirection: 'row',
				paddingRight: 16,
        paddingLeft: 12,
				paddingBottom: 12,
				// alignItems: 'center',
				// justifyContent: 'space-around',
			}}>
				<div style={{display: "flex", flexDirection: 'column', justifyContent: 'center', height: "100%"}}>
					<Button variant={"default"} style={{
						width: 21,
						height: 21,
						borderRadius: 12,
						backgroundColor: "#7968D9",
						display: "flex",
						alignItems: 'center',
						justifyContent: 'center',
						padding: 0,
						// flexDirection: 'column',
						// paddingLeft: 1,
					}}
					onClick={() => {
            setMixedSelection(false);
            for (let i = 0; i < props.collections.length; i++) {
              props.setCollectionSelected(props.collections[i].hash_id, !selected);
            }
						setSelected(selected => !selected);
						// if (props.onToggleSelected) { props.onToggleSelected(!selected); }
					}}
					>
						{/* {selected && ( */}
							<motion.div animate={selectionCircleSize} style={{
								borderRadius: "50%",
								backgroundColor: "#23232D"
							}}/>
						{/* )} */}
					</Button>
				</div>
				<div style={{
					width: '83%',
					display: "flex",
					flexDirection: 'column',
					justifyContent: 'center',
					paddingLeft: 9,
				}}>
					<p style={{
						fontSize: 16,
						color: "#FFFFFF",
						textAlign: 'left',
            height: 25,
					}}>
						{props.title}
					</p>
				</div>
				<div style={{display: "flex", flexDirection: 'column', justifyContent: 'center', padding: 0}}>
					<div style={{
						paddingTop: 0, 
						paddingBottom: 0, 
						paddingLeft: 0, 
						paddingRight: 0, 
						backgroundColor: "#00000000"
					}}
						onClick={() => {
							if (props.onToggleCollapse) { props.onToggleCollapse(!opened); }
							setOpened(opened => !opened);
						}}
					>
						<Icon.ChevronDown
							size={24} 
							color={"#E8E3E3"}
							style={{
								transform: opened?"rotate(0deg)":"rotate(90deg)"
							}}
						/>
					</div>
				</div>
			</div>
			
			<div style={{paddingBottom: 5, overflow: "hidden"}}>
				{props.collections.map((value : collectionType, index: number) => (
          <div style={{paddingBottom: 5}} key={index}>
            <CollectionPreview
              title={value.title} 
              documentCount={value.items} 
              onToggleSelected={(collection_selected: boolean) => {
                props.setCollectionSelected(value.hash_id, collection_selected);
                if (selected && !collection_selected) {
                  // selected_values[index][1](false);
                  setMixedSelection(true);
                  setSelected(false);
                  
                }
                // if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
              }}
              parentSelected={selected}
              parentMixedSelection={mixedSelection}
              onPress={() => {
                props.setPageNavigateArguments("collection-"+value.type+"-"+value.hash_id);
                // props.setPageNavigate("EditCollection");
								navigate("edit_collection");
              }}
              selectedPrior={props.collectionSelected.get(value.hash_id)}
            />
          </div>
        ))}
			</div>
		</motion.div>
	);
}