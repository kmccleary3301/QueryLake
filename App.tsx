// import * as React from 'react';
import { useState, useEffect, useRef } from 'react';
import EventSource from "./src/react-native-server-sent-events";
// import { useFonts } from 'expo-font';
import {
  Platform,
  View,
  Text,
  StyleSheet,
  useWindowDimensions,
  Button,
  Pressable,
  TextInput,
  StatusBar
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
import useFonts from './src/hooks/useFonts';
import AppLoading from 'expo-app-loading';

const platform = Platform.select({ios: 'mobile', android: 'mobile', web: 'web'});

import ChatWindowWeb from './src/pages/ChatWindowWeb';
import ChatWindowMobile from './src/pages/ChatWindowMobile';

const ChatWindow = (platform === "web")?ChatWindowWeb:ChatWindowMobile;
import Sidebar from './src/components/Sidebar';

const Drawer = createDrawerNavigator();


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

export default function App() {
  const [IsReady, SetIsReady] = useState(false);

  const LoadFonts = async () => {
    await useFonts();
  };


  if (!IsReady) {
    return (
      <AppLoading
        startAsync={LoadFonts}
        onFinish={() => SetIsReady(true)}
        onError={() => {}}
      />
    );
  }

  return (
    <NavigationContainer>
      <Drawer.Navigator initialRouteName='ChatWindow'
        drawerContent={(props) => <Sidebar {...props} />} >
        <Drawer.Screen name="ChatWindow" component={ChatWindow} options={{
          headerShown: false, 
          drawerType: Platform.select({
            web: 'permanent',
            default: 'slide'
          })
        }}/>
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
  );
}