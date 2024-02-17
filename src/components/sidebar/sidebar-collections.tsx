// import {
//   View,
//   Text,
// } from 'react-native';
// import { ScrollView, TextInput } from 'react-native-gesture-handler';
// import { Feather } from '@expo/vector-icons';
// import { useEffect, useState } from 'react';
// import CollectionWrapper from './CollectionWrapper';
import CollectionWrapper from '../manual_components/collection-wrapper';
// import CollectionPreview from './CollectionPreview';
// import AnimatedPressable from './AnimatedPressable';
// import getUserCollections from '../hooks/getUserCollections';
// import { getUserCollections } from '@/hooks/querylakeAPI';
import { collectionGroup, pageID, selectedCollectionsType, userDataType } from '@/typing/globalTypes';
import { Button } from '@/components/ui/button';
import { useNavigate } from "react-router-dom";
import * as Icon from 'react-feather';
import { ScrollArea } from '../ui/scroll-area';
import { Input } from '../ui/input';
// import { Accordion } from '../ui/accordion';
import { useEffect } from 'react';

type SidebarCollectionSelectProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  setPageNavigate: React.Dispatch<React.SetStateAction<pageID>>,
  refreshSidePanel: string[]
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
  collectionGroups: collectionGroup[],
  setCollectionGroups: React.Dispatch<React.SetStateAction<collectionGroup[]>>,
  setCollectionSelected: (collection_hash_id : string, value : boolean) => void,
  selectedCollections: selectedCollectionsType
}

export default function SidebarCollectionSelect(props: SidebarCollectionSelectProps) {
	const navigate = useNavigate();
  // const [collectionGroups, setCollectionGroups] = useState<collectionGroup[]>([]);

  // useEffect(() => {
  //   let refresh = false;
  //   if (props.collectionGroups.length == 0) {
  //     refresh = true;
  //   } else {
  //     for (let i = 0; i < props.refreshSidePanel.length; i++) {
  //       if (props.refreshSidePanel[i] === "collections") {
  //         refresh = true;
  //         break;
  //       }
  //     }
  //   }
  //   if (refresh) {
  //     getUserCollections(props.userData.username, props.userData.password_pre_hash, props.setCollectionGroups);
  //   }
  // }, [props.refreshSidePanel]);

  // 

	useEffect(() => {
		console.log("Recieved collection groups:", props.collectionGroups);
	}, [props.collectionGroups]);

  const toggleMyCollections = (selected: boolean, group_key: number) => {
		// if (selected) {
		for (let i = 0; i < props.collectionGroups[group_key].collections.length; i++) {
			props.collectionGroups[group_key].toggleSelections?.[i].setSelected(selected);
		}
  };

  return (
    <>
      <div style={{
        width: '100%',
        // paddingVertical: 10,
        // paddingLeft: 22,
				// paddingRight: 22,
        paddingTop: 0,
        paddingBottom: 10,
        
      }}>
        <div style={{
					display: "flex",
          flexDirection: 'row',
          backgroundColor: '#23232D',
          // paddingTop: 6,
					// paddingBottom: 6,
          // paddingLeft: 10,
					// paddingRight: 10,
          borderRadius: 10,
        }}>
            <Input
              style={{
                color: '#E8E3E3',
                fontSize: 14,
                outlineStyle: 'none',
								outline: "none"
                // textAlignVertical: 'center'
              }}
              spellCheck={false}
							
              placeholder={'Search Public Collections'}
            />
        </div>
      </div>
      <ScrollArea className="h-[calc(100vh-308px)]" style={{
        width: '100%',
        paddingLeft: 0,
        paddingRight: 0,
        // paddingTop: 10,
      }}>
				{/* <Accordion type="single"> */}
					{props.collectionGroups.map((v, k) => (
						<div key={k} style={{paddingTop: (k === 0)?0:10}}>
						<CollectionWrapper
							title={v.title}
							// onToggleCollapse={() => {console.log("Toggle collapse upper");}} 
							onToggleSelected={(selected: boolean) => {
								toggleMyCollections(selected, k);
								if (props.onChangeCollections) { props.onChangeCollections(props.collectionGroups); }
							}}
							collections={v.collections}
							setPageNavigateArguments={props.setPageNavigateArguments}
							setCollectionSelected={props.setCollectionSelected}
							collectionSelected={props.selectedCollections}
						/>
						</div>
					))}
				{/* </Accordion> */}
        <div style={{paddingTop: 10, }}>
					<Button style={{
						display: "flex",
						width: '100%',
						backgroundColor: '#39393C',
						flexDirection: 'row',
						borderRadius: 20,
						// justifyContent: 'space-around',
						// paddingVertical: 10,
						height: 42,
						alignItems: 'center',
						justifyContent: 'center'}}
						onClick={() => {
							navigate("/create_collection");
							// if (props.setPageNavigate) { props.setPageNavigate("CreateCollectionPage"); }
							// if (props.navigation) { props.navigation.navigate("CreateCollectionPage"); }
						}}>
							<div style={{paddingRight: 10}}>
								<Icon.Plus size={20} color="#E8E3E3" />
							</div>
							<div style={{alignSelf: 'center', justifyContent: 'center'}}>
							<p style={{
								fontSize: 16,
								color: '#E8E3E3',
								paddingTop: 1
							}}>{"New Collection"}</p>
							</div>
					</Button>
        </div>
      </ScrollArea>
    </> 
  );
}