import {
  View,
  Text,
  useWindowDimensions,
  Pressable,
} from 'react-native';
import { ScrollView, TextInput } from 'react-native-gesture-handler';
import { Feather } from '@expo/vector-icons';
import { useEffect, useState } from 'react';
import AnimatedPressable from './AnimatedPressable';

// SUCCESSFULLY TRANSLATED TO API SINGLE FILE

type selectedState = [
    selected: boolean,
    setSelected: React.Dispatch<React.SetStateAction<boolean>>,
];

type collectionType = {
  title: string,
  items: number,
  id?: number,
}

type toolchainEntry = {
  name: string,
  id: string,
  category: string
  chat_window_settings: object
};

type toolchainCategory = {
  category: string,
  entries: toolchainEntry[]
};

type userDataType = {
  username: string,
  password_pre_hash: string,
  available_toolchains: toolchainCategory[],
  selected_toolchain: toolchainEntry
};

type SidebarToolchainsProps = {
  userData: userDataType,
  setUserData: React.Dispatch<React.SetStateAction<userDataType>>,
}
  
export default function SidebarToolchains(props: SidebarToolchainsProps) {
  useEffect(() => {
    console.log("new userdata selected", props.userData);
  }, [props.userData]);

  useEffect(() => {
    console.log("Toolchains called");
  }, []);

  return (
    <>
      <ScrollView style={{
          width: '100%',
          paddingHorizontal: 22,
          paddingTop: 0,
        }}
        showsVerticalScrollIndicator={false}
      >
        {props.userData.available_toolchains.map((toolchain_category : toolchainCategory, category_index : number) => (
          <View key={category_index}>
            {(toolchain_category.entries.length > 0) && (
              <>
              <Text style={{
                width: "100%",
                textAlign: 'left',
                fontFamily: 'Inter-Regular',
                fontSize: 14,
                color: '#74748B',
                paddingBottom: 8,
                paddingTop: 8
              }}>
                {toolchain_category.category}
              </Text>
              {toolchain_category.entries.map((value : toolchainEntry, index : number) => (
                <View style={{paddingVertical: 5}} key={index}>
                  <AnimatedPressable
                    onPress={() => {
                      // props.setPageNavigateArguments("chatSession-"+value.hash_id);
                      // if (props.setPageNavigate) { props.setPageNavigate("ChatWindow"); }
                      props.setUserData({...props.userData, selected_toolchain: value});
                    }}
                  >
                    <View style={{
                      flexDirection: 'row'
                    }}>
                      <View style={{
                        width: 20,
                        height: 24
                      }}>
                        {(props.userData.selected_toolchain.id === value.id) && (
                          <Feather name="check" size={16} color="#7968D9"/>
                        )}
                      </View>
                      <Text style={{
                        width: 280,
                        textAlign: 'left',
                        // paddingLeft: 10,
                        fontFamily: 'Inter-Regular',
                        fontSize: 14,
                        height: 24,
                        color: '#E8E3E3'
                      }}>
                        {value.name}
                      </Text>
                    </View>
                  </AnimatedPressable>
                </View>
              ))}
              </>
            )}
          </View>
        ))}
      </ScrollView>
    </> 
  );
}