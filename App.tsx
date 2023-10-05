// import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import EventSource from "./src/react-native-server-sent-events";
import { useFonts } from 'expo-font';
import {
  Platform,
  View,
  Text,
  StyleSheet,
  useWindowDimensions,
  Button,
  Pressable,
  TextInput,
  StatusBar,
  Animated,
  Easing
} from 'react-native';
// import { NavigationContainer } from '@react-navigation/native';
import { Feather } from '@expo/vector-icons';
// import { createStackNavigator } from '@react-navigation/stack';
import {
  createDrawerNavigator,
  DrawerContentScrollView,
  DrawerContent,
  DrawerItemList,
  DrawerItem,
} from '@react-navigation/drawer';
// import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ScrollView } from 'react-native-gesture-handler';
// import { createDrawerNavigator } from "@react-navigation/drawer";
import { NavigationContainer } from "@react-navigation/native";
import Uploady, { useItemProgressListener } from '@rpldy/uploady';
import UploadButton from "@rpldy/upload-button";
import ChatWindow from './src/pages/ChatWindow';
import Sidebar from './src/components/Sidebar';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import * as SplashScreen from 'expo-splash-screen';
import testTextMate from './src/tests/testTextMate';
import MarkdownTestPage from './src/markdown/MarkdownTestPage';


function HomeScreen({ navigation }) {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <Button onPress={navigation.openDrawer} title="Open navigation drawer" />
      <Button
        onPress={() => navigation.navigate("Notifications")}
        title="Go to notifications"
      />
    </View>
  );
}

function NotificationsScreen({ navigation }) {
  return (
    <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
      <Button onPress={navigation.openDrawer} title="Open navigation drawer" />
      <Button onPress={() => navigation.goBack()} title="Go back home" />
    </View>
  );
}

function CustomDrawerContent(props: any) {
  const width = useWindowDimensions().width;
  const height = useWindowDimensions().height;
  // console.log(useWindowDimensions());
  const big_array = Array(100).fill(0);

  return (
    // <DrawerContent>
      <View {...props}>
        <View style={{backgroundColor: "#0000FF", height: height, flexDirection: 'column', padding: 0}}>
          <View style={{
            flex: 5,
            backgroundColor: 'powderblue',
          }}>
            <ScrollView>
              {big_array.map((e) => (
                <Text>Hello</Text>
              ))}
            </ScrollView>
          </View>
          <View style={{backgroundColor: "#00FF00", flex: 1}}>

            <ScrollView>
              {big_array.map((e) => (
                <Text>Goodbye</Text>
              ))}
            </ScrollView>
          </View>
        </View>
      </View>
    /* </DrawerContent> */
  );
}

type pageID = "ChatWindow" | "MarkdownTestPage";

function AppWeb() {
  const [sidebarOpened, setSidebarOpened] = useState(true);
  const sidebarWidth = useRef(new Animated.Value(320)).current;

  // const Stack = createStackNavigator();
  const [pageNavigate, setPageNavigate] = useState<pageID>("ChatWindow");

  const toggle_sidebar = () => {
    setSidebarOpened(sidebarOpened => !sidebarOpened);
  };

  useEffect(() => {
    Animated.timing(sidebarWidth, {
      toValue: sidebarOpened?320:0,
      // toValue: opened?Math.min(300,(children.length*50+60)):50,
      duration: 400,
			easing: Easing.elastic(0),
      useNativeDriver: false,
    }).start();
  }, [sidebarOpened]);



  return (
    <>
      <Animated.View id="rootView" style={{
        flexDirection: "row",
        width: "100vw",
        height: "100vh",
        backgroundColor: "#FF0000",
      }}>
        <Animated.View style={{elevation: sidebarOpened?1:0,}}>
          <Animated.View
            style={{
              width: sidebarWidth,
            }}
            >
            <View style={{width: 320}}>
              <Sidebar toggleSideBar={toggle_sidebar}/>
            </View>
          </Animated.View>
        </Animated.View>
        {(pageNavigate === "ChatWindow") && (
          <ChatWindow toggleSideBar={toggle_sidebar} sidebarOpened={sidebarOpened}/>
        )}
        {(pageNavigate === "MarkdownTestPage") && (
          <MarkdownTestPage toggleSideBar={toggle_sidebar} sidebarOpened={sidebarOpened}/>
        )}
      </Animated.View>
    </>
  );
}

