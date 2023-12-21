import { useState, useEffect } from "react";
import AnimatedPressable from "../manual_components/animated-pressable";
import * as Icon from 'react-feather';
import craftUrl from "@/hooks/craftUrl";
import { getUserMemberships } from "@/hooks/querylakeAPI";
// import HoverEntryGeneral from "../components/HoverEntryGeneral";
import HoverEntryGeneral from "../manual_components/hover-entry-general";
import OrganizationControls from "../manual_components/organization-controls";
import { Input } from "../ui/input";
import { 
	userDataType,
	membershipType,
} from "@/globalTypes";
import { ScrollArea } from "../ui/scroll-area";
import { motion, useAnimation } from "framer-motion";
import { Button } from "../ui/button";

// type userDataType = {
//   username: string,
//   password_pre_hash: string,
//   memberships: membershipType[],
//   is_admin: boolean
// };

type OrganizationManagerProps = {
  userData: userDataType,
  // toggleSideBar?: () => void,
  sidebarOpened: boolean,
  setUserData: React.Dispatch<React.SetStateAction<userDataType>>
};

// type membershipOpenType = {
//   invite_still_open: true,
//   sender: string,
//   organization_id: number,
//   organization_name: string,
//   role: "owner" | "admin" | "member" | "viewer"
// };

// type membershipAcceptedType = {
//   invite_still_open: false,
//   organization_id: number,
//   organization_name: string,
//   role: "owner" | "admin" | "member" | "viewer"
// };

// type membershipType = membershipOpenType | membershipAcceptedType;

