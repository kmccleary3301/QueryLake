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
import AnimatedPressable from "../components/AnimatedPressable";
import { Feather } from "@expo/vector-icons";
import craftUrl from "../hooks/craftUrl";
import getUserMemberships from "../hooks/getUserMemberships";
import getAvailableModels from "../hooks/getAvailableModels";
import getAvailableToolchains from "../hooks/getAvailableToolchains";

// type pageID = "ChatWindow" | "MarkdownTestPage" | "LoginPage";

type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships?: object[],
  is_admin?: boolean,
  serp_key?: string,
  available_models?: {
    default_model: string,
    local_models: string[],
    external_models: object
  },
  available_toolchains: object[],
  selected_toolchain: string
};

type LoginPageProps = {
  setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
  navigation?: any,
  setUserData: React.Dispatch<React.SetStateAction<userDataType>>
}

export default function LoginPage(props : LoginPageProps) {
  const [modeIsLogin, setModeIsLogin] = useState(true); //A boolean for if you're signing up or logging in.
  const [usernameText, setUsernameText] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const [retrievedUserData, setRetrievedUserData] = useState<userDataType | null>(null);
  const [retrievedUserMemberships, setRetrievedUserMemberships] = useState<object[] | null>(null);
  const [membershipCallMade, setMembershipCallMade] = useState(false);
  const [userIsAdmin, setUserIsAdmin] = useState(false);
  const [availableModels, setAvailableModels] = useState({})

  // const set_user_data = (username : string, password_prehash : string, memberships : object[], is_admin : boolean) => {
  //   const url = craftUrl("http://localhost:5000/api/login", {
  //     "username": username,
  //     "password_prehash": password_prehash,
  //   });
  // };

  // useEffect(() => {
  //   if (retrievedUserData === null) { 
  //     return; 
  //   } else if (!membershipCallMade) { 
  //     getUserMemberships(retrievedUserData["username"], retrievedUserData["password_pre_hash"], "all", setRetrievedUserMemberships, setUserIsAdmin);
  //     setMembershipCallMade(true);
  //   } else if (retrievedUserMemberships !== null) {
  //     getAvailableModels(retrievedUserData, (result : object) => {
  //       getAvailableToolchains(retrievedUserData, (result_tools : object) => {
  //         console.log("Got toolchains:", result_tools);

  //         props.setUserData({...{
  //           username: retrievedUserData["username"],
  //           password_pre_hash: retrievedUserData["password_pre_hash"],
  //           memberships: retrievedUserMemberships,
  //           is_admin: userIsAdmin,
  //           available_toolchains: result_tools.result.toolchains,
  //           selected_toolchain: result_tools.result.default
  //         }, ...{available_models : result}});
  //         if (props.setPageNavigate) {
  //           props.setPageNavigate("ChatWindow");
  //         }
  //       })
  //     })
  //   }
    
  // }, [retrievedUserData, membershipCallMade, retrievedUserMemberships]);

  const login = () => {
    // fetch('http://localhost:5000/api/help', {method: "POST"}).then((response) => {
      //   response.json().then((data) => { console.log(data)})});
    const url = craftUrl("http://localhost:5000/api/login", {
      "username": usernameText,
      "password": password
    });
    // let result = {};
    console.log("Calling Server");
    fetch(url, {method: "POST"}).then((response) => {
      console.log("Fetching");
      console.log(response);
      response.json().then((data) => {
          // result = data;
          console.log(data);
          try {
            if (data.success) {
              // setErrorMessage("Login Successful");
              // const retrieved_user_data = {
              //   username: usernameText, 
              //   password_pre_hash: data.result.password_single_hash,
              //   aval
              // };
              // getUserMemberships(usernameText, data.result.password_single_hash, "all", (memberships) => {
              //   props.setUserData({
              //     username: usernameText, 
              //     password_pre_hash: data.result.password_single_hash,
              //     available_toolchains: data.result.available_toolchains,
              //     selected_toolchain: data.result.default_toolchain,
              //     available_models: data.result.available_models,
              //     is_admin: data.result.admin,
              //     memberships: memberships
              //   });
  
              //   if (props.setPageNavigate) {
              //     props.setPageNavigate("ChatWindow");
              //   }
              // }, setUserIsAdmin);
              getUserMemberships(usernameText, data.result.password_single_hash, "all", (memberships) => {
                getAvailableToolchains({username: usernameText, password_pre_hash: data.result.password_single_hash}, (result_tools : object) => {
                  props.setUserData({
                    username: usernameText, 
                    password_pre_hash: data.result.password_single_hash,
                    available_toolchains: result_tools.toolchains,
                    selected_toolchain: result_tools.default,
                    available_models: data.result.available_models,
                    is_admin: data.result.admin,
                    memberships: memberships
                  });
    
                  if (props.setPageNavigate) {
                    props.setPageNavigate("ChatWindow");
                  }
                });
              }, setUserIsAdmin);
              
              console.log({
                username: usernameText, 
                password_pre_hash: data.result.password_single_hash
              });
            } else {
              setErrorMessage(data.note);
            }
          } catch (error) {
            console.log(error);
            setErrorMessage("Client Error");
          }
          return;
      });
    });
    
  };

  const signup = () => {
    const url = craftUrl("http://localhost:5000/api/add_user", {
      "username": usernameText,
      "password": password
    });
    let result = {};
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          console.log(data);
          try {
            if (data.success && data.result.account_made) {
              // setErrorMessage("Signup Successful");
              // props.setUserData({
              //   username: usernameText, 
              //   password_pre_hash: data.result.password_single_hash,
              //   is_admin: false,
              //   memberships: [],
              // });
              // if (props.setPageNavigate) {
              //   props.setPageNavigate("ChatWindow");
              // }
              getUserMemberships(usernameText, data.result.password_single_hash, "all", (memberships) => {
                getAvailableToolchains({username: usernameText, password_pre_hash: data.result.password_single_hash}, (result_tools : object) => {
                  
                  console.log("Result_tools:", result_tools);
                  props.setUserData({
                    username: usernameText, 
                    password_pre_hash: data.result.password_single_hash,
                    available_toolchains: result_tools.toolchains,
                    selected_toolchain: result_tools.default,
                    available_models: data.result.available_models,
                    is_admin: data.result.admin,
                    memberships: memberships
                  });
    
                  if (props.setPageNavigate) {
                    props.setPageNavigate("ChatWindow");
                  }
                });
              }, setUserIsAdmin);

              //Sign-up Successful
            } else {
              setErrorMessage(data.note);
            }
          } catch (error) {
            console.log(error);
            setErrorMessage("Client Error");
          }
          return;
      });
    });
  };

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
      <View style={{
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column'
      }}>
        <View style={{
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
            borderRadius: 15,
            // height: 400,
            backgroundColor: '#39393C',
            padding: 30,
        }}>
            <Text style={{
                fontFamily: "Inter-Regular",
                fontSize: 36,
                color: '#E8E3E3',
            }}>
                {modeIsLogin?"Sign In":"Sign Up"}
            </Text>
            <View style={{paddingTop: 10}}>
              {(errorMessage.length > 0) && (
                <View style={{
                  backgroundColor: '#FF0000',
                  borderRadius: 5,
                  padding: 10,
                }}>
                  <Text style={{
                    fontFamily: "Inter-Regular",
                    fontSize: 14,
                    color: '#E8E3E3'
                  }}>
                    {errorMessage}
                  </Text>
                </View>
              )}
            </View>
            <View style={{paddingTop: 15}}>
              <View style={{
                backgroundColor: '#17181D',
                borderRadius: 5,
              }}>
                <TextInput
                  name="email"
                  id="email"
                  autoCorrect={false}
                  secureTextEntry={false}
                  spellCheck={false}
                  editable
                  numberOfLines={1}
                  placeholder="Username"
                  placeholderTextColor={"#4D4D56"}
                  value={usernameText}
                  onChangeText={(text) => {
                    setUsernameText(text);
                  }}
                  style={Platform.select({
                    web: {
                      // height: inputBoxHeight,
                      color: '#E8E3E3',
                      fontSize: 14,
                      textAlignVertical: 'center',
                      outlineStyle: 'none',
                      fontFamily: 'Inter-Regular',
                      padding: 5,
                    },
                    default: { //The Platform specific switch is necessary because 'outlineStyle' is only on Web, and causes errors on mobile.
                      color: '#E8E3E3',
                      fontSize: 14,
                      textAlignVertical: 'center',
                      fontFamily: 'Inter-Regular',
                      padding: 5,
                        
                    }
                  })}
                />
              </View>
            </View>
            <View style={{paddingTop: 15}}>
              <View style={{
                backgroundColor: '#17181D',
                borderRadius: 5,
              }}>
                <TextInput
                  id="Password"
                  autoCorrect={false}
                  spellCheck={false}
                  editable
                  secureTextEntry={true}
                  numberOfLines={1}
                  placeholder="Password"
                  placeholderTextColor={"#4D4D56"}
                  value={password}
                  onChangeText={(text) => {
                    setPassword(text);
                  }}
                  style={Platform.select({
                    web: {
                      // height: inputBoxHeight,
                      color: '#E8E3E3',
                      fontSize: 14,
                      textAlignVertical: 'center',
                      outlineStyle: 'none',
                      fontFamily: 'Inter-Regular',
                      padding: 5,
                    },
                    default: { //The Platform specific switch is necessary because 'outlineStyle' is only on Web, and causes errors on mobile.
                      color: '#E8E3E3',
                      fontSize: 14,
                      textAlignVertical: 'center',
                      fontFamily: 'Inter-Regular',
                      padding: 5,
                    }
                  })}
                />
              </View>
            </View>
            <AnimatedPressable style={{paddingTop: 10}} onPress={() => {
              if (modeIsLogin) {
                login();
              } else {
                signup();
              }
            }}>
              <View style={{
                paddingHorizontal: 20,
                paddingVertical: 10,
                borderRadius: 10,
                backgroundColor: '#7968D9'
              }}>
              <Text style={{
                fontFamily: "Inter-Regular",
                fontSize: 20,
                color: '#E8E3E3',
              }}>
                {modeIsLogin?"Login":"Create Account"}
              </Text>
              </View>
            </AnimatedPressable>
            <AnimatedPressable style={{paddingTop: 10}} onPress={() => {
              setModeIsLogin(modeIsLogin => !modeIsLogin);
            }}>
              <Text style={{
                fontFamily: "Inter-Regular",
                fontSize: 14,
                color: '#E8E3E3'
              }}>
                {modeIsLogin?"Sign Up":"Log In"}
              </Text>
            </AnimatedPressable>
        </View>
      </View>
    </View>
  );
}
