// import { useState } from 'react'
import './App.css'
import { useEffect, useMemo, useState } from 'react'
// import { Button } from './components/ui/button'
import { ThemeProvider } from "@/components/theme-provider"
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import TestPage1 from '@/components/pages/test-page-1'
import TestPage2 from '@/components/pages/test-page-2'
import LoginPage from '@/components/pages/login-page'
// import TestTextArea from './components/pages/test-text-area'
import { AnimatePresence, motion, useAnimation } from "framer-motion";
import { userDataType, pageID, selectedCollectionsType, timeWindowType } from '@/globalTypes';
import ChatWindow from '@/components/pages/chat-window';
import TestScrollPage1 from '@/components/pages/test-scroll-page-1';
import TestFramerAnimation from '@/components/pages/test-framer-animation'
import Sidebar from '@/components/sidebar/sidebar'
import ChatWindowToolchain from './components/pages/chat-window-toolchains'

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

  return (
    <div style={{
      width: "100%", 
      height: "100%", 
      display: "flex", 
      flexDirection: "row"
      }}>
      {(userData !== undefined) && (
        <motion.div animate={controlsSidebarWidth} >
          <div style={{
            width: 320,
            height: "100vh",
            position: "absolute",
            zIndex: 0
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
        </motion.div>
      )}
      <div style={{zIndex: 1, flex: 1, display: "flex", height: "100vh"}} className='bg-background'>
        <Routes location={location} key={location.pathname}>
          <Route index element={<LoginPage setUserData={setUserData}/>}/>
          <Route path="/login_page" element={<LoginPage setUserData={setUserData}/>}/>
          <Route path="/test_page_1" element={<TestPage1/>}/>
          <Route path="/test_page_2" element={<TestPage2/>}/>
          <Route path="/test_scroll_page" element={<TestScrollPage1/>}/>
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
