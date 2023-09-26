import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  Pressable,
  TextInput,
  StatusBar,
  Modal,
  Button,
  Alert,
  Platform,
  Animated,
  Easing
} from "react-native";
import Clipboard from "@react-native-clipboard/clipboard";
import { Feather } from "@expo/vector-icons";
import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
import EventSource from "../react-native-server-sent-events";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import Icon from "react-native-vector-icons/FontAwesome";
import ChatBarInputWeb from "../components/ChatBarInputWeb";
import ChatBarInputMobile from "../components/ChatBarInputMobile";

type CodeSegmentExcerpt = {
  text: string,
  color: string,
};

type CodeSegment = CodeSegmentExcerpt[];

type ChatContentExcerpt = string | CodeSegment;

type ChatContent = ChatContentExcerpt[];

type ChatEntry = {
  origin: ("user" | "server"),
  content: ChatContent,
};

export default function ChatWindow({ navigation }) {
  const scrollViewRef = useRef();
  const inputTwo = useRef("");
  const [inputText, setInputText] = useState(
    "Write a python function that calculates the Fibonacci sequence up to a given number n. Include type hints and a function description."
  );
  const [isEnabled, setIsEnabled] = useState(false);
  const [chat, setChat] = useState("Sure! Here's a Python function that calculates the Fibonacci sequence up to a given number n:\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nHello");
  const [sseOpened, setSseOpened] = useState(false);
  const [fileDragHover, setFileDragHover] = useState(false);
  const [filesPrepared, setFilesPrepared] = useState<File[]>([]);
  const [filesProgress, setFilesProgress] = useState<Number[]>([]);
  const [submitInput, setSubmitInput] = useState(false);
  
  const [newChat, setNewChat] = useState<ChatEntry[]>([]);
  
  const [temporaryBotEntry, setTemporaryBotEntry] = useState<ChatEntry | null>(null);

  const [inputLineCount, setInputLineCount] = useState(1);

  const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  const PlatformIsWeb = Platform.select({web: true, default: false});

  useFonts({
    YingHei: require("../../assets/fonts/MYingHeiHK-W4.otf"),
  });

  let genString = "";
  let termLet: string[] = [];

  const copyToClipboard = () => {
    Clipboard.setString(inputText);
  };

  const copyChatToClipboard = () => {
    Clipboard.setString(chat);
  };

  const sse_fetch = async function (message : string) {
    if (sseOpened === true) {
      return;
    }
    console.log("Starting SSE");

    const url = new URL("http://localhost:5000/chat");
    url.searchParams.append("query", message);


    let user_entry : ChatEntry = {
      origin: "user",
      content: [message],
    };
    
    setNewChat(newChat => [...newChat, user_entry])
    
    let bot_entry : ChatEntry = {
      origin: "server",
      content: [""] //This needs to be changed, currenty only suits the plaintext returns from server.
    }

    setTemporaryBotEntry(bot_entry);
    // setInputText("");

    console.log(url.toString());
    const es = new EventSource(url, {
      method: "GET",
    });

    es.addEventListener("open", (event) => {
      console.log("Open SSE connection.");
      setSseOpened(true);
    });

    es.addEventListener("message", (event) => {
      // console.log("New message event:", event);
      if (event === undefined || event.data === undefined) return;
      let decoded = event.data.toString();
      if (decoded == "-DONE-") {
        setNewChat(newChat => [...newChat, bot_entry])
        setTemporaryBotEntry(null);
        es.close();
      } else {
        // for (let key in Object.keys(uri_decode_map)) {
        //   decoded = decoded.replace(key, uri_decode_map[key]);
        // }
        decoded = decodeURI(decoded);
        console.log([decoded]);
        genString += decoded;
        setChat(genString);
        bot_entry["content"][0] = genString; //Needs to be cahnged for syntax highlighting.
        setTemporaryBotEntry(bot_entry);
      }

      // setLog(chat+" HELLOOOOOOOOOOOO"+chat+chat);
    });

    es.addEventListener("error", (event) => {
      if (event.type === "error") {
        console.error("Connection error:", event.message);
      } else if (event.type === "exception") {
        console.error("Error:", event.message, event.error);
      }
    });

    es.addEventListener("close", (event) => {
      console.log("Close SSE connection.");
      setSseOpened(false);
    });
  };

  const handleSwitch = (event: any) => {
    setIsEnabled(true);
    event.preventDefault();
    console.log("switch on");
  };

  const toggleSwitch = () => setIsEnabled((previousState) => !previousState);

  const handleDrop = (event: any) => {
    setFileDragHover(false);
    event.preventDefault();
    setFilesPrepared(event.dataTransfer.files);
    console.log("Set files to:", event.dataTransfer.files);
    let formData = new FormData();
    formData.append("file", event.dataTransfer.files[0]);
    const uploader = createUploader({
      destination: {
        method: "POST",
        url: "http://localhost:5000/uploadfile",
        filesParamName: "file",
      },
      autoUpload: true,
      grouped: true,

      //...
    });

    uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
      console.log(`item ${item.id} started uploading`);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
      console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
    });

    uploader.add(event.dataTransfer.files[0]);
    // // fetch("http://localhost:5000/uploadfile", {method: "POST", body: formData});
    // axios.request({
    //   method: "post",
    //   url: "http://localhost:5000/uploadfile",
    //   data: formData,
    //   onUploadProgress: (p) => {
    //     console.log(p);
    //     //this.setState({
    //         //fileprogress: p.loaded / p.total
    //     //})
    //   }
    // }).then (data => {
    //     //this.setState({
    //       //fileprogress: 1.0,
    //     //})
    //     console.log("Then hook called");
    // })
  };


  const onMessageSend = (message : string) => {
    sse_fetch(message);
  };

  const log_key_press = (e: {
    nativeEvent: { key: string; shiftKey: boolean };
  }) => {
    if (e.nativeEvent.key === "Enter" && e.nativeEvent.shiftKey === false) {
      setSubmitInput(true);
    }
  };
  
  const inputBoxHeight = useRef(new Animated.Value(26)).current;
  
  useEffect(() => {
    if (submitInput && inputText !== "") {
      setSubmitInput(false);
      setInputText("");
      inputBoxHeight.setValue(26);
      setInputLineCount(1);
    }
  }, [inputText]);


	useEffect(() => {
    Animated.timing(inputBoxHeight, {
      toValue: (24*inputLineCount+6),
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 200,
			easing: Easing.elastic(1),
      useNativeDriver: true,
    }).start();
  }, [inputLineCount]);

  return (
    <View style={styles.container}>
      <View style={{
        flexDirection: "column",
        // flex: 5,
        height: "100%",
        width: "88%",
        paddingHorizontal: 0,
        // paddingVertical: 24,
      }}>
        <ScrollView style={{
          flex: 5,

        }}>
          <Text
            style={{
              color: "#E8E3E3",
              fontSize: 20,
              // fontFamily: "YingHei",
              flex: 1,
              flexDirection: "column",
            }}
          >
            {inputText}
          </Text>
          <View style={styles.chatBoxContainer}>
            <Text
              style={{
                color: "white",
                // fontFamily: "YingHei",
                fontSize: 20,
                flex: 1,
                flexDirection: "column",
              }}
            >
              {chat}
            </Text>
            <Pressable>
              <Icon
                name="copy"
                size={30}
                style={styles.chatBoxContainerCopyButton}
                onPress={copyToClipboard}
              ></Icon>
            </Pressable>
            <ScrollView
              style={styles.chatBoxPrimary}
              ref={scrollViewRef}
              onContentSizeChange={() =>
                scrollViewRef.current.scrollToEnd({ animated: true })
            }>
              <Text style={styles.chatBoxText}>{chat}</Text>
              <Pressable>
                <Icon
                  name="copy"
                  size={30}
                  style={styles.chatBoxContainerCopyButton}
                  onPress={copyChatToClipboard}
                ></Icon>
              </Pressable>
            </ScrollView>
          </View>
        </ScrollView>

        

        <View id="InputBox" style={{
          flexDirection: 'column',
          justifyContent: 'space-around',
          // flex: 1,
          // height: 200,
          width: '100%',
          paddingVertical: 10,
        }}>
          <View style={{paddingBottom: 5}}>
          <View id="Switch" style={{
            // width: 200,
            width: 150,
            height: 28,
            borderRadius: 14,
            // backgroundColor: '#4D4D56',
            borderWidth: 1,
            borderColor: '#4D4D56',
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            paddingLeft: 3,
          }}>
            <Switch
              trackColor={{ false: "#4D4D56", true: "#7968D9" }}
              // thumbColor={isEnabled ? "#D9D9D9" : "#D9D9D9"}
              thumbColor={"#D9D9D9"}
              
              
              onValueChange={toggleSwitch}
              value={isEnabled}
            />
            <Text
              style={{
                color: "#4D4D56",
                fontSize: 15,
                paddingLeft: 10,
                // flex: 1,
                // flexDirection: "column",
                // alignContent: "space-between",
                // left: "5%",
                // bottom: "50%",
              }}
            >
              Search web
            </Text>
          </View>
          </View>
          {Platform.select({
            web: (
              <ChatBarInputWeb
                onMessageSend={onMessageSend}
                handleDrop={handleDrop}
              />
            ),
            default: (
              <ChatBarInputMobile
                onMessageSend={onMessageSend}
              />
            )

          })}
          
          
          {PlatformIsWeb && (
            <Text style={{
                // fontFamily: "YingHei",
                color: "#4D4D56",
                fontSize: 15,
                fontStyle: "italic",
                textAlignVertical: 'center',
                // backgroundColor: '#4D4D56',
            }}>
              <i>
              Model:{" "}
                <a href="https://huggingface.co/meta-llama/Llama-2-70b-chat-hf" target="_blank">
                  meta-llama/Llama-2-70b-chat-hf
                </a>
              {" · "}Generated content may be inaccurate or false.
              </i>
            </Text>
          )}
        </View> 
            
          
      </View>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = {
  buttonTest: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 4,
    elevation: 3,
    backgroundColor: "black",
  },
  leftPanelContainer: {
    flex: 1,
    backgroundColor: "#D7AE98",
    height: "100%",
    // justifyContent: 'center',
    alignItems: "center",
    paddingVertical: 20,
  },
  chatBoxContainerCopyButton: {
    color: "white",
    flex: 1,
    paddingLeft: "95%",
    bottom: 20,
    left: 20,
  },
  uploadButton: {
    // flex: 1,
    backgroundColor: "#FF0000",
    // borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  container: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: "#23232D",
    alignItems: "center",
    justifyContent: "center",
  },
  chatBoxContainer: {
    paddingVertical: 50,
    paddingLeft: 30,
    paddingRight: 30,
    backgroundColor: "#39393C",
    borderRadius: 50,
    flex: 5,
    // width: '100%',
    // height: '500px',
  },
  chatBoxPrimary: {
    width: "100%",
    height: "100%",
    // flexGrow: 0,
    borderRadius: 50,
    backgroundColor: "#17181D",
    padding: 10,
    paddingHorizontal: 25,
    paddingVertical: 25,
  },
  chatBoxText: {
    // fontFamily: "YingHei",
    fontSize: 20,
    height: "10px",
    color: "white",
  },
  chatColumn: {
    flexDirection: "column",
    // flex: 5,
    height: "100%",
    width: "88%",
    paddingHorizontal: 0,
    paddingVertical: 24,
  },
  inputBoxContainer: {
    // height: '20%',
    width: "100%",
    flex: 1,
    flexDirection: "row",
    color: "#E8E3E3",
    backgroundColor: "#FFAAAA00",
    borderRadius: 10,
    // margin: '10px 0',
    alignItems: "center",
    justifyContent: "space-between",
    // paddingRight: 24,
    paddingVertical: 2,
    paddingHorizontal: 0,
    // padding: 10,
  },
  inputBoxTextInput: {
    // fontFamily: "YingHei",
    fontSize: 15,
    height: "100%",
    flex: 8,
    backgroundColor: "#D7AE98",
    borderRadius: 10,
    padding: 10,
    color: "white",
  },
  inputBoxSendRequest: {
    flex: 1,
    width: "100%",
    bottom: "45%",
    flexDirection: "row",
    height: "50%",
    backgroundColor: "#17181D",
    borderRadius: 15,
    alignItems: "center",
    justifyContent: "center",
    padding: 10,
  },
  inputBoxSendContainer: {
    flex: 1,
    backgroundColor: "#23232D",
    paddingLeft: 20,
    height: "50%",
    width: "100%",
    justifyContent: "center",
  },
  switchButton: {
    flexDirection: "column",
    paddingVertical: 15,
    alignItems: "left",
    justifyContent: "center",
  },
};
