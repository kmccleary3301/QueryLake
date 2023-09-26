import * as Font from "expo-font";
 
const useFonts = async () => {
    await Font.loadAsync({
        'YingHei': Font.load('../../assets/fonts/MYingHeiHK-W4.otf'),
    });
};

export default useFonts;