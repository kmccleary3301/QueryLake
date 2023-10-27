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
import HoverDocumentEntry from './HoverDocumentEntry';
import getChatHistory from '../hooks/getChatHistory';
import craftUrl from '../hooks/craftUrl';

type selectedState = [
    selected: boolean,
    setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionType = {
  title: string,
  items: number,
  id?: number,
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

type timeWindowType = {
  title: string,
  cutoff: number,
  entries: object[]
}

type SidebarChatHistoryProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<any>>,
  refreshSidePanel: string[],
  chatHistory: timeWindowType[],
  setChatHistory: React.Dispatch<React.SetStateAction<timeWindowType[]>>,
}
  
export default function SidebarChatHistory(props: SidebarChatHistoryProps) {

  // const [chatHistory, setChatHistory] = useState<timeWindowType[]>([]);

  // const timeWindows : timeWindowType[] = [
  //   {title: "Last 24 Hours", cutoff: 24*3600, entries: []},
  //   {title: "Last 2 Days", cutoff: 2*24*3600, entries: []},
  //   {title: "Past Week", cutoff: 7*24*3600, entries: []},
  //   {title: "Past Month", cutoff: 30*24*3600, entries: []},
  // ];

  const deleteSession = (chat_history_window_index : number, window_entry_index : number, hash_id : string) => {
    const url = craftUrl("http://localhost:5000/api/hide_chat_session", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "hash_id": hash_id
    });
    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        if (!data.success) {
          console.error("Failed to retrieve sessions", data.note);
          return;
        }
      })
    });
    let chat_history_tmp = props.chatHistory.slice();
    // chat_history_tmp[chat_history_window_index].entries = chat_history_tmp[chat_history_window_index].entries.splice(window_entry_index-1, 1);
    let entries_tmp = chat_history_tmp[chat_history_window_index].entries;
    chat_history_tmp[chat_history_window_index].entries = [...entries_tmp.slice(0, window_entry_index), ...entries_tmp.slice(window_entry_index+1, entries_tmp.length)];
    props.setChatHistory(chat_history_tmp);
  };
  
  return (
    <>
      <ScrollView style={{
          width: '100%',
          paddingHorizontal: 22,
          paddingTop: 10,
        }}
        showsVerticalScrollIndicator={false}
      >
        <View style={{paddingVertical: 10}}>
          <AnimatedPressable style={{
            width: '100%',
            backgroundColor: '#39393C',
            flexDirection: 'row',
            borderRadius: 20,
            // justifyContent: 'space-around',
            height: 36,
            alignItems: 'center',
            justifyContent: 'center'}}
            onPress={() => {
              props.setPageNavigateArguments("");
              props.setPageNavigateArguments("NEW");
              if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
              if (props.navigation) { props.navigation.navigate("ChatWindow"); }
            }}>
              <View style={{paddingRight: 5}}>
                <Feather name="plus" size={20} color="#E8E3E3" />
              </View>
              <View style={{alignSelf: 'center', justifyContent: 'center'}}>
              <Text style={{
                // width: '100%',
                // height: '100%',
                fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#E8E3E3',
                paddingTop: 1
              }}>{"New Chat"}</Text>
              </View>
          </AnimatedPressable>
        </View>
        {props.chatHistory.map((chat_history_window : timeWindowType, chat_history_index : number) => (
          <View key={chat_history_index}>
            {(chat_history_window.entries.length > 0) && (
              <>
              <Text style={{
                width: "100%",
                textAlign: 'left',
                fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#74748B',
                paddingBottom: 8,
                paddingTop: 8
              }}>
                {chat_history_window.title}
              </Text>
              {chat_history_window.entries.map((value, index : number) => (
                <View style={{paddingVertical: 5}} key={index}>
                  <HoverDocumentEntry
                    key={index}
                    title={(value.title !== null)?value.title:"Test"}
                    deleteIndex={() => {
                      deleteSession(chat_history_index, index, value.hash_id);
                    }}
                    textStyle={{
                      width: "100%",
                      textAlign: 'left',
                      paddingLeft: 10,
                      fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      color: '#E8E3E3'
                    }}
                    onPress={() => {
                      props.setPageNavigateArguments("chatSession-"+value.hash_id);
                      if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
                    }}
                  />
                </View>
              ))}
              </>
            )}
          </View>
        ))}
       
      </ScrollView>
    </> 
  );
}