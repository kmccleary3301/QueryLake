"use client";
import { Label } from "@/registry/default/ui/label"
import { Input } from "@/registry/default/ui/input"
import { Button } from "@/registry/default/ui/button"
import { Separator } from "@/registry/default/ui/separator"
import Link from "next/link"
import craftUrl from "@/hooks/craftUrl"
import { userDataType } from "@/types/globalTypes";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@/registry/default/ui/form"
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useForm } from "react-hook-form"
import { setCookie } from "@/hooks/cookies";
import { useRouter } from 'next/navigation';
import { toast } from "sonner"
import { useContextAction } from "@/app/context-provider";
import { get } from "http";
import CompactInput from "@/registry/default/ui/compact-input";

type login_results = {
  success: false,
  error: string
} | {
  success: true,
  result: userDataType
};

const formSchema = z.object({
  email: z.string().min(1, {
    message: "Username must be at least 1 character.",
  }),
  username: z.string().min(1, {
    message: "Username must be at least 1 character.",
  }),
	password: z.string().min(1, {
    message: "Password must be at least 1 character.",
  }),
  password_confirm: z.string().min(1, {
    message: "Password must be at least 1 character.",
  })
})


export default function Component() {
  const { setUserData, getUserData } = useContextAction();
  const router = useRouter();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      username: "",
			password: "",
      password_confirm: ""
    },
  })

  const setUserDataHook = (data: userDataType) => {
    setCookie({ key: "UD", value: data });
    setUserData(data);
    router.push("/home");
  }

  const setErrorMessage = (message: string) => {
    toast(message);
  }

  const signup = (values: z.infer<typeof formSchema>) => {
    if (values.password !== values.password_confirm) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    const url = craftUrl(`/api/add_user`, {
      "email": values.email,
      "username": values.username,
      "password": values.password,
    });
		
    fetch(url).then((response) => {
      console.log("Fetching");
      console.log(response);
      response.json().then((data : login_results) => {
        console.log("Got data:", data);
				if (data.success) {
					const result : userDataType = data.result;
          getUserData(result, () => {setUserDataHook(result);});
				} else {
					setErrorMessage(data.error as string);
				}
      });
    });
  }


  return (
    <div className="mx-auto max-w-sm space-y-2">
      <div className="text-center space-y-0 pb-3">
        <h1 className="text-2xl font-bold">Sign Up</h1>
      </div>
      <Form {...form}>
        <form className="space-y-4" onSubmit={() => {}}>
          <div className="space-y-0">
            {/* <Label htmlFor="username-email">Email</Label> */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CompactInput className="h-11" backgroundColor="#09090B" placeholder="Email" autoComplete="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <div className="space-y-0">
            {/* <Label htmlFor="username-email">Username</Label> */}
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CompactInput className="h-11" backgroundColor="#09090B" placeholder="Username" autoComplete="username" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <div className="space-y-0">
            {/* <Label htmlFor="password">Password</Label> */}
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CompactInput className="h-11" backgroundColor="#09090B" placeholder="Password" type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <div className="space-y-0">
            {/* <Label htmlFor="password">Confirm Password</Label> */}
            <FormField
              control={form.control}
              name="password_confirm"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <CompactInput className="h-11" backgroundColor="#09090B" placeholder="Confirm Password" type="password" autoComplete="new-password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <div className="pb-2">
            <Button className="w-full h-8" type="submit" onClick={form.handleSubmit(signup)}>
              Sign Up
            </Button>
          </div>
          {/* <Button variant="secondary" type="submit" style={{fontSize: 20}}>Submit</Button> */}
        </form>
      </Form>
			<Separator />
			<div className="space-y-2">
        <p className="text-center text-sm flex flex-row justify-center">
          Already have an account?
          <Link className="underline pl-2" href="/auth/login">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}

