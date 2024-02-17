import { useState } from "react";
import ScrollViewBottomStickInner from "../manual_components/scrollable-bottom-stick/scrollview-bottom-stick-inner";
import { setSerpKey } from "@/hooks/querylakeAPI";
import * as Icon from 'react-feather';
import { setOpenAIAPIKey } from "@/hooks/querylakeAPI";
import { Button } from "../ui/button";
// import AnimatedPressable from "../manual_components/animated-pressable";
import { userDataType } from "@/typing/globalTypes";
import { Input } from "../ui/input";

type UserSettingsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>
};

export default function UserSettings(props : UserSettingsProps) {
  const [serpKeyInput, setSerpKeyInput] = useState((props.userData.serp_key)?props.userData.serp_key:"");
  const [openAIAPIKeyInput, setOpenAIAPIKeyInput] = useState("");
  const [attemptSERPResult, setAttemptSERPResult] = useState<undefined | boolean>();
  const [attemptOpenAIResult, setAttemptOpenAIResult] = useState<undefined | boolean>();


  const send_serp_key_finish = (result : boolean) => {
    if (result) {
      props.setUserData({...props.userData, ...{serp_key: serpKeyInput}})
    }
    setAttemptSERPResult(result);
  }

  const send_serp_key = () => {
    setSerpKey({
			serp_key: serpKeyInput, 
			userdata: props.userData, 
			onFinish: send_serp_key_finish
		});
  }


  const send_openai_key = () => {
    setOpenAIAPIKey({
			api_key: openAIAPIKeyInput, 
			userdata: props.userData, 
			onFinish: setAttemptOpenAIResult
		});
  }

  return (
    <div style={{
      flex: 1,
			display: "flex", 
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <div style={{display: "flex", flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <div style={{
					display: "flex",
          flexDirection: "column",
          flex: 1,
          // height: "100%",
          // width: "88%",
          width: "60vw",
          paddingLeft: 0,
					paddingRight: 0,
          alignContent: 'center'
          // paddingVertical: 24,
        }}>
          <ScrollViewBottomStickInner height_string="" animateScroll={false}>
            <div style={{display: "flex", width: '100%', flexDirection: 'row', justifyContent: 'center'}}>
              <p style={{
                // fontFamily: 'Inter-Regular',
                fontSize: 24,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Personal SERP Key"}
              </p>
            </div>
            <div style={{width: '100%', flexDirection: 'row', justifyContent: 'center', paddingTop: 10, paddingBottom: 10}}>
              <p style={{
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"API Key for Google Search API. Sign up "}
                <Button variant="link" style={{color: '#7968D9', padding: 0}} onClick={() => {window.open("https://serpapi.com/users/sign_up")}}>{"here"}</Button>
                {", or get your API key "}
                <Button variant="link" style={{color: '#7968D9', padding: 0}} onClick={() => {window.open("https://serpapi.com/manage-api-key")}}>{"here"}</Button>
              </p>
            </div>
            <div style={{width: '100%', display: 'flex', flexDirection: 'row', justifyContent: 'center'}}>
              <div style={{
								display: 'flex',
                flexDirection: 'row',
                // backgroundColor: '#17181D',
                width: '30vw',
                height: 40,
								paddingLeft: 2,
								paddingRight: 2,
                // borderRadius: 10,
                // borderWidth: 2,
                
              }}>
                <div style={{flex: 1, height: '100%'}}>
                  <Input
										type="password"
                    spellCheck={false}
                    placeholder="SERP Key"
                    value={serpKeyInput}
                    onChange={(e) => {
											const val = e.target?.value;
											setSerpKeyInput(val);
										}}
                    style={{
                        // height: inputBoxHeight,
                        color: '#E8E3E3',
                        fontSize: 14,
                        // textAlignVertical: 'center',
                        outlineStyle: 'none',
                        // fontFamily: 'Inter-Regular',
												borderWidth: 2,
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%',
												borderColor: (attemptSERPResult !== undefined)?(attemptSERPResult?"#88C285":"#E50914"):"none"
                      }}
                  />
                </div>
                <div id="PressablePadView" style={{
                  paddingLeft: 10,
                  paddingRight: 10,
                  alignSelf: 'center',
                }}>
                  <Button variant="default" size="icon" onClick={() => {
                      send_serp_key();
                    }}
                    style={{
                    padding: 10,
                    // height: 24,
                    // width: 24,
                    // backgroundColor: "#7968D9",
                    borderRadius: "50%",
										display: "flex",
                    alignItems: 'center',
                    justifyContent: 'center'
                    }}
                  >
                    <Icon.Send size={24} color="#000000" />
                  </Button>
                </div>
              </div>
            </div>
            <div style={{width: '100%', display: 'flex', flexDirection: 'row', justifyContent: 'center', paddingTop: 20}}>
              <p style={{
                // fontFamily: 'Inter-Regular',
                fontSize: 24,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Personal OpenAI API Key"}
              </p>
            </div>
            <div style={{width: '100%', flexDirection: 'row', justifyContent: 'center', paddingTop: 10, paddingBottom: 10}}>
              <p style={{
                // fontFamily: 'Inter-Regular',
                fontSize: 14,
                paddingBottom: 5,
                paddingTop: 5,
                width: '30vw',
                color: '#E8E3E3',
                textAlign: 'center'
              }}>
                {"Use an OpenAI API key to use proprietary models with QueryLake"}
              </p>
            </div>
            <div style={{width: '100%', display: 'flex', flexDirection: 'row', justifyContent: 'center'}}>
              <div style={{
								display: 'flex',
                flexDirection: 'row',
                // backgroundColor: '#17181D',
                width: '30vw',
                height: 40,
								paddingLeft: 2,
								paddingRight: 2,
                // borderRadius: 10,
                // borderWidth: 2,
                
              }}>
                <div style={{flex: 1, height: '100%'}}>
                  <Input
                    id="openai_key"
										type="password"
                    spellCheck={false}
										hidden={true}
                    placeholder="OpenAI API Key"
                    value={openAIAPIKeyInput}
                    onChange={(e) => {
											const val = e.target?.value;
											setOpenAIAPIKeyInput(val);
                    }}
                    style={{
                        color: '#E8E3E3',
                        fontSize: 14,
                        outlineStyle: 'none',
                        maxWidth: '100%',
                        padding: 5,
                        height: '100%',
												borderWidth: 2,
												borderColor: (attemptOpenAIResult !== undefined)?(attemptOpenAIResult?"#88C285":"#E50914"):"none"
                      }}
                  />
                </div>
                <div id="PressablePadView" style={{
                  paddingLeft: 10,
                  paddingRight: 10,
                  alignSelf: 'center',
                }}>
                  <Button variant="default" size="icon" onClick={() => {
                      send_openai_key();
                    }}
                    style={{
                    padding: 10,
                    // height: 24,
                    // width: 24,
                    // backgroundColor: "#7968D9",
                    borderRadius: "50%",
										display: "flex",
                    alignItems: 'center',
                    justifyContent: 'center'
                    }}
                  >
                    <Icon.Send size={24} color="#000000" />
                  </Button>
                </div>
              </div>
            </div>
          </ScrollViewBottomStickInner>
        </div>
      </div>
    </div>
  );
}