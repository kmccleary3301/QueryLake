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
import ChatBubble from "../components/ChatBubble";
import { DrawerActions } from "@react-navigation/native";
// import MarkdownRender from "../components/MarkdownTestComponent";

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

type ChatWindowProps = {
  navigation?: any,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
}


export default function ChatWindow(props : ChatWindowProps) {


  // props.navigation.navigate("HomeScreen")
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

  // const AnimatedTextInput = Animated.createAnimatedComponent(TextInput);

  const PlatformIsWeb = Platform.select({web: true, default: false});


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
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [inputLineCount]);

  const translateSidebarButton = useRef(new Animated.Value(0)).current;
  const opacitySidebarButton = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    console.log("Change detected in sidebar:", props.sidebarOpened);
    Animated.timing(translateSidebarButton, {
      toValue: props.sidebarOpened?-320:0,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
    setTimeout(() => {
      Animated.timing(opacitySidebarButton, {
        toValue: props.sidebarOpened?0:1,
        // toValue: opened?Math.min(300,(children.length*50+60)):50,
        duration: props.sidebarOpened?50:300,
        easing: Easing.elastic(0),
        useNativeDriver: false,
      }).start();
    }, props.sidebarOpened?0:300);
  }, [props.sidebarOpened]);

  return (
    <View style={{
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <View style={{flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <View id="ChatHeader" style={{
          width: "100%",
          height: 40,
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
          <Animated.View style={{
            paddingLeft: 10,
            transform: [{ translateX: translateSidebarButton,},],
            elevation: -1,
            zIndex: -1,
            opacity: opacitySidebarButton,
          }}>
            {props.sidebarOpened?(
              <Feather name="sidebar" size={24} color="#E8E3E3" />
            ):(
              <Pressable style={{padding: 0}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </Pressable> 
            )}
          </Animated.View>
          {/* Decide what to put here */}
        </View>
        <View style={{
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          width: "88%",
          paddingHorizontal: 0,
          // paddingVertical: 24,
        }}>
          <ScrollView 
            ref={scrollViewRef}
            onContentSizeChange={() => scrollViewRef.current.scrollToEnd({ animated: true })}
            style={{
              flex: 5,
            }}
          >
            {newChat.map((v_2 : ChatEntry, k_2 : number) => (
              <ChatBubble key={k_2} entry={v_2}/>
            ))}
            {temporaryBotEntry && (
              <ChatBubble entry={temporaryBotEntry}/>
            )}
          </ScrollView>

          

          <View id="InputBox" style={{
            flexDirection: 'column',
            justifyContent: 'space-around',
            // flex: 1,
            // height: 200,
            width: '100%',
            paddingVertical: 10,
          }}>
            <View style={{paddingBottom: 5, paddingLeft: 12, flexDirection: "row"}}>
              <View id="Switch" style={{
                // width: 200,
                // width: 140,
                height: 28,
                borderRadius: 14,
                // backgroundColor: '#4D4D56',
                borderWidth: 1,
                borderColor: '#4D4D56',
                flexDirection: 'row',
                justifyContent: 'center',
                alignItems: 'center',
              }}>
                <View style={{paddingLeft: 10}}>
                  <Switch
                    trackColor={{ false: "#4D4D56", true: "#7968D9" }}
                    // thumbColor={isEnabled ? "#D9D9D9" : "#D9D9D9"}
                    thumbColor={"#D9D9D9"}
                    
                    
                    onValueChange={toggleSwitch}
                    value={isEnabled}
                  />
                </View>
                <Text
                  style={{
                    fontFamily: 'Inter-Regular',
                    color: "#4D4D56",
                    fontSize: 12,
                    paddingLeft: 10,
                    paddingRight: 10,
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
              <View style={{flex: 1}}>

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
                  fontFamily: "Inter-Regular",
                  color: "#4D4D56",
                  fontSize: 12,
                  fontStyle: "italic",
                  textAlignVertical: 'center',
                  paddingLeft: 12,
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
      </View>
      <StatusBar style="auto" />
    </View>
  );
}

const MARKDOWN_TEST_MESSAGE = `
# Heading level 1

This is the first paragraph.

This is the second paragraph.

This is the third paragraph.

## Heading level 2

This is an [anchor](https://github.com).

### Heading level 3

This is **bold** and _italics_.

#### Heading level 4

This is \`inline\` code.

This is a code block:

\`\`\`tsx
const Message = () => {
  return <div>hi</div>;
};
\`\`\`

##### Heading level 5

This is an unordered list:

- One
- Two
- Three, and **bold**

This is an ordered list:

1. One
1. Two
1. Three

This is a complex list:

1. **Bold**: One
    - One
    - Two
    - Three
  
2. **Bold**: Three
    - One
    - Two
    - Three
  
3. **Bold**: Four
    - One
    - Two
    - Three

###### Heading level 6

> This is a blockquote.

This is a table:

| Vegetable | Description |
|-----------|-------------|
| Carrot    | A crunchy, orange root vegetable that is rich in vitamins and minerals. It is commonly used in soups, salads, and as a snack. |
| Broccoli  | A green vegetable with tightly packed florets that is high in fiber, vitamins, and antioxidants. It can be steamed, boiled, stir-fried, or roasted. |
| Spinach   | A leafy green vegetable that is dense in nutrients like iron, calcium, and vitamins. It can be eaten raw in salads or cooked in various dishes. |
| Bell Pepper | A colorful, sweet vegetable available in different colors such as red, yellow, and green. It is often used in stir-fries, salads, or stuffed recipes. |
| Tomato    | A juicy fruit often used as a vegetable in culinary preparations. It comes in various shapes, sizes, and colors and is used in salads, sauces, and sandwiches. |
| Cucumber   | A cool and refreshing vegetable with a high water content. It is commonly used in salads, sandwiches, or as a crunchy snack. |
| Zucchini | A summer squash with a mild flavor and tender texture. It can be sautéed, grilled, roasted, or used in baking recipes. |
| Cauliflower | A versatile vegetable that can be roasted, steamed, mashed, or used to make gluten-free alternatives like cauliflower rice or pizza crust. |
| Green Beans | Long, slender pods that are low in calories and rich in vitamins. They can be steamed, stir-fried, or used in casseroles and salads. |
| Potato | A starchy vegetable available in various varieties. It can be boiled, baked, mashed, or used in soups, fries, and many other dishes. |

This is a mermaid diagram:

\`\`\`mermaid
gitGraph
    commit
    commit
    branch develop
    checkout develop
    commit
    commit
    checkout main
    merge develop
    commit
    commit
\`\`\`

\`\`\`latex
\\[F(x) = \\int_{a}^{b} f(x) \\, dx\\]
\`\`\`
`;
