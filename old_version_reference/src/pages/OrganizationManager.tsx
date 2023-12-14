import { useState, useRef, useEffect } from "react";
import { useFonts } from "expo-font";
import {
  View,
  Text,
  Pressable,
  TextInput,
  ScrollView,
  Animated,
  Easing
} from "react-native";
import AnimatedPressable from "../components/AnimatedPressable";
import { Feather } from "@expo/vector-icons";
import craftUrl from "../hooks/craftUrl";
import getUserMemberships from "../hooks/getUserMemberships";
import globalStyleSettings from "../../globalStyleSettings";
import HoverEntryGeneral from "../components/HoverEntryGeneral";
import OrganizationControls from "../components/OrganizationControls";

type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships: membershipType[],
  is_admin: boolean
};

type OrganizationManagerProps = {
  userData: userDataType,
  toggleSideBar?: () => void,
  sidebarOpened: boolean,
  setUserData: React.Dispatch<React.SetStateAction<userDataType>>
};

type membershipOpenType = {
  invite_still_open: true,
  sender: string,
  organization_id: number,
  organization_name: string,
  role: "owner" | "admin" | "member" | "viewer"
};

type membershipAcceptedType = {
  invite_still_open: false,
  organization_id: number,
  organization_name: string,
  role: "owner" | "admin" | "member" | "viewer"
};

type membershipType = membershipOpenType | membershipAcceptedType;

