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
import ChatWindow from './src/pages/ChatWindow';
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

export default function App() {
  return (
    <NavigationContainer>
      <Drawer.Navigator initialRouteName='ChatWindow'
        drawerContent={(props) => <Sidebar {...props} style={{backgroundColor: "black"}}/>} >
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