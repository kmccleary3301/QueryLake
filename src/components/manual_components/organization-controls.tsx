import { useState, useEffect } from "react";
import AnimatedPressable from "./animated-pressable";
import craftUrl from "@/hooks/craftUrl";
import { DropDownSelection } from "./dropdown-selection";
import {
	userDataType,
	membershipType
} from "@/typing/globalTypes";
import * as Icon from 'react-feather';
import { formEntryType } from "./dropdown-selection";
import { Input } from "../ui/input";
import { ScrollArea } from "../ui/scroll-area";

type organizationRoles = "owner" | "admin" | "member" | "viewer";

// type membershipAcceptedType = {
//   invite_still_open: false,
//   organization_id: number,
//   organization_name: string,
//   role: organizationRoles
// };

type OrganizationControlsProps = {
  userData: userDataType,
  organization: membershipType,
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
  const [availableInviteRoles, setAvailableInviteRoles] = useState<formEntryType[]>([]);
  const [invitationRole, setInvitationRole] = useState<organizationRoles>("viewer");

  useEffect(() => {
    const available_invite_roles : formEntryType[] = [];
    for (const [key, value] of Object.entries(membershipValueMap)) {
      if (value < membershipValueMap[props.organization.role] || props.organization.role === "owner") {
        available_invite_roles.push({
          label: key,
          value: key
        });
      }
    }
    setAvailableInviteRoles(available_invite_roles);

    const url = craftUrl(`/api/fetch_memberships_of_organization`, {
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
  }, [props.organization, props.userData.password_pre_hash, props.userData.username]);

  // const updateMembershipRole = (
	// 	// username : string, 
	// 	// new_role : orgMemberType
	// ) => {

  // }

  const updateOrganization = () => {

    props.onFinish();
  };

  const inviteUser = () => {
    const url = craftUrl(`/api/invite_user_to_organization`, {
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
    <div style={{
			display: "flex",
      alignItems: 'center',
      justifyContent: 'center',
      flexDirection: 'column',
      flex: 1,
    }}>
      <div id={"OrganizationControlBox"} style={{
        alignItems: 'center',
				display: "flex",
        justifyContent: 'center',
        flexDirection: 'column',
        borderRadius: 15,
        // height: 400,
        // width: 400,
        backgroundColor: '#39393C',
        paddingLeft: 25,
				paddingRight: 25,
        paddingBottom: 15,
        paddingTop: 15,
      }}>
        <div style={{display: "flex", flexDirection: "row"}}>
          <div style={{display: "flex",flexDirection: "column"}}>
            <span style={{
              // fontFamily: 'Inter-Regular',
              fontSize: 20,
              paddingBottom: 5,
              paddingTop: 0,
              paddingLeft: 10,
							paddingRight: 10,
              color: '#E8E3E3',
              textAlign: 'center'
            }}>
              {"Manage Organization"}
            </span>
            {(props.organization.role === "admin" || props.organization.role === "owner" || props.organization.role === "member") && (
              <div style={{display: "flex", width: '100%', flexDirection: 'row', justifyContent: 'space-around'}}>
                <div style={{
									display: "flex",
                  flexDirection: 'row',
                  backgroundColor: '#17181D',
                  width: 200,
                  height: 40,
                  borderRadius: 10,
                  borderWidth: 2,
                  borderColor: (attemptInviteResult !== undefined)?(attemptInviteResult?"#88C285":"#E50914"):"none"
                }}>
                  <div style={{display: "flex", flex: 1, height: '100%'}}>
										<Input
											// type="password"
											spellCheck={false}
											placeholder="SERP Key"
											value={userToInvite}
											onChange={(e) => {
												const val = e.target?.value;
												setUserToInvite(val);
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
													borderColor: "none"
												}}
										/>
                  </div>
                  <div id="PressablePadView" style={{
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
                      <Icon.Send size={15} color="#E8E3E3" />
                    </AnimatedPressable>
                  </div>
                </div>
                {(availableInviteRoles.length > 0) && (
                  <div style={{
                    height: 40,
										display: "flex",
                    flexDirection: 'column',
                    justifyContent: 'center'
                  }}>
                    <DropDownSelection
                      values={availableInviteRoles}
                      defaultValue={{label : invitationRole, value : invitationRole}}
											selection={{label : invitationRole, value : invitationRole}}
                      setSelection={(value : formEntryType) => {
												const value_as = value.value as organizationRoles;
												setInvitationRole(value_as);
											}}
											width={200}
                    />
                  </div>
                )}
              </div>
            )}
            <div style={{
							display: "flex",
              flexDirection: 'row',
              justifyContent: 'space-between',
              paddingBottom: 10,
            }}/>
            <div style={{
              backgroundColor: '#E8E3E3',
              height: 2,
              paddingTop: 2,
              borderRadius: 1,
              width: '100%'
            }}/>
            <div style={{
							display: "flex",
              flexDirection: 'row',
              justifyContent: 'space-between',
              paddingBottom: 10,
            }}/>
            <div style={{paddingBottom: 10}}>
              {/* <spanInput
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
              /> */}
							<Input
								// type="password"
								spellCheck={false}
								placeholder="Name"
								contentEditable={(props.organization.role === "admin" || props.organization.role === "owner")}
								value={createOrganizationName}
								onChange={(e) => {
									const val = e.target?.value;
									setCreateOrganizationName(val);
								}}
								style={{
									color: '#E8E3E3',
                  fontSize: 16,
                  // textAlignVertical: 'center',
                  // fontFamily: 'Inter-Regular',
                  backgroundColor: "#17181D",
                  borderRadius: 15,
                  padding: 10,
                  width: 450,
								}}
							/>
            </div>
            <div style={{paddingBottom: 10}}>
              {/* <spanInput
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
              /> */}
							<Input
								// type="password"
								spellCheck={false}
								contentEditable={(props.organization.role === "admin" || props.organization.role === "owner")}
								placeholder="Description"
								value={createOrganizationDescription}
								onChange={(e) => {
									const val = e.target?.value;
									setCreateOrganizationDescription(val);
								}}
								style={{
									color: '#E8E3E3',
                  fontSize: 16,
                  // textAlignVertical: 'center',
                  // fontFamily: 'Inter-Regular',
                  backgroundColor: "#17181D",
                  borderRadius: 15,
                  padding: 10,
                  width: 450,
								}}
							/>
            </div>
          </div>
        </div>
        {(organizationMembers !== undefined && organizationMembers.length > 0) && (
          <ScrollArea style={{
						display: "flex",
            width: 320,
            maxHeight: 200,
            flexGrow: 1,
          }}>
            <span style={{
              width: '100%',
              textAlign: 'center',
              // textAlignVertical: 'center',
              paddingTop: 6,
							paddingBottom: 6,
              // fontFamily: 'Inter-Regular',
              fontSize: 20,
              color: '#E8E3E3'
            }}>
              {"Members"}
            </span>
            {organizationMembers.map((value : orgMemberType, index: number) => (
              <div key={index} style={{
								display: "flex",
                flexDirection: 'row',
                justifyContent: 'space-between',
                height: 40
              }}>
                <span style={{
                  maxWidth: 50,
                  textAlign: 'center',
                  // textAlignVertical: 'center',
                  height: 40,
                  // fontFamily: 'Inter-Regular',
                  fontSize: 12,
                  color: '#E8E3E3'
                }}>
                  {value.username}
                </span>
                {((props.organization.role === "admin" || props.organization.role === "owner") &&
                  (membershipValueMap[props.organization.role] > membershipValueMap[value.role]))?(
                    <div style={{
                      height: 40,
											display: "flex",
                      flexDirection: 'column',
                      justifyContent: 'center',
                    }}>
                      {/* <DropDownSelection
                        values={availableInviteRoles}
                        defaultValue={{label : value.role, value : value.role}}
												selection={}
                        setSelection={(new_value : formEntryType) => {
													const value =  new_value.value as organizationRoles;
                          updateMembershipRole(value.username, new_value.value);
                        }}
                        // width={85}
                      /> */}
											<span style={{
												fontSize: 12,
												color: '#E8E3E3'
											}}>
												{"Add role changer here"}
											</span>
                    </div>
                ):(
                  <span style={{
                    maxWidth: 50,
                    textAlign: 'center',
                    // textAlignVertical: 'center',
                    
                    // fontFamily: 'Inter-Regular',
                    fontSize: 12,
                    color: '#E8E3E3'
                  }}>
                    {value.role}
                  </span>
                )}
              </div>
            ))}
          </ScrollArea>
        )}
        <AnimatedPressable style={{
					display: "flex",
          width: '100%',
          borderRadius: 10,
          backgroundColor: '#7968D9',
          alignItems: 'center',
          justifyContent: 'center'
        }} onPress={updateOrganization}>
          <div style={{width: '100%'}}>
          <span style={{
            // fontFamily: 'Inter-Regular',
            fontSize: 24,
            color: '#E8E3E3',
            alignSelf: 'center',
            padding: 10,
            width: '100%',
          }}>
            {"Save Changes"}
          </span>
          </div>
        </AnimatedPressable>
      </div>
    </div>
  );
}