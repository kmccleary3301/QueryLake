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
  refreshSidePanel: boolean
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
}

export default function SidebarColectionSelect(props: SidebarCollectionSelectProps) {
  const [collectionGroups, setCollectionGroups] = useState<collectionGroup[]>([]);

  useEffect(() => {
    const url = new URL("http://localhost:5000/api/fetch_all_collections");
    url.searchParams.append("username", props.userData.username);
    url.searchParams.append("password_prehash", props.userData.password_pre_hash);
    let collection_groups_fetch : collectionGroup[] = [];

    let retrieved_data = {};

    fetch(url, {method: "POST"}).then((response) => {
      // console.log(response);
      response.json().then((data) => {
        // console.log(data);
        retrieved_data = data;
        if (data["success"] == false) {
          console.error("Collection error:", data["note"]);
          return;
        }
        try {
          let personal_collections : collectionGroup = {
            title: "My Collections",
            collections: [],
          };
          for (let i = 0; i < data.result.user_collections.length; i++) {
            console.log(data.result.user_collections[i]);
            personal_collections.collections.push({
              "title": data.result.user_collections[i]["name"],
              "hash_id": data.result.user_collections[i]["hash_id"],
              "items": data.result.user_collections[i]["document_count"],
              "type": data.result.user_collections[i]["type"]
            })
          }
          collection_groups_fetch.push(personal_collections);
        } catch {}
        try {
          let global_collections : collectionGroup = {
            title: "Global Collections",
            collections: [],
          };
          for (let i = 0; i < data["result"]["global_collections"].length; i++) {
            global_collections.collections.push({
              "title": data["result"]["global_collections"][i]["name"],
              "hash_id": data["result"]["global_collections"][i]["hash_id"],
              "items": data["result"]["global_collections"][i]["document_count"],
              "type": data["result"]["global_collections"][i]["type"]
            })
          }
          collection_groups_fetch.push(global_collections);
        } catch {}
        try {
          let organization_ids = Object.keys(retrieved_data.result.organization_collections)
          for (let j = 0; j < organization_ids.length; j++) {
            try {
              let org_id = organization_ids[j];
              let organization_specific_collections : collectionGroup = {
                title: retrieved_data.result.organization_collections[org_id].name,
                collections: [],
              };
              for (let i = 0; i < retrieved_data.result.organization_collections[org_id].collections.length; i++) {
                organization_specific_collections.collections.push({
                  "title": retrieved_data.result.organization_collections[org_id].collections[i].name,
                  "hash_id": retrieved_data.result.organization_collections[org_id].collections[i].hash_id,
                  "items": retrieved_data.result.organization_collections[org_id].collections[i].document_count,
                  "type": retrieved_data.result.organization_collections[org_id].collections[i].type,
                })
              }
              collection_groups_fetch.push(organization_specific_collections)
            } catch {}
          }
        } catch {}
        setCollectionGroups(collection_groups_fetch);
      });
    });
    
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
              title={collectionGroups[k].title}
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