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

type SidebarChatHistoryProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<any>>,
  refreshSidePanel: boolean,
}
  
export default function SidebarChatHistory(props: SidebarChatHistoryProps) {
  const [chatHistoryToday, setChatHistoryToday] = useState([]);
  const [chatHistoryYesterday, setChatHistoryYesterday] = useState([]);
  const [chatHistoryWeek, setChatHistoryWeek] = useState([]);
  const [chatHistoryMonth, setChatHistoryMonth] = useState([]);
  const [chatHistoryOlder, setChatHistoryOlder] = useState([]);

  const currentTime = Date.now()/1000;
  
  const today_difference = 24*3600;
  const yesterday_difference = 2*24*3600;
  const week_difference = 7*24*3600;
  const month_difference = 30*24*3600;


  useEffect(() => {
    const url = new URL("http://localhost:5000/fetch_chat_sessions");
    url.searchParams.append("username", props.userData.username);
    url.searchParams.append("password_prehash", props.userData.password_pre_hash);
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        console.log(data);
        if (!data.success) {
          console.error("Failed to retrieve sessions");
          return;
        }
        let chat_history_tmp_today = [];
        let chat_history_tmp_yesterday = [];
        let chat_history_tmp_week = [];
        let chat_history_tmp_month = [];
        let chat_history_tmp_older = [];
        for (let i = 0; i < data.result.length; i++) {
          let entry = {
            time: data.result[i].time,
            title: data.result[i].title,
            hash_id: data.result[i].hash_id,
          };
          console.log((currentTime - entry.time));
          if ((currentTime - entry.time) < today_difference) { chat_history_tmp_today.push(entry); }
          else if ((currentTime - entry.time) < yesterday_difference) { chat_history_tmp_yesterday.push(entry); }
          else if ((currentTime - entry.time) < week_difference) { chat_history_tmp_week.push(entry); }
          else if ((currentTime - entry.time) < month_difference) { chat_history_tmp_month.push(entry); }
          else { chat_history_tmp_older.push(entry); }
        }
        setChatHistoryToday(chat_history_tmp_today);
        setChatHistoryYesterday(chat_history_tmp_yesterday);
        setChatHistoryWeek(chat_history_tmp_week);
        setChatHistoryMonth(chat_history_tmp_month);
        setChatHistoryOlder(chat_history_tmp_older);
      });
    });

  }, [props.refreshSidePanel]);

  const deleteSession = () => {
    
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
        {(chatHistoryToday.length > 0) && (
          <>
          <Text style={{
            width: "100%",
            textAlign: 'left',
            fontFamily: 'Inter-Regular',
            fontSize: 16,
            color: '#74748B',
            paddingBottom: 10,
          }}>
            {"Today"}
          </Text>
          {chatHistoryToday.map((value, index : number) => (
            <View style={{paddingVertical: 5}} key={index}>
              <HoverDocumentEntry
                key={index}
                title={(value.title !== null)?value.title:"Test"}
                deleteIndex={() => {

                }}
                textStyle={{
                  width: "100%",
                  textAlign: 'left',
                  paddingLeft: 10,
                  fontFamily: 'Inter-Regular',
                  fontSize: 16,
                  color: '#E8E3E3'
                }}
                onPress={() => {
                  props.setPageNavigateArguments(value.hash_id);
                  if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
                }}
              />
            </View>
          ))}
          </>
        )}
        {(chatHistoryYesterday.length > 0) && (
          <>
          <Text style={{
            width: "100%",
            textAlign: 'left',
            fontFamily: 'Inter-Regular',
            fontSize: 16,
            color: '#74748B',
            paddingBottom: 10,
          }}>
            {"Yesterday"}
          </Text>
          {chatHistoryYesterday.map((value, index : number) => (
            <View style={{paddingVertical: 5}} key={index}>
              <HoverDocumentEntry
                // key={index}
                title={(value.title !== null)?value.title:"Test"}
                deleteIndex={() => {

                }}
                textStyle={{
                  width: "100%",
                  textAlign: 'left',
                  paddingLeft: 10,
                  fontFamily: 'Inter-Regular',
                  fontSize: 16,
                  color: '#E8E3E3'
                }}
                onPress={() => {
                  props.setPageNavigateArguments(value.hash_id);
                  if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
                }}
              />
            </View>
          ))}
          </>
        )}
      </ScrollView>
    </> 
  );
}