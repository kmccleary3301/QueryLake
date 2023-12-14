import { useState, useRef, useEffect } from "react";
import { useFonts } from "expo-font";
import {
  Text,
  TextInput,
  View,
  Animated,
  Easing,
  Platform,
  Linking
} from "react-native";
import AnimatedPressable from "../components/AnimatedPressable";
import { Feather } from "@expo/vector-icons";
import craftUrl from "../hooks/craftUrl";
import ScrollViewBottomStick from "../components/ScrollViewBottomStick";
import setSerpKey from "../hooks/setSerpKey";
import searchGoogle from "../hooks/searchGoogle";
import { embedUrls } from "../hooks/searchGoogle";
import parseSearchResults from "../hooks/parseSearchResults";
import setOpenAIAPIKey from "../hooks/setOpenAIAPIKey";

type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships: object[],
  is_admin: boolean,
  serp_key?: string,
  openai_api_key?: string
};

type UserSettingsProps = {
  userData: userDataType,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  setUserData: React.Dispatch<React.SetStateAction<userDataType>>
};

export default function UserSettings(props : UserSettingsProps) {
  const translateSidebarButton = useRef(new Animated.Value(0)).current;
  const opacitySidebarButton = useRef(new Animated.Value(0)).current;
  const [serpKeyInput, setSerpKeyInput] = useState((props.userData.serp_key)?props.userData.serp_key:"");
  const [openAIAPIKeyInput, setOpenAIAPIKeyInput] = useState((props.userData.openai_api_key)?props.userData.openai_api_key:"");
  const [attemptSERPResult, setAttemptSERPResult] = useState<undefined | boolean>();
  const [attemptOpenAIResult, setAttemptOpenAIResult] = useState<undefined | boolean>();


  useEffect(() => {
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

  const send_serp_key_finish = (result : boolean) => {
    if (result) {
      props.setUserData({...props.userData, ...{serp_key: serpKeyInput}})
    }
    setAttemptSERPResult(result);
  }

  const send_serp_key = () => {
    setSerpKey(serpKeyInput, props.userData, send_serp_key_finish, undefined);
  }

  const send_openai_key_finish = (result : boolean) => {
    // if (result) {
    //   props.setUserData({...props.userData, ...{serp_key: serpKeyInput}})
    // }
    // setAttemptSERPResult(result);
    setAttemptOpenAIResult(result);
  }

  const send_openai_key = () => {
    setOpenAIAPIKey(openAIAPIKeyInput, props.userData, send_openai_key_finish, undefined);
  }

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
        </View>
        <View style={{
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          // width: "88%",
          width: "60vw",
          paddingHorizontal: 0,
          alignContent: 'center'
          // paddingVertical: 24,
        }}>
          <ScrollViewBottomStick animateScroll={false} showsVerticalScrollIndicator={false}>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center'}}>
              <Text style={{
                fontFamily: 'Inter-Regular',
                fontSize: 24,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Personal SERP Key"}
              </Text>
            </View>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center', paddingVertical: 10}}>
              <Text style={{
                fontFamily: 'Inter-Regular',
                fontSize: 14,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"API Key for Google Search API. Sign up "}
                <Text style={{color: '#7968D9'}} onPress={() => {Linking.openURL("https://serpapi.com/users/sign_up")}}>{"here"}</Text>
                {", or get your API key "}
                <Text style={{color: '#7968D9'}} onPress={() => {Linking.openURL("https://serpapi.com/manage-api-key")}}>{"here"}</Text>
              </Text>
            </View>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center'}}>
              <View style={{
                flexDirection: 'row',
                backgroundColor: '#17181D',
                width: '30vw',
                height: 40,
                borderRadius: 10,
                borderWidth: 2,
                borderColor: (attemptSERPResult !== undefined)?(attemptSERPResult?"#88C285":"#E50914"):"none"
              }}>
                <View style={{flex: 1, height: '100%'}}>
                  <TextInput
                    id="Password"
                    autoCorrect={false}
                    spellCheck={false}
                    editable
                    secureTextEntry={true}
                    numberOfLines={1}
                    placeholder="SERP Key"
                    placeholderTextColor={"#4D4D56"}
                    value={serpKeyInput}
                    onChangeText={(text) => {
                      setSerpKeyInput(text);
                    }}
                    style={Platform.select({
                      web: {
                        // height: inputBoxHeight,
                        color: '#E8E3E3',
                        fontSize: 14,
                        textAlignVertical: 'center',
                        outlineStyle: 'none',
                        fontFamily: 'Inter-Regular',
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%'
                      },
                      default: { //The Platform specific switch is necessary because 'outlineStyle' is only on Web, and causes errors on mobile.
                        color: '#E8E3E3',
                        fontSize: 14,
                        textAlignVertical: 'center',
                        fontFamily: 'Inter-Regular',
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%'
                      }
                    })}
                  />
                </View>
                <View id="PressablePadView" style={{
                  paddingLeft: 10,
                  paddingRight: 10,
                  alignSelf: 'center',
                }}>
                  <AnimatedPressable 
                    id="SendButton"
                    onPress={() => {
                      send_serp_key();
                    }}
                    style={{
                    // padding: 10,
                    height: 24,
                    width: 24,
                    backgroundColor: "#7968D9",
                    borderRadius: 12,
                    alignItems: 'center',
                    justifyContent: 'center'
                    }}
                  >
                    <Feather name="send" size={15} color="#000000" />
                  </AnimatedPressable>
                </View>
              </View>
            </View>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center', paddingTop: 20}}>
              <Text style={{
                fontFamily: 'Inter-Regular',
                fontSize: 24,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Personal OpenAI API Key"}
              </Text>
            </View>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center', paddingVertical: 10}}>
              <Text style={{
                fontFamily: 'Inter-Regular',
                fontSize: 14,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Use an OpenAI API key to use proprietary models with QueryLake"}
              </Text>
            </View>
            <View style={{width: '100%', flexDirection: 'row', justifyContent: 'center'}}>
              <View style={{
                flexDirection: 'row',
                backgroundColor: '#17181D',
                width: '30vw',
                height: 40,
                borderRadius: 10,
                borderWidth: 2,
                borderColor: (attemptOpenAIResult !== undefined)?(attemptOpenAIResult?"#88C285":"#E50914"):"none"
              }}>
                <View style={{flex: 1, height: '100%'}}>
                  <TextInput
                    id="openai_key"
                    autoCorrect={false}
                    spellCheck={false}
                    editable
                    secureTextEntry={true}
                    numberOfLines={1}
                    placeholder="OpenAI API Key"
                    placeholderTextColor={"#4D4D56"}
                    value={openAIAPIKeyInput}
                    onChangeText={(text) => {
                      setOpenAIAPIKeyInput(text);
                    }}
                    style={Platform.select({
                      web: {
                        // height: inputBoxHeight,
                        color: '#E8E3E3',
                        fontSize: 14,
                        textAlignVertical: 'center',
                        outlineStyle: 'none',
                        fontFamily: 'Inter-Regular',
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%'
                      },
                      default: { //The Platform specific switch is necessary because 'outlineStyle' is only on Web, and causes errors on mobile.
                        color: '#E8E3E3',
                        fontSize: 14,
                        textAlignVertical: 'center',
                        fontFamily: 'Inter-Regular',
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%'
                      }
                    })}
                  />
                </View>
                <View id="PressablePadView" style={{
                  paddingLeft: 10,
                  paddingRight: 10,
                  alignSelf: 'center',
                }}>
                  <AnimatedPressable 
                    id="SendButton"
                    onPress={() => {
                      // send_serp_key();
                      send_openai_key();
                    }}
                    style={{
                    // padding: 10,
                    height: 24,
                    width: 24,
                    backgroundColor: "#7968D9",
                    borderRadius: 12,
                    alignItems: 'center',
                    justifyContent: 'center'
                    }}
                  >
                    <Feather name="send" size={15} color="#000000" />
                  </AnimatedPressable>
                </View>
              </View>
            </View>
            {/* <AnimatedPressable 
              id="SendButton"
              onPress={() => {
                searchGoogle("chain of density prompting", props.userData, undefined, (result) => {
                  console.log("Google results");
                  console.log(result);
                });

                // parseSearchResults(props.userData, ["https://www.freecodecamp.org/news/python-map-explained-with-examples/", "https://www.statsmodels.org/devel/generated/statsmodels.nonparametric.kernel_regression.KernelReg.html"])
                // send_serp_key();
              }}
              style={{
              // padding: 10,
              height: 24,
              width: 24,
              backgroundColor: "#7968D9",
              borderRadius: 12,
              alignItems: 'center',
              justifyContent: 'center'
              }}
            >
              <Feather name="send" size={15} color="#000000" />
            </AnimatedPressable>
            <AnimatedPressable
              onPress={() => {
                embedUrls(['https://arxiv.org/abs/2309.04269', 'https://medium.com/aimonks/chain-of-density-the-latest-prompting-technique-on-the-block-183fe87fa9a6', 'https://www.ssw.com.au/rules/chain-of-density/', 'https://www.forbes.com/sites/lanceeliot/2023/09/20/prompt-engineering-new-chain-of-density-technique-prompts-generative-ai-toward-smartly-jampacking-crucial-content/', 'https://the-decoder.com/chain-of-density-prompt-improves-ai-summaries-by-packing-more-info-into-fewer-words/', 'https://www.reddit.com/r/ChatGPT/comments/16l403w/chain_of_density_cod_a_new_prompt_by_mit_and/', 'https://www.linkedin.com/pulse/art-science-summarization-unpacking-chain-density-rajaratnam', 'https://advanced-stack.com/resources/how-to-summarize-using-chain-of-density-prompting.html', 'https://www.chatgptpromptshub.com/the-power-of-the-chain-of-density-prompt-a-comprehensive-guide'], props.userData, (result) => {
                  console.log("embed results");
                  console.log(result);
                });
                
                // parseSearchResults(props.userData, ["https://www.freecodecamp.org/news/python-map-explained-with-examples/", "https://www.statsmodels.org/devel/generated/statsmodels.nonparametric.kernel_regression.KernelReg.html"])
                // send_serp_key();
              }}
              style={{
              // padding: 10,
              height: 24,
              width: 24,
              backgroundColor: "#7968D9",
              borderRadius: 12,
              alignItems: 'center',
              justifyContent: 'center'
              }}
            >
              <Feather name="send" size={15} color="#000000" />
            </AnimatedPressable> */}
          </ScrollViewBottomStick>
        </View>
      </View>
    </View>
  );
}