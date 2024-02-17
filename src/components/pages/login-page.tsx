import { useEffect, useState } from "react";
import craftUrl from "@/hooks/craftUrl";
import { getAvailableToolchains, getUserMemberships } from "@/hooks/querylakeAPI";
import { Button } from "@/components/ui/button";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { userDataType, availableToolchainsResult } from "@/typing/globalTypes";
 
const formSchema = z.object({
  username: z.string().min(1, {
    message: "Username must be at least 1 character.",
  }),
	password: z.string().min(1, {
    message: "Password must be at least 1 character.",
  })
})

type membershipType = {
	organization_id: string,
	organization_name: string,
	role: "owner" | "admin" | "member" | "viewer",
	invite_still_open: boolean,
};

// type toolchainEntry = {
//   name: string,
//   id: string,
//   category: string
//   chat_window_settings: object
// };

// type toolchainCategory = {
//   category: string,
//   entries: toolchainEntry[]
// };



// type userDataType = {
// 	username: string,
// 	password_pre_hash: string,
// 	memberships?: object[],
// 	is_admin?: boolean,
// 	serp_key?: string,
// 	available_models?: {
// 		default_model: string,
// 		local_models: string[],
// 		external_models: {
//       openai?: string[]
//     }
// 	},
// 	available_toolchains: toolchainCategory[],
//   selected_toolchain: toolchainEntry
// };

type login_results = {
  success: false,
  note: string
} | {
  success: true,
  result: {
    admin: boolean,
    password_single_hash: string,
    memberships: {
      organization_id: string,
      organization_name: string,
      role: "owner" | "admin" | "member" | "viewer",
      invite_still_open: boolean,
    }[],
    available_models: {
      default_model: string,
      local_models: string[],
      external_models: {
        openai?: string[]
      }
    }
  }
};

type LoginPageProps = {
	setPageNavigate?: React.Dispatch<React.SetStateAction<string>>,
	setUserData: React.Dispatch<React.SetStateAction<userDataType | undefined>>
};