export default function OrganizationManager(props : OrganizationManagerProps) {
  const [acceptedMemberships, setAcceptedMemberships] = useState<membershipType[]>([]);
  const [membershipInvites, setMembershipInvites] = useState<membershipType[]>([]);
  const [openedInvites, setOpenedInvites] = useState(false);
  const [openedAccepted, setOpenedAccepted] = useState(false);
  const [organizationPanel, setOrganizationPanel] = useState<undefined | "CreateOrganization" | "ControlOrganization">(undefined);
  const [createOrganizationName, setCreateOrganizationName] = useState("");
  const [createOrganizationDescription, setCreateOrganizationDescription] = useState("");
  const [selectedOrganization, setSelectedOrganization] = useState<undefined | membershipType>();
	// const [selected, setSelected] = useState(false);
	// const [viewScrollable, setViewScrollable] = useState(false);

	const controlHeightInvites = useAnimation();
	useEffect(() => {
		controlHeightInvites.set({
			height: 42
		});
	}, [controlHeightInvites]);

	const controlHeightAccepted = useAnimation();
	useEffect(() => {
		controlHeightAccepted.set({
			height: 42
		});
	}, [controlHeightAccepted]);

  const refreshUserMemberships = () => {
    getUserMemberships({
			username: props.userData.username, 
			password_prehash: props.userData.password_pre_hash, 
			subset: "all", 
			set_value: (result: membershipType[]) => {
				props.setUserData({...props.userData, memberships: result});
			}
	})
  };

  const openOrganizationControls = (membership : membershipType) => {
    setSelectedOrganization(membership);
    setOrganizationPanel("ControlOrganization");
  };

  const resolveInvite = (organization_id : number | string, choice : boolean) => {
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
    const invites : membershipType[] = [], accepted_memberships : membershipType[] = [];
		if (props.userData.memberships !== undefined) {
			for (const [key, value] of Object.entries(props.userData.memberships)) {
				key;
				if (value.invite_still_open) {
					invites.push(value);
				} else {
					accepted_memberships.push(value);
				}
			}
			setAcceptedMemberships(accepted_memberships);
			setMembershipInvites(invites);
		}
  }, [props.userData]);


  useEffect(() => {
		controlHeightInvites.start({
			height: (openedInvites && membershipInvites.length > 0)?(membershipInvites.length*45+48):42,
			transition: { duration: 0.4 }
		});
  }, [openedInvites, membershipInvites, controlHeightInvites]);

  useEffect(() => {
		controlHeightAccepted.start({
			height: (openedAccepted && acceptedMemberships.length > 0)?(acceptedMemberships.length*45+48):42,
			transition: { duration: 0.4 }
		});
  }, [openedAccepted, acceptedMemberships, controlHeightAccepted]);

  return (
    <div style={{
			display: "flex",
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <div style={{display: "flex", flexDirection: 'column', height: '100%', width: '100%', alignItems: 'center'}}>
        <div id="ChatHeader" style={{
					display: "flex",
          width: "100%",
          height: 40,
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
        </div>
        <div id="ContentBody" style={{
					display: "flex",
          flex: 1,
          width: "100%",
          backgroundColor: "#23232D",
          flexDirection: 'row',
          alignItems: 'center'
        }}>
          <div style={{
						display: "flex",
            height: "100%",
            width: 320,
            flexDirection: 'column',
            paddingLeft: 20,
          }}>
            <span style={{
              width: '100%',
              textAlign: 'center',
              // textAlignVertical: 'center',
              height: 40,
              // fontFamily: 'Inter-Regular',
              fontSize: 28,
              color: '#E8E3E3',
							// paddingBottom: 10,
            }}>
              {"Memberships"}
            </span>
            <div style={{
							paddingTop: 20,
							display: "flex",
							flexDirection: "column",
              width: '100%',
              flex: 1,
            }}>
              <div style={{paddingBottom: 10, maxWidth: '100%'}}>
                <AnimatedPressable style={{
									display: "flex",
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
                    <div style={{paddingRight: 5}}>
                      <Icon.Plus size={20} color="#E8E3E3" />
                    </div>
                    <div style={{alignSelf: 'center', justifyContent: 'center'}}>
                    <span style={{
                      // width: '100%',
                      // height: '100%',
                      // fontFamily: 'Inter-Regular',
                      fontSize: 14,
                      color: '#E8E3E3',
                      paddingTop: 1
                    }}>{"New Organization"}</span>
                    </div>
                </AnimatedPressable>
              </div>
              <motion.div animate={controlHeightInvites} style={{
                width: '100%',
								display: "flex",
                flexDirection: 'column',
                borderRadius: 20,
                // justifyContent: 'space-around',
                // paddingVertical: 10,
                paddingTop: 8,
                // height: boxHeightInvites.current,
                // alignSelf: 'center',
              }}>
                <div style={{
									display: "flex",
                  // height: 200,
                  flexDirection: 'row',
                  // paddingRight: 16,
                  // paddingLeft: 12,
                  paddingBottom: 8,
                  // alignItems: 'center',
                  // justifyContent: 'space-around',
                }}>
                  <div style={{
										display: "flex",
                    // width: '83%',
                    flex: 1,
                    flexDirection: 'column',
                    justifyContent: 'center',
                    // paddingLeft: 9,
                  }}>
                    <span style={{
                      fontSize: 16,
                      color: "#E8E3E3",
                      textAlign: 'left',
                      // textAlignVertical: 'center',
                      height: 25,
                      width: '100%',
                    }}
                    >
                      {"Invitations"}
                    </span>
                  </div>
                  <div style={{display: "flex", flexDirection: 'column', justifyContent: 'center'}}>
                    <Button style={{padding: 2, width: 30, height: 30}} variant={"ghost"} 
										onClick={() => {
											setOpenedInvites(opened => !opened);
										}}>
                      <Icon.ChevronDown
                        size={24} 
                        color={"#E8E3E3"}
                        style={{
                          transform: openedInvites?"rotate(0deg)":"rotate(90deg)"
                        }}
                      />
                    </Button>
                  </div>
                </div>
                
                <ScrollArea style={{
									display: "flex",
									flexDirection: "row",
									paddingBottom: 5,
								}}>
                  {membershipInvites.map((value : membershipType, index: number) => (
										<>
                    <HoverEntryGeneral key={index} title={value.organization_name}>
                      <AnimatedPressable onPress={() => {
                        resolveInvite(value.organization_id, true);
                      }} style={{paddingRight: 10}}>
                        <Icon.Check size={16} color={'#E8E3E3'}/>
                      </AnimatedPressable>
                      <AnimatedPressable onPress={() => {
                        resolveInvite(value.organization_id, false);
                      }} style={{paddingRight: 10}}>
                        <Icon.X size={16} color={'#E8E3E3'}/>
                      </AnimatedPressable>
                    </HoverEntryGeneral>
										</>
                  ))}
                </ScrollArea>
                
              </motion.div>
              <motion.div animate={controlHeightAccepted} style={{
                width: '100%',
								display: "flex",
                flexDirection: 'column',
                borderRadius: 20,
                // justifyContent: 'space-around',
                // paddingVertical: 10,
                paddingTop: 8,
                // height: boxHeightAccepted.current,
                // alignSelf: 'center',
              }}>
                <div style={{
                  // height: 200,
									display: "flex",
                  flexDirection: 'row',
                  // paddingRight: 16,
                  // paddingLeft: 12,
                  paddingBottom: 8,
                  // alignItems: 'center',
                  // justifyContent: 'space-around',
                }}>
                  <div style={{
                    // width: '83%',
										display: "flex",
                    flex: 1,
                    flexDirection: 'column',
                    justifyContent: 'center',
                    // paddingLeft: 9,
                  }}>
                    <span style={{
                      fontSize: 16,
                      color: "#E8E3E3",
                      textAlign: 'left',
                      // textAlignVertical: 'center',
                      height: 25,
                      width: '100%',
                    }}>
                      {"Organizations"}
                    </span>
                  </div>
                  <div style={{flexDirection: 'column', justifyContent: 'center'}}>
                    <Button style={{padding: 2, width: 30, height: 30}} variant={"ghost"}
                      onClick={() => {
                        setOpenedAccepted(opened => !opened);
                      }}
                    >
                      <Icon.ChevronDown
                        size={24} 
                        color={"#E8E3E3"}
                        style={{
                          transform: openedAccepted?"rotate(0deg)":"rotate(90deg)"
                        }}
                      />
                    </Button>
                  </div>
                </div>
                
                <ScrollArea style={{
									paddingBottom: 5,
								}}>
                  {acceptedMemberships.map((value : membershipType, index: number) => (
                    <AnimatedPressable key={index} onPress={() => {
                      openOrganizationControls(value);
                    }} style={{
											display: "flex",
                      flexDirection: 'row',
                      justifyContent: 'space-between',
                      width: '100%'
                    }}>
                      <span style={{
                        maxWidth: "100%",
                        textAlign: 'center',
                        // textAlignVertical: 'center',
                        alignSelf: 'flex-start',
                        // fontFamily: 'Inter-Regular',
                        fontSize: 14,
                        color: '#E8E3E3',
                        paddingLeft: 4
                      }}>
                        {value.organization_name}
                      </span>
                      <span style={{
                        maxWidth: "100%",
                        textAlign: 'center',
                        // textAlignVertical: 'center',
                        alignSelf: 'flex-start',
                        // fontFamily: 'Inter-Regular',
                        fontSize: 14,
                        color: '#4D4D56',
                      }}>
                        {value.role}
                      </span>
                    </AnimatedPressable>
                  ))}
                </ScrollArea>
                
              </motion.div>
            </div>
          </div>
          <div style={{
						display: "flex",
            flex: 1,
            height: '100%',
            justifyContent: 'center',
            alignContent: 'center'
          }}>
            {(organizationPanel !== undefined) && (
              (organizationPanel === "CreateOrganization")?(
                <div style={{
									display: "flex",
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column',
                  flex: 1,
                }}>
                  <div id={"OrganizationBox"} style={{
										display: "flex",
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexDirection: 'column',
                    borderRadius: 15,
                    // height: 400,
                    // width: 400,
                    backgroundColor: '#39393C',
                    paddingLeft: 25,
										paddingRight: 25,
                    paddingBottom: 25,
                    paddingTop: 15,
                  }}>
                    <div style={{display: "flex", flexDirection: "row"}}>
                      <div style={{display: "flex", flexDirection: "column"}}>
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
                          {"Create a New Organization"}
                        </span>
                        <div style={{
                          backgroundColor: '#E8E3E3',
                          height: 2,
                          paddingTop: 2,
                          borderRadius: 1,
                          width: '100%'
                        }}/>
                        <div style={{
                          flexDirection: 'row',
                          justifyContent: 'space-between',
                          paddingBottom: 10,
                        }}>
                        </div>
                        <div style={{paddingBottom: 10}}>
													<Input
														// type="password"
														spellCheck={false}
														placeholder="Name"
														value={createOrganizationName}
														onChange={(e) => {
															const val = e.target?.value;
															// setSerpKeyInput(val);
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
													<Input
														// type="password"
														spellCheck={false}
														placeholder="Description"
														value={createOrganizationDescription}
														onChange={(e) => {
															const val = e.target?.value;
															// setSerpKeyInput(val);
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
                    
                    <AnimatedPressable style={{
                      width: '100%',
                      borderRadius: 10,
                      backgroundColor: '#7968D9',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }} onPress={createOrganization}>
                      <div style={{width: '100%'}}>
                      <span style={{
                        // fontFamily: 'Inter-Regular',
                        fontSize: 24,
                        color: '#E8E3E3',
                        alignSelf: 'center',
                        padding: 10,
                        width: '100%',
                      }}>
                        {"Create Organization"}
                      </span>
                      </div>
                    </AnimatedPressable>
                  </div>
                </div>
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
          </div>
        </div>
      </div>
    </div>
  );
}