import {
  View,
  Text,
} from 'react-native';
// import Uploady, { useUploady } from "@rpldy/uploady";
import createUploader, { UPLOADER_EVENTS } from "@rpldy/uploader";

import { useState } from 'react';
// import Dropzone from '../react-dropzone-uploader';
// import 'react-dropzone-uploader/dist/styles.css'
// import './TestUploadBox.css';
// import axios from 'axios';

// const LogProgress = () => {
//   useItemProgressListener((item) => {
//       console.log(`>>>>> (hook) File ${item.file.name} completed: ${item.completed}`);
//   });
//   return null;
// }

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
    let formData = new FormData()
    formData.append("file", event.dataTransfer.files[0]);
    const uploader = createUploader({ 
      destination: {method: 'POST', url: "http://localhost:5000/uploadfile", filesParamName: 'file'},
      autoUpload: true,
      grouped: true,
      
      //...
    });
    
    uploader.on(UPLOADER_EVENTS.ITEM_START, (item) => {
        console.log(`item ${item.id} started uploading`);  
    });

    uploader.on(UPLOADER_EVENTS.ITEM_PROGRESS, (item) => {
      console.log(`item ${item.id} progress ${JSON.stringify(item)}`);
    });
    
    uploader.add(event.dataTransfer.files[0]);
    // // fetch("http://localhost:5000/uploadfile", {method: "POST", body: formData});
    // axios.request({
    //   method: "post", 
    //   url: "http://localhost:5000/uploadfile", 
    //   data: formData, 
    //   onUploadProgress: (p) => {
    //     console.log(p); 
    //     //this.setState({
    //         //fileprogress: p.loaded / p.total
    //     //})
    //   }
  // }).then (data => {
  //     //this.setState({
  //       //fileprogress: 1.0,
  //     //})
  //     console.log("Then hook called");
  // })
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