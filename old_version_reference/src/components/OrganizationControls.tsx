import { useState, useRef, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  ScrollView,
  Platform,
} from "react-native";
import AnimatedPressable from "./AnimatedPressable";
import { Feather } from "@expo/vector-icons";
import craftUrl from "../hooks/craftUrl";
import HoverEntryGeneral from "./HoverEntryGeneral";
import DropDownSelection from "./DropDownSelection";

type userDataType = {
  username: string,
  password_pre_hash: string,
  memberships: object[],
  is_admin: boolean
};

type organizationRoles = "owner" | "admin" | "member" | "viewer";

type membershipAcceptedType = {
  invite_still_open: false,
  organization_id: number,
  organization_name: string,
  role: organizationRoles
};

type OrganizationControlsProps = {
  userData: userDataType,
  organization: membershipAcceptedType,
  onFinish: () => void,
};

type orgMemberType = {
  username: string,
  role: organizationRoles,
}


const membershipValueMap = {
  "owner": 4,
  "admin": 3,
  "member": 2,
  "viewer": 1
}
// type membership = {

// }

export default function OrganizationControls(props : OrganizationControlsProps) {
  // const [acceptedMemberships, setAcceptedMemberships] = useState<membershipAcceptedType[]>([]);
  const [createOrganizationName, setCreateOrganizationName] = useState(props.organization.organization_name);
  const [createOrganizationDescription, setCreateOrganizationDescription] = useState("");
  const [attemptInviteResult, setAttemptInviteResult] = useState<undefined | boolean>();
  const [userToInvite, setUserToInvite] = useState("");
  const [organizationMembers, setOrganizationMembers] = useState<orgMemberType[]>([]);
  const [availableInviteRoles, setAvailableInviteRoles] = useState<{label : string, value : string}[]>([]);
  const [invitationRole, setInvitationRole] = useState<organizationRoles>("viewer");

  useEffect(() => {
    let available_invite_roles = [];
    for (const [key, value] of Object.entries(membershipValueMap)) {
      if (value < membershipValueMap[props.organization.role] || props.organization.role === "owner") {
        available_invite_roles.push({
          label: key,
          value: key
        });
      }
    }
    setAvailableInviteRoles(available_invite_roles);

    const url = craftUrl("http://localhost:5000/api/fetch_memberships_of_organization", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "organization_id": props.organization.organization_id,
    });
    
    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to retrieve organization members:", data.note);
          return;
        }
        setOrganizationMembers(data.memberships);
      });
    });
  }, [props.organization]);

  const updateMembershipRole = (username : string, new_role : orgMemberType) => {

  }

  const updateOrganization = () => {

    props.onFinish();
  };

  const inviteUser = () => {
    const url = craftUrl("http://localhost:5000/api/invite_user_to_organization", {
      "username": props.userData.username,
      "password_prehash": props.userData.password_pre_hash,
      "organization_id": props.organization.organization_id,
      "username_to_invite": userToInvite,
      "member_class": invitationRole,
    });

    fetch(url, {method: "POST"}).then((response) => {
      response.json().then((data) => {
        console.log(data);
        if (!data["success"]) {
          console.error("Failed to invite user to organization:", data.note);
          setAttemptInviteResult(false);
          return;
        }
        setAttemptInviteResult(true);
      });
    });
  };

  return (
    <View style={{
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      flex: 1,
    }}>
      <View id={"OrganizationControlBox"} style={{
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        borderRadius: 15,
        // height: 400,
        // width: 400,
        backgroundColor: '#39393C',
        paddingHorizontal: 25,
        paddingBottom: 15,
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
              {"Manage Organization"}
            </Text>
            {(props.organization.role === "admin" || props.organization.role === "owner" || props.organization.role === "member") && (
              <View style={{width: '100%', flexDirection: 'row', justifyContent: 'space-around'}}>
                <View style={{
                  flexDirection: 'row',
                  backgroundColor: '#17181D',
                  width: 200,
                  height: 40,
                  borderRadius: 10,
                  borderWidth: 2,
                  borderColor: (attemptInviteResult !== undefined)?(attemptInviteResult?"#88C285":"#E50914"):"none"
                }}>
                  <View style={{flex: 1, height: '100%'}}>
                    <TextInput
                      id="InvitedUser"
                      autoCorrect={false}
                      spellCheck={false}
                      editable
                      numberOfLines={1}
                      placeholder="Invite User"
                      placeholderTextColor={"#4D4D56"}
                      value={userToInvite}
                      onChangeText={(text) => {
                        setUserToInvite(text);
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
                      onPress={inviteUser}
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
                {(availableInviteRoles.length > 0) && (
                  <View style={{
                    height: 40,
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}>
                    <DropDownSelection
                      values={availableInviteRoles}
                      defaultValue={{label : "viewer", value : "viewer"}}
                      setSelection={setInvitationRole}
                      width={160}
                    />
                  </View>
                )}
              </View>
            )}
            <View style={{
              flexDirection: 'row',
              justifyContent: 'space-between',
              paddingBottom: 10,
            }}/>
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
            }}/>
            <View style={{paddingBottom: 10}}>
              <TextInput
                editable={(props.organization.role === "admin" || props.organization.role === "owner")}
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
                editable={(props.organization.role === "admin" || props.organization.role === "owner")}
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
        {(organizationMembers !== undefined && organizationMembers.length > 0) && (
          <ScrollView style={{
            width: 320,
            maxHeight: 200,
            flexGrow: 1,
          }}>
            <Text style={{
              width: '100%',
              textAlign: 'center',
              textAlignVertical: 'center',
              paddingVertical: 6,
              fontFamily: 'Inter-Regular',
              fontSize: 20,
              color: '#E8E3E3'
            }}>
              {"Members"}
            </Text>
            {organizationMembers.map((value : orgMemberType, index: number) => (
              <View key={index} style={{
                flexDirection: 'row',
                justifyContent: 'space-between',
                height: 40
              }}>
                <Text style={{
                  maxWidth: 50,
                  textAlign: 'center',
                  textAlignVertical: 'center',
                  height: 40,
                  fontFamily: 'Inter-Regular',
                  fontSize: 12,
                  color: '#E8E3E3'
                }}>
                  {value.username}
                </Text>
                {((props.organization.role === "admin" || props.organization.role === "owner") &&
                  (membershipValueMap[props.organization.role] > membershipValueMap[value.role]))?(
                    <View style={{
                      height: 40,
                      flexDirection: 'column',
                      justifyContent: 'center',
                    }}>
                      <DropDownSelection
                        values={availableInviteRoles}
                        defaultValue={{label : value.role, value : value.role}}
                        setSelection={(new_value : {label: string, value: orgMemberType}) => {
                          updateMembershipRole(value.username, new_value.value);
                        }}
                        width={85}
                      />
                    </View>
                ):(
                  <Text style={{
                    maxWidth: 50,
                    textAlign: 'center',
                    textAlignVertical: 'center',
                    
                    fontFamily: 'Inter-Regular',
                    fontSize: 12,
                    color: '#E8E3E3'
                  }} numberOfLines={1}>
                    {value.role}
                  </Text>
                )}
              </View>
            ))}
          </ScrollView>
        )}
        <AnimatedPressable style={{
          width: '100%',
          borderRadius: 10,
          backgroundColor: '#7968D9',
          alignItems: 'center',
          justifyContent: 'center'
        }} onPress={updateOrganization}>
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
      </View>
    </View>
  );
}