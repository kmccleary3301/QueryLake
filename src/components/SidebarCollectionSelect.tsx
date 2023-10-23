import {
  View,
  Text,
  useWindowDimensions,
  Pressable,
} from 'react-native';
import { ScrollView, TextInput } from 'react-native-gesture-handler';
import { Feather } from '@expo/vector-icons';
import { useEffect, useState } from 'react';
import CollectionWrapper from './CollectionWrapper';
import CollectionPreview from './CollectionPreview';
import AnimatedPressable from './AnimatedPressable';
import getUserCollections from '../hooks/getUserCollections';

type selectedState = [
  selected: boolean,
  setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionType = {
  title: string,
  items: number,
  hash_id: string,
  type: string,
}

type collectionGroup = {
  title: string,
  // toggleSelections: selectedState[],
  selected: selectedState,
  collections: collectionType[],
};

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type SidebarCollectionSelectProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  setPageNavigate: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  refreshSidePanel: string[]
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
}

export default function SidebarColectionSelect(props: SidebarCollectionSelectProps) {
  const [collectionGroups, setCollectionGroups] = useState<collectionGroup[]>([]);

  useEffect(() => {
    let refresh = false;
    if (collectionGroups.length == 0) {
      refresh = true;
    } else {
      for (let i = 0; i < props.refreshSidePanel.length; i++) {
        if (props.refreshSidePanel[i] === "collections") {
          refresh = true;
          break;
        }
      }
    }
    if (refresh) {
      getUserCollections(props.userData.username, props.userData.password_pre_hash, setCollectionGroups);
    }
  }, [props.refreshSidePanel]);

  // 

  const toggleMyCollections = (selected: boolean, group_key: number) => {
      // if (selected) {
      for (let i = 0; i < collectionGroups[group_key].collections.length; i++) {
          collectionGroups[group_key].toggleSelections[i][1](selected);
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
              style={{
                color: '#E8E3E3',
                fontSize: 14,
                outlineStyle: 'none',
                textAlignVertical: 'center'
              }}
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
      showsVerticalScrollIndicator={false}
      >
        {collectionGroups.map((v, k) => (
          <View key={k} style={{
            paddingVertical: 5
          }}>
            <CollectionWrapper key={k} 
              title={v.title}
              // onToggleCollapse={() => {console.log("Toggle collapse upper");}} 
              onToggleSelected={(selected: boolean) => {
                toggleMyCollections(selected, k);
                if (props.onChangeCollections) { props.onChangeCollections(collectionGroups); }
              }}
              collections={v.collections}
              setPageNavigate={props.setPageNavigate}
              setPageNavigateArguments={props.setPageNavigateArguments}
            >
              {/* {CollectionGroups[k].collections.map((v_2, k_2) => (
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
              ))} */}
            </CollectionWrapper>
          </View>
        ))}
        <View style={{paddingTop: 10, }}>
        <AnimatedPressable style={{
          width: '100%',
          backgroundColor: '#39393C',
          flexDirection: 'row',
          borderRadius: 20,
          // justifyContent: 'space-around',
          // paddingVertical: 10,
          height: 42,
          alignItems: 'center',
          justifyContent: 'center'}}
          onPress={() => {
            if (props.setPageNavigate) { props.setPageNavigate("CreateCollectionPage"); }
            if (props.navigation) { props.navigation.navigate("CreateCollectionPage"); }
          }}>
            <View style={{paddingRight: 10}}>
              <Feather name="plus" size={20} color="#E8E3E3" />
            </View>
            <View style={{alignSelf: 'center', justifyContent: 'center'}}>
            <Text style={{
              // width: '100%',
              // height: '100%',
              fontFamily: 'Inter-Regular',
              fontSize: 16,
              color: '#E8E3E3',
              paddingTop: 1
            }}>{"New Collection"}</Text>
            </View>
        </AnimatedPressable>
        </View>
      </ScrollView>
    </> 
  );
}