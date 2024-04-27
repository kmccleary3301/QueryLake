"use client";
import { Metadata } from "next"

import "public/registry/themes.css"
import { Announcement } from "@/components/inherited/announcement"
import {
  PageActions,
  PageHeader,
  PageHeaderDescription,
  PageHeaderHeading,
} from "@/components/inherited/page-header"
import { ThemeCustomizer } from "@/components/inherited/theme-customizer"
import { ThemeWrapper } from "@/components/inherited/theme-wrapper"
import { ThemesTabs } from "@/app/themes/tabs"
import { ScrollArea } from "@/registry/default/ui/scroll-area"
import { useContextAction } from "@/app/context-provider";
import { ComboBox } from "@/registry/default/ui/combo-box"
import CompactInput from "@/registry/default/ui/compact-input";
import { Button } from "@/registry/default/ui/button";
import { Send, Trash } from "lucide-react";
import { ChangeEvent, ChangeEventHandler, use, useEffect, useRef, useState } from "react";
import { modifyUserExternalProviders } from "@/hooks/querylakeAPI";
import { Input } from "@/registry/default/ui/input";

// export const metadata: Metadata = {
//   title: "Themes OG",
//   description: "Hand-picked themes that you can copy and paste into your apps.",
// }

export default function SettingsPage() {
  const {
    userData,
    setUserData,
  } = useContextAction();

  const [keyAvailable, setKeyAvailable] = useState(false);
  const [currentKeyInput, setCurrentKeyInput] = useState("");


  // useEffect(() => {
  //   console.log("Key Available:", keyAvailable);
  //   setCurrentKeyInput(keyAvailable?"...........":"");
  // }, [keyAvailable]);
  // useEffect(() => {console.log("User Data:", userData)}, [userData]);

  const [currentProvider, setCurrentProvider] = useState("");

  useEffect(() => {
    console.log("Current Provider:", currentProvider);
    if (userData) {
      console.log("Setting key");
      console.log("Providers:", userData.providers, "Current Provider:", currentProvider)
      const newKeyAvailable = userData.user_set_providers.includes(currentProvider);
      setKeyAvailable(newKeyAvailable);
      setCurrentKeyInput(newKeyAvailable?".......................................":"");
    }
  }, [currentProvider, userData?.providers]);

  useEffect(() => {
    console.log("User set providers:", userData?.user_set_providers);
  }, [userData?.user_set_providers]);



  return (
    <ScrollArea className="w-full h-screen">
      <div className="w-full flex flex-row justify-center">
        <div className="flex flex-col w-[85vw] md:w-[70vw]">
          <ThemeWrapper
            defaultTheme="zinc"
            className="relative flex flex-col items-start md:flex-row md:items-center gap-8"
          >
            <div className="w-full flex flex-col items-center">
              <PageHeader className="gap-8">
                <PageHeaderHeading className="hidden md:block">
                  Customize Your Settings
                </PageHeaderHeading>
                <PageHeaderHeading className="md:hidden">
                  User Settings
                </PageHeaderHeading>
                <PageActions>
                  <ThemeCustomizer />
                </PageActions>
              </PageHeader>
              <div className="space-y-6">
                <div className="space-y-2">
                  <div className="flex flex-row justify-between gap-6">
                    <h1 className="text-2xl h-auto flex flex-col justify-center">External Providers</h1>
                    <ComboBox 
                      values={(userData?.providers || []).map((e) => ({value: e.toLowerCase(), label: e}))}
                      placeholder="Select Provider..."
                      searchPlaceholder="Search Providers..."
                      value={currentProvider.toLowerCase()}
                      onChange={(_, label) => setCurrentProvider(label)}
                    />
                  </div>
                </div>
                <div className="flex flex-row justify-between gap-2">
                  <Input
                    placeholder="Set Provider Key" 
                    type="password"
                    className="flex-grow"
                    onChange={(e : ChangeEvent<HTMLInputElement>) => {
                      setCurrentKeyInput(e.target.value);
                    }}

                    // defaultValue={keyAvailable?"...........":""}
                    value={currentKeyInput}
                  />
                  <div className="flex flex-row gap-2">
                  <Button 
                    className="p-0 pt-[1px] pr-[0px] m-0 h-10 w-10"
                    variant="ghost"
                    type="submit" 
                    size="icon"
                    onClick={() => {
                      modifyUserExternalProviders({
                        auth: userData?.auth as string,
                        update: {[`${currentProvider}`]: currentKeyInput},
                        onFinish: (success : boolean) => {
                          if (success) {
                            setKeyAvailable(true);
                            if (userData) {
                              setUserData({
                                ...userData,
                                user_set_providers: [
                                  ...userData.user_set_providers.filter((e) => e !== currentProvider), 
                                  currentProvider
                                ]
                              });
                            }
                          }
                        }
                      })
                    }}
                  >
                    <Send className="h-4 w-4 text-primary" />
                  </Button>
                  <Button variant={"ghost"} className="w-10 h-10 p-0 m-0" onClick={() => {
                    modifyUserExternalProviders({
                      auth: userData?.auth as string,
                      delete: [currentProvider],
                      onFinish: (success : boolean) => {
                        console.log("Delete result:", success);
                        if (success) {
                          setKeyAvailable(false);
                          if (userData) {
                            setUserData({
                              ...userData,
                              user_set_providers: [
                                ...userData.user_set_providers.filter((e) => e !== currentProvider)
                              ]
                            });
                          }
                        }
                      }
                    })
                  }}>
                    <Trash className="w-4 h-4 text-primary"/>
                  </Button>
                  </div>
                </div>
              </div>
            </div>
          </ThemeWrapper>
          
          {/* <ThemesTabs /> */}
        </div>
      </div>
    </ScrollArea>
  )
}
