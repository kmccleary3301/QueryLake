import {
  View,
  Text,
  useWindowDimensions,
  Pressable,
  Platform,
} from 'react-native';
import { ScrollView, TextInput } from 'react-native-gesture-handler';
import { Feather } from '@expo/vector-icons';
import { useState } from 'react';
import CollectionWrapper from './CollectionWrapper';
import CollectionPreview from './CollectionPreview';

type selectedState = [
    selected: boolean,
    setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionGroup = {
    title: string,
    toggleSelections: selectedState[],
    selected: selectedState,
    collections: any,
};

const test_collections = [
    {
        "title": "Test Collectionsajdhfkshdkfhskd",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 55
    },
    {
        "title": "Test Collection",
        "items": 555
    },
    {
        "title": "Test Collection sdfasdfasdfsf",
        "items": 5555
    },
    {
        "title": "Test Collection",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 5
    },
    {
        "title": "Test Collection",
        "items": 5
    },
];

type SidebarCollectionSelectProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  // sidebarOpened?: boolean,
}

export default function SidebarColectionSelect(props: SidebarCollectionSelectProps) {
  // console.log(props);
  const [panelMode, setPanelMode] = useState("");

  let toggleSelections: selectedState[] = [];
  for (let i = 0; i < test_collections.length; i++) {
      toggleSelections.push(useState(false));
  }

  let CollectionGroups : collectionGroup[] = [
    {
      title: "My Collections",
      toggleSelections: [],
      selected: useState(false),
      collections: test_collections,
    },
    {
      title: "Added Collections",
      toggleSelections: [],
      selected: useState(false),
      collections: test_collections,
    }
  ];

  const reloadCollectionGroup = (group_key : number) => {
    CollectionGroups[group_key].toggleSelections = [];
    for (let i = 0; i < CollectionGroups[group_key].collections.length; i++) {
      CollectionGroups[group_key].toggleSelections.push(useState(false));
    } 
  };

  for (let i = 0; i < CollectionGroups.length; i++) {
      reloadCollectionGroup(i);
  }

  const toggleMyCollections = (selected: boolean, group_key: number) => {
      // if (selected) {
      for (let i = 0; i < CollectionGroups[group_key].collections.length; i++) {
          CollectionGroups[group_key].toggleSelections[i][1](selected);
      }
      // }
  };

  return (
    <>
      <View style={{
        width: '100%',
        // paddingVertical: 10,
        paddingHorizontal: 22,
        paddingTop: 10,
        paddingBottom: 10,
        
      }}>
        <View style={{
          flexDirection: 'row',
          backgroundColor: '#23232D',
          paddingVertical: 6,
          paddingHorizontal: 10,
          borderRadius: 10,
        }}>
          <Feather name="search" size={20} color="#E8E3E3" style={{flex: 1}}/>
          <View style={{width: '86%', height: "100%", paddingRight: 5}}>
            <TextInput
              style={Platform.select({
                web: {
                  color: '#E8E3E3',
                  fontSize: 14,
                  outlineStyle: 'none',
                  textAlignVertical: 'center'
                },
                default: {
                  color: '#E8E3E3',
                  fontSize: 14,
                  textAlignVertical: 'center'
                }
              })}
              spellCheck={false}
              placeholder={'Search Public Collections'}
              placeholderTextColor={'#E8E3E3'}
            />
          </View>
        </View>
      </View>
      <ScrollView style={{
          width: '100%',
          paddingHorizontal: 22,
          // paddingTop: 10,
        }}
      
      >
        {CollectionGroups.map((v, k) => (
          <View key={k} style={{
            paddingVertical: 5
          }}>
            <CollectionWrapper key={k} 
              title={CollectionGroups[k].title}
              // onToggleCollapse={() => {console.log("Toggle collapse upper");}} 
              onToggleSelected={(selected: boolean) => {
                toggleMyCollections(selected, k);
                if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
              }}
              selectedState={{
                selected: CollectionGroups[k].selected[0],
                setSelected: CollectionGroups[k].selected[1]
              }}
            >
              {CollectionGroups[k].collections.map((v_2, k_2) => (
                <CollectionPreview key={k_2}
                  style={{
                    paddingTop: (k_2===0)?0:5,
                  }}
                  title={CollectionGroups[k].collections[k_2].title}
                  selectedState={{
                    selected: CollectionGroups[k].toggleSelections[k_2][0],
                    setSelected: CollectionGroups[k].toggleSelections[k_2][1]
                  }}
                  documentCount={v_2.items}
                  onToggleSelected={(collection_selected: boolean) => {
                    if (!collection_selected &&  CollectionGroups[k].selected[0]) {
                      CollectionGroups[k].selected[1](false);
                    }
                    if (props.onChangeCollections) { props.onChangeCollections(CollectionGroups); }
                  }}
                />
              ))}
            </CollectionWrapper>
          </View>
        ))}
      </ScrollView>
    </> 
  );
}