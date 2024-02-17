// import { useState } from 'react'
import './App.css'
import { useEffect, useMemo, useState, Dispatch, SetStateAction } from 'react'
// import { Button } from './components/ui/button'
import { ThemeProvider } from "@/components/theme-provider"
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import TestPage1 from '@/components/pages/test-page-1'
import TestPage2 from '@/components/pages/test-page-2'
import LoginPage from '@/components/pages/login-page'
// import TestTextArea from './components/pages/test-text-area'
import { AnimatePresence, motion, useAnimation } from "framer-motion";
import { userDataType, pageID, selectedCollectionsType, timeWindowType } from '@/typing/globalTypes';
// import ChatWindow from '@/components/pages/chat-window';
import TestScrollPage1 from '@/components/pages/test-scroll-page-1';
import TestFramerAnimation from '@/components/pages/test-framer-animation';
import Sidebar from '@/components/sidebar/sidebar';
import ChatWindowToolchain from './components/pages/chat-window-toolchains/chat-window-toolchains';
import TestWebSockets from './components/pages/test-websocket';
// import AnimatedPressable from './components/manual_components/animated-pressable';
import * as Icon from 'react-feather';
import { Button } from './components/ui/button';
import UserSettings from './components/pages/user-settings';
import HuggingFaceRemodel from './components/pages/test-huggingface-remodel';
// import OrganizationControls from './components/manual_components/organization-controls';
import OrganizationManager from './components/pages/organization-manager'

// type userDataType = {
//   username: string,
//   password_pre_hash: string,
//   memberships: object[],
//   is_admin: boolean,
//   serp_key?: string,
//   available_models?: {
//     default_model: string,
//     local_models: string[],
//     external_models: object
//   },
//   available_toolchains: toolchainCategory[],
//   selected_toolchain: toolchainEntry
// };



