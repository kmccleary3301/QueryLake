import React, { useRef, useState } from 'react';
import { Button } from './button';
import { cn } from '@/lib/utils';

export default function FileDropzone({ 
  onFileSelected,
  multiple = false,
}:{
  onFileSelected: (file: File) => void;
  multiple?: boolean;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    const file = event.dataTransfer.files[0];
    onFileSelected(file);
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onFileSelected(file);
    }
  };

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (files_in : FileList) => {
    if (files_in !== null && files_in.length > 0) {
      if (multiple) {
        setFiles([...files, ...Array.from(files_in)]);
      } else {
        setFiles([Array.from(files_in)[0]]);
      }
    }
  };

  return (
    <div className={cn(
      "hover:bg-accent active:bg-accent/70 hover:text-accent-foreground hover:text-accent-foreground/",
      "rounded-lg border-[2px] border-dashed border-primary p-2 text-center cursor-pointer",
    )}
    onClick={handleButtonClick}
    onDrop={(e)=>{
      e.preventDefault();
      console.log("DROP!!!");
    }}
    onDragOver={(e) => {
      e.preventDefault();
    }}>
      <div className='rounded-[inherit]'>
        <input
          type="file"
          multiple={multiple}
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={(e) => {if (e.target.files) handleFileChange(e.target.files)}}
        />
        <p>Upload File</p>
      </div>
    </div>
  );
};