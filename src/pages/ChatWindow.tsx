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
} from "react-native";
import Clipboard from "@react-native-clipboard/clipboard";
import { Feather } from "@expo/vector-icons";
import { ScrollView, Switch } from "react-native-gesture-handler";
// import Uploady, { useItemProgressListener } from '@rpldy/uploady';
// import UploadButton from "@rpldy/upload-button";
import EventSource from "../react-native-server-sent-events";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import Icon from "react-native-vector-icons/FontAwesome";

export default function ChatWindow({ navigation }) {
  const scrollViewRef = useRef();
  const inputTwo = useRef("");
  const [inputText, setInputText] = useState(
    "Write a python function that calculates the Fibonacci sequence up to a given number n. Include type hints and a function description."
  );
  const [isEnabled, setIsEnabled] = useState(false);
  const [chat, setChat] = useState(
    "Sure! Here's a Python function that calculates the Fibonacci sequence up to a given number n:"
  );
  const [sseOpened, setSseOpened] = useState(false);
  const [fileDragHover, setFileDragHover] = useState(false);
  const [filesPrepared, setFilesPrepared] = useState<File[]>([]);
  const [filesProgress, setFilesProgress] = useState<Number[]>([]);
  const [submitInput, setSubmitInput] = useState(false);

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

  const sse_fetch = async function () {
    if (sseOpened === true) {
      return;
    }
    console.log("Starting SSE");

    const url = new URL("http://localhost:5000/chat");
    url.searchParams.append("query", inputText);

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
        es.close();
      } else {
        // for (let key in Object.keys(uri_decode_map)) {
        //   decoded = decoded.replace(key, uri_decode_map[key]);
        // }
        decoded = decodeURI(decoded);
        console.log([decoded]);
        genString += decoded;
      }

      setChat(genString);
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

  const handleDragOver = (event: any) => {
    setFileDragHover(true);
    event.preventDefault();
    console.log("Hello");
  };

  const handleDragEnd = (event: any) => {
    setFileDragHover(false);
    event.preventDefault();
    console.log("Goodbye");
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

  const log_key_press = (e: {
    nativeEvent: { key: string; shiftKey: boolean };
  }) => {
    if (e.nativeEvent.key === "Enter" && e.nativeEvent.shiftKey === false) {
      setSubmitInput(true);
    }
  };

  useEffect(() => {
    if (submitInput && inputText !== "") {
      setSubmitInput(false);
      setInputText("");
    }
  }, [inputText]);

  return (
    <View style={styles.container}>
      <View style={styles.chatColumn}>
        <Text
          style={{
            color: "#E8E3E3",
            fontSize: 20,
            fontFamily: "YingHei",
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
              fontFamily: "YingHei",
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
            }
          >
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

        <View style={styles.switchButton}>
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
              flex: 1,
              flexDirection: "column",
              alignContent: "space-between",
              left: "5%",
              bottom: "50%",
            }}
          >
            Search web
          </Text>
        </View>

        <View style={styles.inputBoxContainer}>
          <div
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
            onDrop={handleDrop}
            onDragLeave={handleDragEnd}
            style={{
              flex: 8,
              padding: 0,
              height: "100%",
            }}
          >
            <TextInput
              // ref={input => { this.textInput = inputTwo }}
              editable
              multiline
              numberOfLines={4}
              placeholder="Ask Anything"
              placeholderTextColor={"#4D4D56"}
              value={inputText}
              onKeyPress={(e: {
                nativeEvent: { key: string; shiftKey: boolean };
              }) => {
                log_key_press(e);
              }}
              onChangeText={(text) => {
                setInputText(text);
              }}
              style={{
                fontFamily: "YingHei",
                color: "#E8E3E3",
                fontSize: 15,
                height: "60%",
                width: "100%",
                backgroundColor: fileDragHover ? "#836454" : "#17181D",
                borderRadius: 10,
                padding: 10,
                paddingVertical: 10,
              }}
            />
            <Text
              style={{
                fontFamily: "YingHei",
                color: "#4D4D56",
                fontSize: 15,
                fontStyle: "italic",
              }}
            >
              Model:{" "}
              <a
                href="https://huggingface.co/meta-llama/Llama-2-70b-chat-hf"
                target="_blank"
              >
                meta-llama/Llama-2-70b-chat-hf
              </a>
              · Generated content may be inaccurate or false.
            </Text>
          </div>

          <View style={styles.inputBoxSendContainer}>
            <Pressable onPress={sse_fetch} style={styles.inputBoxSendRequest}>
              <Text
                style={{
                  fontFamily: "YingHei",
                  fontSize: 15,
                  color: "white",
                }}
              >
                Go
              </Text>
            </Pressable>
          </View>
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
    fontFamily: "YingHei",
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
    fontFamily: "YingHei",
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
