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

// type pageID = "ChatWindow" | "MarkdownTestPage" | "LoginPage";

type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships?: object[],
  is_admin?: boolean,
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
  const [retrievedUserMemberships, setRetrievedUserMemberships] = useState([]);
  const [membershipCallMade, setMembershipCallMade] = useState(false);
  const [userIsAdmin, setUserIsAdmin] = useState(false);
  const [availableModels, setAvailableModels] = useState({})

  // const set_user_data = (username : string, password_prehash : string, memberships : object[], is_admin : boolean) => {
  //   const url = craftUrl("http://localhost:5000/api/login", {
  //     "username": username,
  //     "password_prehash": password_prehash,
  //   });
  // };

  useEffect(() => {
    if (retrievedUserData === null) { 
      return; 
    } else if (!membershipCallMade) { 
      getUserMemberships(retrievedUserData["username"], retrievedUserData["password_pre_hash"], "all", setRetrievedUserMemberships, setUserIsAdmin);
      setMembershipCallMade(true);
    } else {
      getAvailableModels(retrievedUserData, (result : object) => {
        props.setUserData({...{
          username: retrievedUserData["username"],
          password_pre_hash: retrievedUserData["password_pre_hash"],
          memberships: retrievedUserMemberships,
          is_admin: userIsAdmin
        }, ...{available_models : result}});
        if (props.setPageNavigate) {
          props.setPageNavigate("ChatWindow");
        }
      })
    }
    
  }, [retrievedUserData, membershipCallMade]);

  const login = () => {
    // fetch('http://localhost:5000/api/help', {method: "POST"}).then((response) => {
    //   response.json().then((data) => { console.log(data)})});
    const url = craftUrl("http://localhost:5000/api/login", {
      "username": usernameText,
      "password": password
    });
    let result = {};
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          result = data;
          console.log(result);
          try {
            if (result["successful"]) {
              // setErrorMessage("Login Successful");
              setRetrievedUserData({
                username: usernameText, 
                password_pre_hash: result["password_single_hash"]
              });

              console.log({
                username: usernameText, 
                password_pre_hash: result["password_single_hash"]
              });
            } else {
              setErrorMessage(result["note"]);
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
          result = data;
          console.log(result);
          try {
            if (result["account_made"]) {
              // setErrorMessage("Signup Successful");
              props.setUserData({username: usernameText, password_pre_hash: result["password_single_hash"]});
              if (props.setPageNavigate) {
                props.setPageNavigate("ChatWindow");
              }
              //Sign-up Successful
            } else {
              setErrorMessage(result["note"]);
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
