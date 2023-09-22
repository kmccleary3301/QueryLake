import {
  View,
  Text,
} from 'react-native';
import Uploady, { useItemProgressListener } from '@rpldy/uploady';
import UploadButton from "@rpldy/upload-button";
// import Uploady from "@rpldy/uploady";
import UploadDropZone from "@rpldy/upload-drop-zone";
import { useState } from 'react';
import Dropzone from '../react-dropzone-uploader';
// import 'react-dropzone-uploader/dist/styles.css'
// import './TestUploadBox.css';

const LogProgress = () => {
  useItemProgressListener((item) => {
      console.log(`>>>>> (hook) File ${item.file.name} completed: ${item.completed}`);
  });
  return null;
}

// function get_data(dropzone_data: any) {
// 	console.log(dropzone_data);
// 	return (
// 		<Text>Hello</Text>
// 	);
// }


export default function TestUploadBox(props: any) {
  const [files, setFiles] = useState(null);

	const handleDragOver = (event) => {
    event.preventDefault();
    console.log("Hello");
  };

  const handleDragEnd = (event) => {
    event.preventDefault();
    console.log("Goodbye");
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setFiles(event.dataTransfer.files);
    console.log("Set files to:", event.dataTransfer.files);
    for (let file in event.dataTransfer.files) {
      let formData = new FormData()
      formData.append("file", file);
      fetch("http://localhost:5000/uploadfile", {method: "POST", body: formData});
    }
  };

  return (
    <div 
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDrop = {handleDrop}
      onDragLeave={handleDragEnd}
    >
      <View style={{backgroundColor: '#FF0000', width: 100, height: 100}}/>
    </div>
  )
}