export default function OrganizationManager(props : OrganizationManagerProps) {
  const [acceptedMemberships, setAcceptedMemberships] = useState<membershipAcceptedType[]>([]);
  const [membershipInvites, setMembershipInvites] = useState<membershipOpenType[]>([]);
  const [openedInvites, setOpenedInvites] = useState(false);
  const [openedAccepted, setOpenedAccepted] = useState(false);
  const [organizationPanel, setOrganizationPanel] = useState<undefined | "CreateOrganization" | "ControlOrganization">(undefined);
  const [createOrganizationName, setCreateOrganizationName] = useState("");
  const [createOrganizationDescription, setCreateOrganizationDescription] = useState("");
  const [selectedOrganization, setSelectedOrganization] = useState<undefined | membershipAcceptedType>();
	// const [selected, setSelected] = useState(false);
	// const [viewScrollable, setViewScrollable] = useState(false);

  const boxHeightInvites = useRef(new Animated.Value(42));
  const boxHeightAccepted = useRef(new Animated.Value(42));

  const refreshUserMemberships = () => {
    getUserMemberships(props.userData.username, props.userData.password_pre_hash, "all", (result: object[]) => {
      props.setUserData({...props.userData, memberships: result});
    })
  };

  const openOrganizationControls = (membership : membershipAcceptedType) => {
    setSelectedOrganization(membership);
    setOrganizationPanel("ControlOrganization");
  };

  const resolveInvite = (organization_id : number, choice : boolean) => {
    const url = craftUrl("http://localhost:5000/api/resolve_organization_invitation", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "organization_id": organization_id,
      "accept": choice
    });

    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to resolve invite:", data.note);
          return;
        }
        refreshUserMemberships();
      });
    });
  }

  const createOrganization = () => {
    const url = craftUrl("http://localhost:5000/api/create_organization", {...{
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "organization_name": createOrganizationName,
    }, ...(createOrganizationDescription !== "")?{"organization_description": createOrganizationDescription}:{}},);

    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to create organization:", data.note);
          return;
        }
        refreshUserMemberships();
        setCreateOrganizationName("");
        setCreateOrganizationDescription("");
        setOrganizationPanel(undefined);
      });
    });
  };

  useEffect(() => {
    console.log("memberships:");
    console.log(props.userData);
    let invites : membershipOpenType[] = [], accepted_memberships : membershipAcceptedType[] = [];
    for (const [key, value] of Object.entries(props.userData.memberships)) {
      if (value.invite_still_open) {
        invites.push(value);
      } else {
        accepted_memberships.push(value);
      }
    }
    setAcceptedMemberships(accepted_memberships);
    setMembershipInvites(invites);
  }, [props.userData]);

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

  useEffect(() => {
    Animated.timing(boxHeightInvites.current, {
      toValue: (openedInvites && membershipInvites.length > 0)?(membershipInvites.length*45+48):42,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [openedInvites, membershipInvites]);

  useEffect(() => {
    Animated.timing(boxHeightAccepted.current, {
      toValue: (openedAccepted && acceptedMemberships.length > 0)?(acceptedMemberships.length*45+48):42,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [openedAccepted, acceptedMemberships]);

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
        <View id="ContentBody" style={{
          flex: 1,
          width: "100%",
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
          <View style={{
            height: "100%",
            width: 320,
            flexDirection: 'column',
            paddingLeft: 20,
          }}>
            <Text style={{
              width: '100%',
              textAlign: 'center',
              textAlignVertical: 'center',
              height: 40,
              fontFamily: 'Inter-Regular',
              fontSize: 28,
              color: '#E8E3E3'
            }}>
              {"Memberships"}
            </Text>
            <Animated.ScrollView style={{
              width: '100%',
              flex: 1,
            }}>
              <View style={{paddingBottom: 10, maxWidth: '100%'}}>
                <AnimatedPressable style={{
                  width: 300,
                  backgroundColor: '#39393C',
                  flexDirection: 'row',
                  borderRadius: 20,
                  // justifyContent: 'space-around',
                  height: 36,
                  alignItems: 'center',
                  justifyContent: 'center'}}
                  onPress={() => {
                    setOrganizationPanel("CreateOrganization");
                  }}>
                    <View style={{paddingRight: 5}}>
                      <Feather name="plus" size={20} color="#E8E3E3" />
                    </View>
                    <View style={{alignSelf: 'center', justifyContent: 'center'}}>
                    <Text style={{
                      // width: '100%',
                      // height: '100%',
                      fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      color: '#E8E3E3',
                      paddingTop: 1
                    }}>{"New Organization"}</Text>
                    </View>
                </AnimatedPressable>
              </View>
              <Animated.ScrollView style={{
                width: '100%',
                flexDirection: 'column',
                borderRadius: 20,
                // justifyContent: 'space-around',
                // paddingVertical: 10,
                paddingTop: 8,
                height: boxHeightInvites.current,
                // alignSelf: 'center',
              }} scrollEnabled={false} showsVerticalScrollIndicator={false}>
                <View style={{
                  // height: 200,
                  flexDirection: 'row',
                  // paddingRight: 16,
                  // paddingLeft: 12,
                  paddingBottom: 8,
                  // alignItems: 'center',
                  // justifyContent: 'space-around',
                }}>
                  <View style={{
                    // width: '83%',
                    flex: 1,
                    flexDirection: 'column',
                    justifyContent: 'center',
                    // paddingLeft: 9,
                  }}>
                    <Text style={{
                      fontSize: 16,
                      color: globalStyleSettings.colorText,
                      textAlign: 'left',
                      textAlignVertical: 'center',
                      height: 25,
                      width: '100%',
                    }}
                    numberOfLines={1}
                    >
                      {"Invitations"}
                    </Text>
                  </View>
                  <View style={{flexDirection: 'column', justifyContent: 'center'}}>
                    <Pressable 
                      onPress={() => {
                        setOpenedInvites(opened => !opened);
                      }}
                    >
                      <Feather 
                        name="chevron-down" 
                        size={24} 
                        color={globalStyleSettings.colorText}
                        style={{
                          transform: openedInvites?"rotate(0deg)":"rotate(90deg)"
                        }}
                      />
                    </Pressable>
                  </View>
                </View>
                
                <ScrollView style={{
                    paddingBottom: 5,
                  }}
                  showsVerticalScrollIndicator={false}
                >
                  {membershipInvites.map((value : membershipOpenType, index: number) => (
                    <HoverEntryGeneral key={index} title={value.organization_name}>
                      <AnimatedPressable onPress={() => {
                        resolveInvite(value.organization_id, true);
                      }} style={{paddingRight: 10}}>
                        <Feather name="check" size={16} color={'#E8E3E3'} st/>
                      </AnimatedPressable>
                      <AnimatedPressable onPress={() => {
                        resolveInvite(value.organization_id, false);
                      }} style={{paddingRight: 10}}>
                        <Feather name="x" size={16} color={'#E8E3E3'} st/>
                      </AnimatedPressable>
                    </HoverEntryGeneral>
                  ))}
                </ScrollView>
                
              </Animated.ScrollView>
              <Animated.ScrollView style={{
                width: '100%',
                flexDirection: 'column',
                borderRadius: 20,
                // justifyContent: 'space-around',
                // paddingVertical: 10,
                paddingTop: 8,
                height: boxHeightAccepted.current,
                // alignSelf: 'center',
              }} scrollEnabled={false} showsVerticalScrollIndicator={false}>
                <View style={{
                  // height: 200,
                  flexDirection: 'row',
                  // paddingRight: 16,
                  // paddingLeft: 12,
                  paddingBottom: 8,
                  // alignItems: 'center',
                  // justifyContent: 'space-around',
                }}>
                  <View style={{
                    // width: '83%',
                    flex: 1,
                    flexDirection: 'column',
                    justifyContent: 'center',
                    // paddingLeft: 9,
                  }}>
                    <Text style={{
                      fontSize: 16,
                      color: globalStyleSettings.colorText,
                      textAlign: 'left',
                      textAlignVertical: 'center',
                      height: 25,
                      width: '100%',
                    }}
                    numberOfLines={1}
                    >
                      {"Organizations"}
                    </Text>
                  </View>
                  <View style={{flexDirection: 'column', justifyContent: 'center'}}>
                    <Pressable 
                      onPress={() => {
                        setOpenedAccepted(opened => !opened);
                      }}
                    >
                      <Feather 
                        name="chevron-down" 
                        size={24} 
                        color={globalStyleSettings.colorText}
                        style={{
                          transform: openedAccepted?"rotate(0deg)":"rotate(90deg)"
                        }}
                      />
                    </Pressable>
                  </View>
                </View>
                
                <ScrollView style={{
                    paddingBottom: 5,
                  }}
                  showsVerticalScrollIndicator={false}
                >
                  {acceptedMemberships.map((value : membershipAcceptedType, index: number) => (
                    <AnimatedPressable key={index} onPress={() => {
                      openOrganizationControls(value);
                    }} style={{
                      flexDirection: 'row',
                      justifyContent: 'space-between',
                      width: '100%'
                    }}>
                      <Text style={{
                        maxWidth: "100%",
                        textAlign: 'center',
                        textAlignVertical: 'center',
                        alignSelf: 'flex-start',
                        fontFamily: 'Inter-Regular',
                        fontSize: 14,
                        color: '#E8E3E3',
                        paddingLeft: 4
                      }} numberOfLines={1}>
                        {value.organization_name}
                      </Text>
                      <Text style={{
                        maxWidth: "100%",
                        textAlign: 'center',
                        textAlignVertical: 'center',
                        alignSelf: 'flex-start',
                        fontFamily: 'Inter-Regular',
                        fontSize: 14,
                        color: '#4D4D56',
                      }} numberOfLines={1}>
                        {value.role}
                      </Text>
                    </AnimatedPressable>
                  ))}
                </ScrollView>
                
              </Animated.ScrollView>
            </Animated.ScrollView>
          </View>
          <View style={{
            flex: 1,
            height: '100%',
            justifyContent: 'center',
            alignContent: 'center'
          }}>
            {(organizationPanel !== undefined) && (
              (organizationPanel === "CreateOrganization")?(
                <View style={{
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  flex: 1,
                }}>
                  <View id={"OrganizationBox"} style={{
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                    borderRadius: 15,
                    // height: 400,
                    // width: 400,
                    backgroundColor: '#39393C',
                    paddingHorizontal: 25,
                    paddingBottom: 25,
                    paddingTop: 15,
                  }}>
                    <View style={{flexDirection: "row"}}>
                      <View style={{flexDirection: "column"}}>
                        <Text style={{
                          fontFamily: 'Inter-Regular',
                          fontSize: 20,
                          paddingBottom: 5,
                          paddingTop: 0,
                          paddingHorizontal: 10,
                          color: '#E8E3E3',
                          textAlign: 'center'
                        }}>
                          {"Create a New Organization"}
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
                          justifyContent: 'space-between',
                          paddingBottom: 10,
                        }}>
                        </View>
                        <View style={{paddingBottom: 10}}>
                          <TextInput
                            editable
                            numberOfLines={1}
                            placeholder="Name"
                            placeholderTextColor={"#4D4D56"}
                            value={createOrganizationName}
                            onChangeText={(text) => {
                              setCreateOrganizationName(text);
                            }}
                            style={{
                              color: '#E8E3E3',
                              fontSize: 16,
                              textAlignVertical: 'center',
                              fontFamily: 'Inter-Regular',
                              backgroundColor: "#17181D",
                              borderRadius: 15,
                              padding: 10,
                              width: 450,
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
                            value={createOrganizationDescription}
                            onChangeText={(text) => {
                              setCreateOrganizationDescription(text);
                            }}
                            style={{
                              color: '#E8E3E3',
                              fontSize: 16,
                              textAlignVertical: 'center',
                              fontFamily: 'Inter-Regular',
                              backgroundColor: "#17181D",
                              borderRadius: 15,
                              padding: 10,
                              width: 450,
                            }}
                          />
                        </View>
                      </View>
                    </View>
                    
                    <AnimatedPressable style={{
                      width: '100%',
                      borderRadius: 10,
                      backgroundColor: '#7968D9',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }} onPress={createOrganization}>
                      <View style={{width: '100%'}}>
                      <Text style={{
                        fontFamily: 'Inter-Regular',
                        fontSize: 24,
                        color: '#E8E3E3',
                        alignSelf: 'center',
                        padding: 10,
                        width: '100%',
                      }}>
                        {"Create Organization"}
                      </Text>
                      </View>
                    </AnimatedPressable>
                  </View>
                </View>
              ):(
                (selectedOrganization !== undefined)?(
                  <OrganizationControls
                    userData={props.userData}
                    organization={selectedOrganization}
                    onFinish={() => {
                      setOrganizationPanel(undefined);
                      setSelectedOrganization(undefined);
                    }}
                  />
                ):(
                  <></>
                )
              )
            )}
          </View>
        </View>
      </View>
    </View>
  );
}