function MainContent() {

  // const pagesWithSidebarDisabled = ["login_page"];
  
  
  const [userData, setUserData] = useState<userDataType>();
  const pagesWithSidebarDisabled = useMemo(() => ["login_page"], []);
  const [chatHistory, setChatHistory] = useState<timeWindowType[]>([]);
  const [pageNavigate, setPageNavigate] = useState<pageID>("LoginPage");
  // const [userData, setUserData] = useState<userDataType>();
  // const transitionOpacity = useRef(new Animated.Value(1)).current;
  const [pageNavigateDelayed, setPageNavigateDelayed] = useState<pageID>("LoginPage");
  const [sidebarOpened, setSidebarOpened] = useState(false);
  const [pageNavigateArguments, setPageNavigateArguments] = useState("");
  const [refreshSidePanel, setRefreshSidePanel] = useState<string[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<selectedCollectionsType>(new Map<string, boolean>([]));


  const location = useLocation();
  const [isSidebarDisabled, setSidebarDisabled] = useState(pagesWithSidebarDisabled.includes(location.pathname.replace('/', '')));
  
  useEffect(() => {
    console.log("location:", location.pathname.replace('/', ''));
    setSidebarDisabled(pagesWithSidebarDisabled.includes(location.pathname.replace('/', '')));

  }, [location.pathname, setSidebarDisabled, pagesWithSidebarDisabled]);
  
  
  const toggle_sidebar = () => { setSidebarOpened(sidebarOpened => !sidebarOpened); };
  // const location = useLocation();

  useEffect(() => {
    console.log("userdata:", userData)
  }, [userData]);

  const controlsSidebarWidth = useAnimation();

  useEffect(() => {
		controlsSidebarWidth.set({
			width: 0
		});
	}, [controlsSidebarWidth]);

  // const testWidthSidebar = useMotionValue(0);
  useEffect(() => {
    console.log("sidebarOpened:", sidebarOpened);

    const sidebar_available = (userData !== undefined && !isSidebarDisabled);

		controlsSidebarWidth.start({
			width: (sidebarOpened && sidebar_available)?320:0,
			transition: { duration: 0.4 }
		});
	}, [controlsSidebarWidth, sidebarOpened, userData, isSidebarDisabled]);

  
	const controlSidebarButtonOffset = useAnimation();

  useEffect(() => {
    controlSidebarButtonOffset.set({
      zIndex: 2,
      opacity: 1
    });
  }, [controlSidebarButtonOffset]);

  useEffect(() => {
		controlSidebarButtonOffset.start({
			// translateX: sidebarOpened?-320:0,
      opacity: sidebarOpened?0:1,
			transition: { delay: sidebarOpened?0:0.4, duration: sidebarOpened?0:0.6 }
		});
  }, [sidebarOpened, controlSidebarButtonOffset]);


  return (
    <div style={{
      width: "100%", 
      height: "100%", 
      display: "flex", 
      flexDirection: "row",
      backgroundColor: "#23232D",
      zIndex: 0,
      position: "relative"
      }}>
      {(userData !== undefined) && (
        <>
        <motion.div id="SIDEBARBUTTON" style={{paddingTop: 4, paddingLeft: 10,
          position: "absolute",
          width: 30,
          height: 30,
          zIndex: sidebarOpened?-2:2,
          // backgroundColor: "#FF0000",
          translateX: 0
        }} 
        animate={controlSidebarButtonOffset}
        >
          <Button variant={"ghost"} style={{padding: 2, borderRadius: 5, paddingLeft: 8, paddingRight: 8}} onClick={toggle_sidebar}>
            <Icon.Sidebar size={24} color="#E8E3E3" />
          </Button> 

        </motion.div>
        {/* <motion.div id="Hellooooo" style={{zIndex: 3}} animate={controlsSidebarWidth} > */}
        <motion.div style={{}} animate={controlsSidebarWidth} >
          <div style={{
            width: 320,
            height: "100vh",
            // position: "relative",
            // zIndex: 2
          }}>
            <div style={{
              // zIndex: 2,
              backgroundColor: "#FF0000",
            }}>
              <Sidebar
                // userData={userData}
                // pageNavigateArguments={pageNavigateArguments}
                // setPageNavigateArguments={setPageNavigateArguments}
                toggle_sideBar={toggle_sidebar} 
                user_data={userData}
                set_page_navigate={setPageNavigate} 
                set_page_navigate_arguments={setPageNavigateArguments}
                refresh_side_panel={refreshSidePanel}
                set_refresh_side_panel={setRefreshSidePanel}
                page_navigate_arguments={pageNavigateArguments}
                set_selected_collections={setSelectedCollections}
                selected_collections={selectedCollections}
                set_user_data={setUserData}
                chat_history={chatHistory}
                set_chat_history={setChatHistory}
              />
            </div>
            {/* <div
              style={{
                translate: 320,
                position: "absolute",
                width: 30,
                height: 30,
                backgroundColor: "#FF0000",
                zIndex: 5,
              }}
            /> */}
            {/* <motion.div id="SIDEBARBUTTON" style={{paddingTop: 4, paddingLeft: 10, zIndex: 5,
              position: "absolute",
              width: 30,
              height: 30,
              backgroundColor: "#FF0000",
              translateX: 320
            }} 
            // animate={controlSidebarButtonOffset}
            >
              <Button variant={"ghost"} style={{padding: 2, borderRadius: 5, paddingLeft: 8, paddingRight: 8}} onClick={toggle_sidebar}>
                <div style={{}}>
                <Icon.Sidebar size={24} style={{}} color="#E8E3E3" />
                </div>
              </Button> 

            </motion.div> */}
          </div>
        </motion.div>
        {/* </motion.div> */}
        </>
      )}
      <div style={{zIndex: 1, flex: 1, display: "flex", height: "100vh"}} className='bg-background'>
        
        {/* <motion.div style={{backgroundColor: "#FF0000", position: "absolute", paddingTop: 4, paddingLeft: 10, zIndex: 5}} animate={controlSidebarButtonOffset}>
          <Button variant={"ghost"} style={{padding: 2, borderRadius: 5, paddingLeft: 8, paddingRight: 8, zIndex: 5}} onClick={toggle_sidebar}>
            <Icon.Sidebar size={24} style={{zIndex: 5}} color="#E8E3E300" />
          </Button> 
        </motion.div> */}
        <Routes location={location} key={location.pathname}>
          <Route index element={<LoginPage setUserData={setUserData}/>}/>
          <Route path="/login_page" element={<LoginPage setUserData={setUserData}/>}/>
          <Route path="/test_page_1" element={<TestPage1/>}/>
          <Route path="/test_page_2" element={<TestPage2/>}/>
          <Route path="/test_scroll_page" element={<TestScrollPage1/>}/>
          <Route path="/test_websocket" element={<TestWebSockets/>}/>
          <Route path="/hf_test" element={<HuggingFaceRemodel/>}/>
          <Route path="/organization_manager" element={
            <>
              {(userData !== undefined) && (
                <OrganizationManager
                  // toggleSideBar={toggleSideBarOpened} 
                  sidebarOpened={sidebarOpened}
                  userData={userData}
                  setUserData={setUserData as Dispatch<SetStateAction<userDataType>>}
                />
              )}
            </>
          }/>
          <Route path="/user_settings" element={
           <>
            {(userData !== undefined) && (
              <UserSettings
                userData={userData}
                setUserData={setUserData}
              />
            )}
          </>
          }/>
          <Route path="/test_animation" element={<TestFramerAnimation/>}/>
          {/* <Route path="/chat" element={
            <>
              {(userData !== undefined) && (

                <ChatWindow
                  sidebarOpened={sidebarOpened}
                  userData={userData}
                  pageNavigateArguments={pageNavigateArguments}
                  setRefreshSidePanel={setRefreshSidePanel}
                  selectedCollections={selectedCollections}
                  toggleSideBar={toggle_sidebar}
                />
              )}
            </>
          }/> */}
          <Route path="/chat" element={
            <>
              {(userData !== undefined) && (

                <ChatWindowToolchain
                  sidebarOpened={sidebarOpened}
                  userData={userData}
                  pageNavigateArguments={pageNavigateArguments}
                  setRefreshSidePanel={setRefreshSidePanel}
                  selectedCollections={selectedCollections}
                  toggleSideBar={toggle_sidebar}
                />
              )}
            </>
          }/>
          {/* <Route path="/test_text_area" element={<TestTextArea/>}/> */}
        </Routes>
      </div>
    </div>
  )
}

function App() {
  // ...

  return (
    <BrowserRouter>
      <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
        <AnimatePresence mode='popLayout'>
          <motion.div
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            <MainContent />
          </motion.div>
        </AnimatePresence>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App
