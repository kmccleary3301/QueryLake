import {
  View,
  Text,
  useWindowDimensions,
} from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';
import TestUploadBox from '../TestUploadBox';


export default function Sidebar(props: any) {
	const width = useWindowDimensions().width;
	const height = useWindowDimensions().height;
	// console.log(useWindowDimensions());
	const big_array = Array(100).fill(0);

	const test_url_pointer = () => {
		const url = new URL("http://localhost:5000/uploadfile");
		url.searchParams.append("query", "test test test");
		return url.toString();
	};

	return (
		// <DrawerContent>
			<View {...props}>
				<View style={{
					backgroundColor: "#0000FF", 
					height: height, 
					flexDirection: 'column', 
					padding: 0, 
				}}>
					<View style={{
						flex: 5,
						backgroundColor: 'powderblue',
					}}>
						<ScrollView>
							<View style={{
								alignItems: 'center',
								justifyContent: 'center'
							}}>
							<TestUploadBox/>
							{big_array.map((e) => (
								<Text>Hello</Text>
							))}
							</View>
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

const styles={
	topContainer: {
		
	}
}