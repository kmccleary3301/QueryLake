
// import { Feather } from '@expo/vector-icons';
import * as Icon from 'react-feather';
// import AnimatedPressable from './AnimatedPressable';
// import HoverDocumentEntry from './HoverDocumentEntry';
import HoverDocumentEntry from '../manual_components/hover_document_entry';
import craftUrl from '@/hooks/craftUrl';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import { userDataType, timeWindowType, collectionGroup } from '@/globalTypes';
import { useNavigate } from 'react-router-dom';


type SidebarChatHistoryProps = {
  onChangeCollections?: (collectionGroups: collectionGroup[]) => void,
  userData: userDataType,
  pageNavigateArguments: string,
  setPageNavigateArguments: React.Dispatch<React.SetStateAction<string>>,
  refreshSidePanel: string[],
  chatHistory: timeWindowType[],
  setChatHistory: React.Dispatch<React.SetStateAction<timeWindowType[]>>,
}
  
export default function SidebarChatHistory(props: SidebarChatHistoryProps) {
	const navigate = useNavigate();
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
    const chat_history_tmp = props.chatHistory.slice();
    // chat_history_tmp[chat_history_window_index].entries = chat_history_tmp[chat_history_window_index].entries.splice(window_entry_index-1, 1);
    const entries_tmp = chat_history_tmp[chat_history_window_index].entries;
    chat_history_tmp[chat_history_window_index].entries = [...entries_tmp.slice(0, window_entry_index), ...entries_tmp.slice(window_entry_index+1, entries_tmp.length)];
    props.setChatHistory(chat_history_tmp);
  };
  
  return (
    <>
      <ScrollArea className="h-[calc(100vh-262px)]" style={{
          width: '100%',
          paddingLeft: 22,
					paddingRight: 22,
          paddingTop: 0,
        }}
      >
        <div style={{paddingBottom: 10}}>
          <Button variant={"ghost"} style={{
            width: '100%',
            // backgroundColor: '#39393C',
						display: 'flex',
            flexDirection: 'row',
            borderRadius: 20,
            // justifyContent: 'space-around',
            height: 36,
            alignItems: 'center',
            justifyContent: 'center'}}
            onClick={() => {
              if (props.pageNavigateArguments === "NEW") {
                props.setPageNavigateArguments(" NEW");
              } else {
                props.setPageNavigateArguments("NEW");
              }
              navigate("/chat");
            }}>
              <div style={{paddingRight: 5}}>
                <Icon.Plus size={20} color="#E8E3E3" />
              </div>
              <div style={{alignSelf: 'center', justifyContent: 'center'}}>
              <p style={{
                // width: '100%',
                // height: '100%',
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#E8E3E3',
                paddingTop: 1
              }}>{"New Chat"}</p>
              </div>
          </Button>
        </div>
        {props.chatHistory.map((chat_history_window : timeWindowType, chat_history_index : number) => (
          <div key={chat_history_index}>
            {(chat_history_window.entries.length > 0) && (
              <>
              <p style={{
                width: "100%",
                textAlign: 'left',
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#74748B',
                paddingBottom: 8,
                paddingTop: 8
              }}>
                {chat_history_window.title}
              </p>
              {chat_history_window.entries.map((value, index : number) => (
                <div style={{paddingTop: 0, paddingBottom: 0}} key={index}>
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
                      // fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      color: '#E8E3E3',
											// height: "100%",
                    }}
										style={{
											width: "100%"
										}}
                    onPress={() => {
                      props.setPageNavigateArguments("chatSession-"+value.hash_id);
                      navigate("/chat");
                    }}
                  />
                </div>
              ))}
              </>
            )}
          </div>
        ))}
       
      </ScrollArea>
    </> 
  );
}