import { useEffect, useState, ReactNode } from 'react';
import { selectedCollectionsType } from '@/types/globalTypes';
import { Button } from '@/registry/default/ui/button';
import { motion, useAnimation } from "framer-motion";
import * as Icon from 'react-feather';
import CollectionPreview from '@/components/manual_components/collection-preview';
import { redirect } from 'next/navigation'
// import { fontSans } from '@/lib/fonts';

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
  setCollectionSelected: (collection_hash_id : string, value : boolean) => void,
  collectionSelected: selectedCollectionsType
}

export default function CollectionWrapper(props: CollectionWrapperProps) {
	const [opened, setOpened] = useState(false);
	// const [selected, setSelected] = useState(false);
	// const [viewScrollable, setViewScrollable] = useState(false);
	const [selected, setSelected] = useState(false);
  const [mixedSelection, setMixedSelection] = useState(true);
	// const {children, title} = props;
	
	// const selectionCircleSize = useRef(new Animated.Value(0)).current;
	// const boxHeight = useRef(new Animated.Value(42));


	const controlHeight = useAnimation();
	const selectionCircleSize = useAnimation();

	useEffect(() => {
		controlHeight.set({
			height: 0
		});
	}, [controlHeight]);

	useEffect(() => {
		controlHeight.start({
			height: (opened && props.collections.length > 0)?"auto":0,
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


	// useEffect(() => {
	// 	console.log("PROP COLLECTIONS:", props.collections);
	// }, [props.collections]);

		return (
			
			<div className={"flex flex-col pr-[16px] pl-[12px] bg-secondary rounded-md"}>
				<div className="flex flex-row h-11">
					<div className="flex flex-col justify-center h-full">
						<Button variant={"default"} className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center p-0"
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
								<motion.div animate={selectionCircleSize} className="rounded-full bg-gray-800"/>
							{/* )} */}
						</Button>
					</div>
					<div className="flex flex-col flex-grow justify-center pl-[9px] whitespace-nowrap text-ellipsis overflow-hidden h-full">
						<span className="text-left">
							{props.title}
						</span>
					</div>
					<div className="flex flex-col justify-center p-0 h-full">
						<Button className="h-7 w-7 p-0 hover:bg-primary/20 active:bg-primary/10" variant={"ghost"}
							onClick={() => {
								if (props.onToggleCollapse) { props.onToggleCollapse(!opened); }
								setOpened(opened => !opened);
							}}
						>
							<Icon.ChevronDown
								style={{
									transform: opened?"rotate(0deg)":"rotate(90deg)"
								}}
							/>
						</Button>
					</div>
				</div>
				<motion.div animate={controlHeight} className="text-sm antialiased w-full overflow-hidden">
					<div className="overflow-hidden space-y-3 pb-2 pt-2">
						{props.collections.map((value : collectionType, index: number) => (
							<CollectionPreview
								key={index}
								title={value.title} 
								documentCount={value.items}
								collectionId={value.hash_id}
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
									redirect(`/collections/edit?id=${value.hash_id}`)
								}}
								selectedPrior={props.collectionSelected.get(value.hash_id)}
							/>
						))}
					</div>
				</motion.div>
			</div>
		);
	}
