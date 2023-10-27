import { useState, useRef, useEffect } from "react";
// import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  TextInput,
  Animated,
  Easing,
  Linking
} from "react-native";
import AnimatedPressable from "../components/AnimatedPressable";
import { Feather } from "@expo/vector-icons";
import { Dropdown } from "react-native-element-dropdown";
import { ScrollView } from "react-native-gesture-handler";
import HoverDocumentEntry from "../components/HoverDocumentEntry";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";
import craftUrl from "../hooks/craftUrl";

type documentRetrieved = {
  title: string,
  hash_id: string,
  uploaded: boolean,
  uploadFile?: any,
}

type pageID = "ChatWindow" | "MarkdownTestPage" | "LoginPage";

type userDataType = {
  username: string,
  password_pre_hash: string,
};

type EditCollectionProps = {
  setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  userData: userDataType,
  pageNavigateArguments: string,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  setRefreshSidePanel: React.Dispatch<React.SetStateAction<string[]>>
}

export default function EditCollection(props : EditCollectionProps) {
  const [collectionIsPublic, setCollectionIsPublic] = useState({label: "Private", value: false});
  const [collectionOwner, setCollectionOwner] = useState("Personal");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [fileDragHover, setFileDragHover] = useState(false);  
  const [uploadFiles, setUploadFiles] = useState<documentRetrieved[]>([]);
  const [fileNames, setFileNames] = useState([]);
  const [collectionType, setCollectionType] = useState("user");
  const [nonUploadedFileCount, setNonUploadedFileCount] = useState(0);
  const [documentsToDelete, setDocumentsToDelete] = useState<string[]>([]);

  const hoverOpacity = useRef(new Animated.Value(1)).current;
  const [hashId, setHashId] = useState("");

  let finished_uploads = 0;

  const [finishedUploads, setFinishedUploads] = useState(0);
  const [currentUploadProgress, setCurrentUploadProgress] = useState(0);
  const [publishStarted, setPublishStarted] = useState(false);
  
  
  const visibility_selections = [
    {label: "Private", value: false},
    {label: "Public", value: true},
  ];


  useEffect(() => {
    if (props.pageNavigateArguments.length == 0) { return; }
    const nav_args = props.pageNavigateArguments.split("-");
    if (nav_args[0] !== "collection") { return; }
    setCollectionType(nav_args[1]);
    setHashId(nav_args[2]);
    const url = craftUrl("http://localhost:5000/api/fetch_collection", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "collection_type": nav_args[1],
      "collection_hash_id": nav_args[2]
    });

    fetch(url, {method: "POST"}).then((response) => {
      // console.log(response);
      response.json().then((data) => {
        console.log(data);
        if (data["success"] == false) {
          console.error("Collection error:", data["note"]);
          return;
        }
        setName(data.result.title);
        setDescription(data.result.description);
        setCollectionOwner(data.result.owner);
        setCollectionIsPublic(data.result.public?visibility_selections[1]:visibility_selections[0]);
        let documents : documentRetrieved[] = [];
        try {
          for (let i = 0; i < data.result.document_list.length; i++) {
            documents.push({
              title: data.result.document_list[i].title,
              hash_id: data.result.document_list[i].hash_id,
              uploaded: true,
            })
          }
          setUploadFiles(documents);
        } catch {}
      });
    });

  }, [props.pageNavigateArguments]);

  const owner_selections = [
    {label: "Personal", value: "Personal"},
  ];

  useEffect(() => {
    Animated.timing(hoverOpacity, {
      toValue: fileDragHover?0.7:1,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 150,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [fileDragHover]);

  const handleDragOver = (event: any) => {
    setFileDragHover(true);
    event.preventDefault();
  };

  const handleDragEnd = (event: any) => {
    setFileDragHover(false);
    event.preventDefault();
  };

  const handleDrop = (event: any) => {
    let new_files_push : documentRetrieved[] = [];
    for (let i = 0; i < event.dataTransfer.files.length; i++) {
      new_files_push.push({
        "title": event.dataTransfer.files[i].name,
        "hash_id": "",
        uploaded: false,
        uploadFile: event.dataTransfer.files[i]
      })
    }
    let new_files = [...uploadFiles, ...new_files_push];
    setUploadFiles(new_files)
  };

  const start_save = () => {
    const url = craftUrl("http://localhost:5000/api/modify_document_collection", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "title": name,
      "description": description,
      "collection_hash_id": hashId
    });
    let collection_id = -1;

    for (let i = 0; i < documentsToDelete.length; i++) {
      const url_delete_document = craftUrl("http://localhost:5000/api/delete_document", {
        "username": props.userData.username,
        "password_prehash": props.userData.password_pre_hash,
        "hash_id": documentsToDelete[i],
      });
      fetch(url_delete_document, {method: "POST"});
    }

    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        if (data["success"] == false) {
          console.error("Collection Publish Failed", data["note"]);
          return;
        }
        collection_id = data["collection_id"];
      });
    });
    // If organization specified, set that to author.
    let url_2 = craftUrl("http://localhost:5000/api/async/upload_document", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "collection_hash_id": hashId,
      "collection_type": collectionType
    });

    const uploader = createUploader({
      destination: {
        method: "POST",
        url: url_2,
        filesParamName: "file",
      },
      autoUpload: true,
    });

    uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
      console.log(`item ${item.id} started uploading`);
      setFinishedUploads(finishedUploads => finishedUploads+1);
      setCurrentUploadProgress(0);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
      console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
      setCurrentUploadProgress(item.completed);
    });

    uploader.on(UPLOADER_EVENTS.ITEM_FINISH, (item) => {
      console.log(`item ${item.id} response:`, item.uploadResponse);
      finished_uploads += 1;
      if (finished_uploads >= upload_count) {
        props.setRefreshSidePanel(["collections"]);
        if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
        if (props.navigation) { props.navigation.navigate("ChatWindow"); }
      }
    });
    1
    // let formData = new FormData();
    let upload_count = 0;
    for (let i = 0; i < uploadFiles.length; i++) {
      // formData.append("file", event.dataTransfer.files[i]);
      if (!uploadFiles[i].uploaded) {
        uploader.add(uploadFiles[i].uploadFile);
        upload_count += 1;
      }
    }
    if (upload_count == 0) {
      props.setRefreshSidePanel(["collections"]);
      if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
      if (props.navigation) { props.navigation.navigate("ChatWindow"); }
    }
    setNonUploadedFileCount(upload_count);
    setPublishStarted(true);
  };

  const deleteDocumentFromServer = (hash_id : string) => {
    const url = craftUrl("http://localhost:5000/api/delete_document", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "hash_id": hash_id
    });

    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
        if (data["success"] == false) {
          console.error("Document Delete Failed", data["note"]);
          return;
        }
        // setUploadFiles([...uploadFiles.slice(0, upload_file_index), ...uploadFiles.slice(upload_file_index+1, uploadFiles.length)]);
      });
    });
  };

  const openDocument = (hash_id : string) => {
    const url = craftUrl("http://localhost:5000/api/async/fetch_document", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "hash_id": hash_id
    });
    Linking.openURL(url.toString());
  }

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
              <AnimatedPressable style={{padding: 0}} onPress={() => {if (props.toggleSideBar) { props.toggleSideBar(); }}}>
                <Feather name="sidebar" size={24} color="#E8E3E3" />
              </AnimatedPressable> 
            )}
          </Animated.View>
          {/* Decide what to put here */}
        </View>
        <View style={{
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          alignSelf: 'center',
          alignContent: 'center',
          flex: 1,
          // height: '100%'
        }}>
          
          <View id={"CollectionBox"} style={{
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              borderRadius: 30,
              // height: 400,
              // width: 400,
              backgroundColor: '#39393C',
              padding: 15,
          }}>
            <View style={{flexDirection: "row"}}>
              <View style={{flexDirection: "column"}}>
                <Text style={{
                  fontFamily: 'Inter-Regular',
                  fontSize: 20,
                  paddingBottom: 5,
                  paddingTop: 5,
                  width: '30vw',
                  color: '#E8E3E3',
                  textAlign: 'center'
                }}>
                  {"Edit Document Collection"}
                </Text>
                <View style={{
                  backgroundColor: '#E8E3E3',
                  height: 2,
                  paddingTop: 2,
                  borderRadius: 1,
                  width: '100%'
                }}/>
                <View style={{
                  flexDirection: 'row',
                  justifyContent: 'space-between'
                }}>
                  <Dropdown
                    placeholderStyle={{
                      backgroundColor: 'none',
                      borderWidth: 0,
                      elevation: 0,
                      shadowOpacity: 0,
                      color: '#E8E3E3'
                    }}
                    selectedTextStyle={{
                      fontSize: 14,
                      backgroundColor: 'none',
                      color: '#E8E3E3'
                    }}
                    itemContainerStyle={{
                      flexShrink: 1,
                      backgroundColor: 'none',
                      borderWidth: 0,
                      elevation: 0,
                      shadowOpacity: 0,
                      alignItems: 'center'
                    }}
                    itemTextStyle={{
                      backgroundColor: 'none',
                      borderWidth: 0,
                      elevation: 0,
                      shadowOpacity: 0
                    }}
                    selectedStyle={{
                      backgroundColor: 'none',
                      borderWidth: 0,
                      elevation: 0,
                      shadowOpacity: 0
                    }}
                    containerStyle={{
                      // backgroundColor: 'none',
                      // borderWidth: 0,
                      // elevation: 0,
                      // shadowOpacity: 0
                    }}
                    iconStyle={{
                      width: 20,
                      height: 20,
                    }}
                    maxHeight={300}
                    labelField="label"
                    valueField="value"
                    // placeholder={!isFocus ? 'Select item' : '...'}
                    value={collectionIsPublic}
                    // onFocus={() => setIsFocus(true)}
                    // onBlur={() => setIsFocus(false)}
                    onChange={item => {
                      setCollectionIsPublic(item);
                      // setIsFocus(false);
                    }}
                    data={visibility_selections}
                    style={{
                      margin: 16,
                      // height: 50,
                      width: 80,
                      backgroundColor: 'none',
                      // borderRadius: 12,
                      // padding: 12,
                      // shadowOpacity: 0.2,
                      // shadowRadius: 1.41,
                
                      // elevation: 2,
                    }}
                    placeholder={"Hello"}
                  />
                  <View style={{flexDirection: 'row'}}>
                    <Text style={{
                      fontSize: 14,
                      fontFamily: 'Inter-Regular',
                      paddingRight: 2,
                      color: '#E8E3E3',
                      alignSelf: 'center',
                    }}>{"Owner"}</Text>
                    <Text style={{
                      fontSize: 14,
                      fontFamily: 'Inter-Regular',
                      paddingRight: 2,
                      color: '#E8E3E3',
                      alignSelf: 'center',
                    }}>
                      {collectionOwner}
                    </Text>
                  </View>
                </View>
                <View style={{paddingBottom: 10}}>
                  <TextInput
                    editable
                    numberOfLines={1}
                    placeholder="Name"
                    placeholderTextColor={"#4D4D56"}
                    value={name}
                    onChangeText={(text) => {
                      setName(text);
                    }}
                    style={{
                      color: '#E8E3E3',
                      fontSize: 16,
                      textAlignVertical: 'center',
                      fontFamily: 'Inter-Regular',
                      backgroundColor: "#17181D",
                      borderRadius: 15,
                      padding: 10
                    }}
                  />
                </View>
                <View style={{paddingBottom: 10}}>
                  <TextInput
                    editable
                    multiline
                    numberOfLines={5}
                    placeholder="Description"
                    placeholderTextColor={"#4D4D56"}
                    value={description}
                    onChangeText={(text) => {
                      setDescription(text);
                    }}
                    style={{
                      color: '#E8E3E3',
                      fontSize: 16,
                      textAlignVertical: 'center',
                      fontFamily: 'Inter-Regular',
                      backgroundColor: "#17181D",
                      borderRadius: 15,
                      padding: 10
                    }}
                  />
                </View>
              </View>
              <ScrollView style={{
                // height: "100%",
                width: 300,
                padding: 10,
                height: 280,
              }} showsVerticalScrollIndicator={false}>
                {uploadFiles.map((value : documentRetrieved, index : number) => (
                  <HoverDocumentEntry
                    key={index}
                    title={value.title}
                    deleteIndex={() => {
                      if (value.uploaded) {
                        setDocumentsToDelete([...documentsToDelete, value.hash_id]);
                        // deleteDocumentFromServer(value.hash_id, index); 
                      }
                      setUploadFiles([...uploadFiles.slice(0, index), ...uploadFiles.slice(index+1, uploadFiles.length)]);
                    }}
                    onPress={() => {
                      if (value.uploaded) { openDocument(value.hash_id); }
                    }}
                  />
                ))}
              </ScrollView>
            </View>
            <div
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
              onDrop={(e) => {
                handleDrop(e);
                handleDragEnd(e);
              }}
              onDragLeave={handleDragEnd}
              style={{width: '100%', paddingBottom: 10,}}
            >
              <Animated.View id="FileDrop" style={{
                width: '100%',
                backgroundColor: "#17181D",
                borderStyle: 'dashed',
                borderWidth: 2,
                borderColor: '#E8E3E3',
                borderRadius: 15,
                padding: 10,
                alignItems: 'center',
                justifyContent: 'center',
                opacity: hoverOpacity
              }}>
                <Feather name="file-plus" size={40} color={'#E8E3E3'}/>
              </Animated.View>
            </div>
            {(publishStarted) && (
              <View style={{flexDirection: 'row'}}>
                <Text style={{
                  fontFamily: 'Inter-Regular',
                  fontSize: 16,
                  color: '#E8E3E3'
                }}>
                  {finishedUploads.toString()+"/"+nonUploadedFileCount.toString()}
                </Text>
                <View style={{
                  flexDirection: 'column',
                  justifyContent: 'center',
                }}>
                  <View style={{
                    width: 100,
                    height: 4,
                    borderRadius: 2,
                    backgroundColor: '#17181D'
                  }}>
                    <View style={{
                      width: currentUploadProgress,
                      backgroundColor: '#7968D9',
                      height: 4,
                      borderRadius: 2
                    }}/>
                  </View>
                </View>
              </View>
            )}
            {(!publishStarted) && (

              <AnimatedPressable style={{
                width: '100%',
                borderRadius: 10,
                backgroundColor: '#7968D9',
                alignItems: 'center',
                justifyContent: 'center'
              }} onPress={start_save}>
                <View style={{width: '100%'}}>
                <Text style={{
                  fontFamily: 'Inter-Regular',
                  fontSize: 24,
                  color: '#E8E3E3',
                  alignSelf: 'center',
                  padding: 10,
                  width: '100%',
                }}>
                  {"Save Changes"}
                </Text>
                </View>
              </AnimatedPressable>
            )}
          </View>
        </View>
      </View>
    </View>
  );
}