function AppMobile() {
  

  // return (
  //   <View style={{height: "100vh", width: "100vw", backgroundColor: "#FF0000", alignItems: 'center', justifyContent: 'center'}}>
  //     <Text style={{
  //       fontSize: 30,
  //       width: 400,
  //       height: 400,
  //       color: 'black',
  //       fontFamily: 'YingHei4'
  //     }}>
  //       {"Hello there 马云1964年9月10日—[8]，祖籍浙江嵊县，生于浙江杭州，中国大陆企业家，中国共产党党员。曾为亚洲首富、阿里巴巴集团董事局主席（董事长）[9]，淘宝网、支付宝的创始人，大自然保護協會大中華理事會名譽主席，華誼兄弟董事。目前擔任香港大學經管學院名譽教授，所在的學術領域為「管理及商業策略」，以及擔任東京大學所屬研究機構東京學院的客座教授，研究方向為「可持续农业和粮食生产」。"}
  //     </Text>
  //   </View>
  // );

  const Drawer = createDrawerNavigator();
  return (
    <NavigationContainer>
      <Drawer.Navigator initialRouteName='NotificationsScreen'
        drawerContent={(props) => <Sidebar {...props} style={{backgroundColor: "black"}}/>} 
        screenOptions={{
          drawerStyle: {width: 320, borderRightWidth: 0},
          overlayColor: 'transparent',
        }}
        >
        <Drawer.Screen name="ChatWindow" component={ChatWindow} options={{
          headerShown: false, 
          drawerType: Platform.select({
            web: 'back',
            default: 'slide'
          }),
        }}
        />
        <Drawer.Screen name="HomeScreen" component={HomeScreen} options={{
          headerShown: false, 
          drawerType: Platform.select({
            web: 'permanent',
            default: 'front'
          })
        }}/>
        <Drawer.Screen name="NotificationsScreen" component={NotificationsScreen} options={{
          headerShown: false, 
          drawerType: Platform.select({
            web: 'permanent',
            default: 'front'
          })
        }}/>
        {/* <Drawer.Screen name="StackNav" component={TabNav} options={{headerShown: false}}/> */}
      </Drawer.Navigator>
    </NavigationContainer>
  )
}

export default function App() {
  const [fontsLoaded] = useFonts({
    "YingHei2": require("./assets/fonts/MYingHei/MYingHeiHK-W2.otf"),
    "YingHei3": require("./assets/fonts/MYingHei/MYingHeiHK-W3.otf"),
    "YingHei4": require("./assets/fonts/MYingHei/MYingHeiHK-W4.otf"),
    "YingHei5": require("./assets/fonts/MYingHei/MYingHeiHK-W5.otf"),
    "YingHei7": require("./assets/fonts/MYingHei/MYingHeiHK-W7.otf"),
    "YingHei8": require("./assets/fonts/MYingHei/MYingHeiHK-W8.otf"),
    "YingHei9": require("./assets/fonts/MYingHei/MYingHeiHK-W9.otf"),
    "Consolas": require("./assets/fonts/Consolas/Consolas.otf"),
    "Consolas-Bold": require("./assets/fonts/Consolas/Consolas-Bold.otf"),
    "Consolas-Italic": require("./assets/fonts/Consolas/Consolas-Italic.otf"),
    "Consolas-BoldItalic": require("./assets/fonts/Consolas/Consolas-BoldItalic.otf"),
    "Inter-Black": require("./assets/fonts/Inter/Inter-Black.otf"),
    "Inter-Bold": require("./assets/fonts/Inter/Inter-Bold.otf"),
    "Inter-ExtraBold": require("./assets/fonts/Inter/Inter-ExtraBold.otf"),
    "Inter-ExtraLight": require("./assets/fonts/Inter/Inter-ExtraLight.otf"),
    "Inter-Light": require("./assets/fonts/Inter/Inter-Light.otf"),
    "Inter-Medium": require("./assets/fonts/Inter/Inter-Medium.otf"),
    "Inter-Regular": require("./assets/fonts/Inter/Inter-Regular.otf"),
    "Inter-SemiBold": require("./assets/fonts/Inter/Inter-SemiBold.otf"),
    "Inter-Thin": require("./assets/fonts/Inter/Inter-Thin.otf"),
  });

  useEffect(() => {
    async function prepare() {
      await SplashScreen.preventAutoHideAsync();
    }
    prepare();
  }, []);

  if (!fontsLoaded) {
    return undefined;
  } else {
    SplashScreen.hideAsync();
  }

  const is_web = Platform.select({web: true, default: false});
  const AppGet = is_web?AppWeb:AppMobile;
  testTextMate();
  return (
    <AppGet/>
  );
}