export default function LoginPage(props : LoginPageProps) {
  const [modeIsLogin, setModeIsLogin] = useState(true); //A boolean for if you're signing up or logging in.
  const [errorMessage, setErrorMessage] = useState("");
	const navigate = useNavigate();

	const navigateDestination = "/chat";

	useEffect(() => {
		console.log("Changed error message to:", errorMessage);
	}, [errorMessage]);

	const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
			password: ""
    },
  })
 
  // 2. Define a submit handler.
  function onSubmit(values: z.infer<typeof formSchema>) {
    // Do something with the form values.
    // ✅ This will be type-safe and validated.
    console.log(values)
		if (modeIsLogin === true) {
			login(values);
		} else {
			signup(values);
		}
  }

	const login = (values: z.infer<typeof formSchema>) => {
    const url = craftUrl(`http://localhost:5173/api/login`, {
      "username": values.username,
      "password": values.password
    });
		
    fetch(url, {method: "POST"}).then((response) => {
      console.log("Fetching");
      console.log(response);
      response.json().then((data : login_results) => {
        console.log("Got data:", data);
				if (data.success) {
					getUserMemberships({
						username: values.username, 
						password_prehash: data.result.password_single_hash, 
						subset: "all", 
						set_value: (memberships : membershipType[]) => {
						getAvailableToolchains({
							userdata: {username: values.username, password_pre_hash: data.result.password_single_hash}, 
							onFinish: (result_tools : availableToolchainsResult | undefined) => {
							
								console.log("Result_tools:", result_tools);
								if (result_tools !== undefined) {

									props.setUserData({
										username: values.username, 
										password_pre_hash: data.result.password_single_hash,
										available_toolchains: result_tools.toolchains,
										selected_toolchain: result_tools.default,
										available_models: data.result.available_models,
										is_admin: data.result.admin,
										memberships: memberships
									});
									
									// CHANGE TO CHAT WINDOW
									navigate(navigateDestination);
								} else {
									setErrorMessage("Could not fetch Toolchains")
								}
							}
						});
					}
				});
					//Sign-up Successful
				} else {
					setErrorMessage(data.note);
				}
      });
    });
  }

	const signup = (values: z.infer<typeof formSchema>) => {
    const url = craftUrl(`/api/add_user`, {
			"username": values.username,
			"password": values.password
    });
    fetch(url, {method: "POST"}).then((response) => {
      console.log(response);
      response.json().then((data) => {
          console.log(data);
          try {
            if (data.success && data.result.account_made) {
              getUserMemberships({
								username: values.username, 
								password_prehash: data.result.password_single_hash, 
								subset: "all", 
								set_value: (memberships : membershipType[]) => {
                getAvailableToolchains({
									userdata: {username: values.username, password_pre_hash: data.result.password_single_hash}, 
									onFinish: (result_tools : availableToolchainsResult | undefined) => {
                  
										console.log("Result_tools:", result_tools);
										if (result_tools !== undefined) {

											props.setUserData({
												username: values.username, 
												password_pre_hash: data.result.password_single_hash,
												available_toolchains: result_tools.toolchains,
												selected_toolchain: result_tools.default,
												available_models: data.result.available_models,
												is_admin: data.result.admin,
												memberships: memberships
											});
											
											// CHANGE TO CHAT WINDOW
											navigate(navigateDestination);
										} else {
											setErrorMessage("Could not fetch Toolchains")
										}
									}
								});
							}
						});
              //Sign-up Successful
            } else {
							// setErrorMessage(data.note);
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
    <div style={{
			display: 'flex',
      flex: 1,
      flexDirection: "row",
      backgroundColor: "#23232D",
      alignItems: "center",
      justifyContent: "center",
      // width: "80vw"
      height: "100vh",
      // width: "100%",
    }}>
      <div style={{
        alignItems: 'center',
        justifyContent: 'center',
				display: 'flex',
        flexDirection: 'column'
      }}>
        <div style={{
            alignItems: 'center',
            justifyContent: 'center',
						display: 'flex',
            flexDirection: 'column',
            borderRadius: 15,
            // height: 400,
            backgroundColor: '#39393C',
            padding: 30,
        }}>
					<p style={{
							// fontFamily: "Inter-Regular",
							fontFamily: "Consolas",
							fontSize: 36,
							color: '#E8E3E3',
					}}>
							{modeIsLogin?"Sign In":"Sign Up"}
					</p>
					<div style={{paddingTop: 10, paddingBottom: 10}}>
						{(errorMessage.length > 0) && (
							<div style={{
								backgroundColor: '#FF0000',
								borderRadius: 5,
								padding: 10,
							}}>
								<p style={{
									// fontFamily: "Inter-Regular",
									fontSize: 14,
									color: '#E8E3E3'
								}}>
									{errorMessage}
								</p>
							</div>
						)}
					</div>
					<>
						<Form {...form}>
							<form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
								<FormField
									control={form.control}
									name="username"
									render={({ field }) => (
										<FormItem>
											<FormControl>
												<Input style={{
													width: 250,
													backgroundColor: '#17181D',
													borderRadius: 5,
												}} placeholder="Username" {...field} />
											</FormControl>
											<FormMessage />
										</FormItem>
									)}
								/>
								<FormField
									control={form.control}
									name="password"
									render={({ field }) => (
										<FormItem>
											<FormControl>
												<Input style={{
													width: 250,
													backgroundColor: '#17181D',
													borderRadius: 5,
												}} placeholder="Password" {...field} />
											</FormControl>
											<FormMessage />
										</FormItem>
									)}
								/>
								<Button variant="secondary" type="submit" style={{fontSize: 20}}>Submit</Button>
							</form>
						</Form>
					</>
					<div style={{paddingTop: 10}}>
						<Button variant="link" style={{paddingTop: 10}} onClick={() => {
							setModeIsLogin(modeIsLogin => !modeIsLogin);
						}}>
							<p style={{
								// fontFamily: "Inter-Regular",
								fontSize: 20,
								// color: '#E8E3E3'
							}}>
								{modeIsLogin?"Sign Up":"Log In"}
							</p>
						</Button>
					</div>
					<Button variant={"secondary"} onClick={() => {navigate("/test_websocket");}}>
						<p>{"Test Websocket"}</p>
					</Button>
        </div>
      </div>
    </div>
  );
}