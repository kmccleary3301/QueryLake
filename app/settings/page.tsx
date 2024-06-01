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
import { ComboBox, ComboBoxScroll } from "@/registry/default/ui/combo-box"
import CompactInput from "@/registry/default/ui/compact-input";
import { Button } from "@/registry/default/ui/button";
import { Send, Trash } from "lucide-react";
import { ChangeEvent, ChangeEventHandler, use, useEffect, useRef, useState } from "react";
import { modifyUserExternalProviders } from "@/hooks/querylakeAPI";
import { Input } from "@/registry/default/ui/input";
import { toast } from "sonner";
import MarkdownCodeBlock from "@/components/markdown/markdown-code-block";
import { SHIKI_THEMES } from "@/lib/shiki";
import { BundledTheme } from "shiki/themes";

// export const metadata: Metadata = {
//   title: "Themes OG",
//   description: "Hand-picked themes that you can copy and paste into your apps.",
// }

const DEMO_CODE = `
function torusMat(t, t_2, t_3) {
  "use strict";
  var phi = (1+Math.sqrt(5))/2;
  var ca = Math.cos(t);
  var sa = Math.sin(t);
  var cb = Math.cos(phi*t_2);
  var sb = Math.sin(phi*t_2);
  var c2b = Math.cos(2*phi*t_3);
  var s2b = Math.sin(2*phi*t_3);
  return [
      [ 1,      0,      0,   0, 0,      0,      0,    0 ],
      [ 0,  ca*cb,  sa*cb,   0, 0,  ca*sb,  sa*sb,    0 ],
      [ 0, -sa*cb,  ca*cb,   0, 0, -sa*sb,  ca*sb,    0 ],
      [ 0,      0,      0, c2b, 0,      0,      0, -s2b ],
      [ 0,      0,      0,   0, 1,      0,      0,    0 ],
      [ 0, -ca*sb, -sa*sb,   0, 0,  ca*cb,  sa*cb,    0 ],
      [ 0,  sa*sb, -ca*sb,   0, 0, -sa*cb,  ca*cb,    0 ],
      [ 0,      0,      0, s2b, 0,      0,      0,  c2b ],
  ];
}
`;

export default function SettingsPage() {
  const {
    userData,
    setUserData,
    shikiTheme,
    setShikiTheme,
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
        <div className="flex flex-col w-[85vw] md:w-[70vw] pb-[120px]">
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
                <div className="flex flex-col justify-center space-y-2">
                  <div className="flex flex-row justify-between gap-6">
                    <h1 className="text-2xl h-auto flex flex-col justify-center">Code Highlighter Theme</h1>
                    <ComboBox
                      values={SHIKI_THEMES}
                      placeholder="Select Code Theme..."
                      searchPlaceholder="Search Themes..."
                      value={shikiTheme}
                      onChange={(value, _) => setShikiTheme(value as BundledTheme)}
                    />
                  </div>
                  <MarkdownCodeBlock text={DEMO_CODE} lang="javascript"/>
                </div>
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
                          toast(success?"Key successfully saved":"Key could not be saved");
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
                        toast(success?"Key successfully deleted":"Key could not be deleted");
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
