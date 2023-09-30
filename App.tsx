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

function AppWeb() {
  const [sidebarOpened, setSidebarOpened] = useState(true);
  const sidebarWidth = useRef(new Animated.Value(320)).current;

  const Stack = createStackNavigator();

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
        backgroundColor: "#FF0000"
      }}>
        <Animated.View
          style={{
            width: sidebarWidth
          }}
          >
          <View style={{width: 320}}>
            <Sidebar toggleSideBar={toggle_sidebar}/>
          </View>
        </Animated.View>
        <ChatWindow toggleSideBar={toggle_sidebar}/>
      </Animated.View>
    </>
  );
}

function AppMobile() {
  const Drawer = createDrawerNavigator();
  return (
    <NavigationContainer>
      <Drawer.Navigator initialRouteName='ChatWindow'
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
  const is_web = Platform.select({web: true, default: false});
  const AppGet = is_web?AppWeb:AppMobile;
  return (
    <AppGet/>
  );
}