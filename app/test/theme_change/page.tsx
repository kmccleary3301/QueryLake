"use client";
import { useCallback, useEffect, useRef, useState } from "react";
// import { ScrollArea } from "@radix-ui/react-scroll-area";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
// import { Textarea } from "@/registry/default/ui/textarea";
import Editor, { Monaco, OnMount } from '@monaco-editor/react';
import { editor } from "monaco-editor-core";
import { Button } from "@/registry/default/ui/button";
// import { getHighlighter } from 'shiki';
// import * as monaco from 'monaco-editor';

function ThemeController({
  children,
}:{
  children: React.ReactNode
}) {
  const [primaryColor, setPrimaryColor] = useState('0, 100%, 50%'); // Initial Red
  const [secondaryColor, setSecondaryColor] = useState('120, 100%, 50%'); // Initial Green

  const handleChangeColors = () => {
    setPrimaryColor(primaryColor === '0, 100%, 50%' ? '0, 50%, 50%' : '0, 100%, 50%'); // Toggle between Red and Blue
    setSecondaryColor(secondaryColor === '120, 100%, 50%' ? '120, 50%, 50%' : '120, 100%, 50%'); // Toggle between Green and Magenta
  };

  return (
    <div
      style={{
        // '--background': primaryColor,
        // '--secondary': secondaryColor,
      } as React.CSSProperties} // Add type assertion to accept custom CSS properties
      className="custom-colors bg-primary-color text-secondary-color p-4"
    >
      <Button onClick={handleChangeColors}>Change Colors</Button>
      {children}
    </div>
  );
}


export default function ThemeTestPage() {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  const handleEditorDidMount = (editor: editor.IStandaloneCodeEditor, monaco: Monaco) => {
    // here is the editor instance
    // you can store it in `useRef` for further usage
    editorRef.current = editor;
  }

  return (
    <div className="w-full h-[calc(100vh)] flex flex-row justify-center">
				<ScrollArea className="w-full">
					<div className="flex flex-row justify-center">
						<div className="w-[85vw] md:w-[70vw] lg:w-[45vw]">
              <ThemeController>
                <div className="flex flex-wrap justify-center gap-6 py-[100px]">
                  <div className="w-[100px] h-[100px] bg-background border-8 border-foreground"/>
                  <div className="w-[100px] h-[100px] bg-foreground border-8 border-background"/>
                  <div className="w-[100px] h-[100px] bg-card border-8 border-card-foreground"/>
                  <div className="w-[100px] h-[100px] bg-card-foreground border-8 border-card"/>
                  <div className="w-[100px] h-[100px] bg-popover border-8 border-popover-foreground"/>
                  <div className="w-[100px] h-[100px] bg-popover-foreground border-8 border-popover"/>
                  <div className="w-[100px] h-[100px] bg-primary border-8 border-primary-foreground"/>
                  <div className="w-[100px] h-[100px] bg-primary-foreground border-8 border-primary"/>
                  <div className="w-[100px] h-[100px] bg-secondary border-8 border-secondary-foreground"/>
                  <div className="w-[100px] h-[100px] bg-secondary-foreground border-8 border-secondary"/>
                  <div className="w-[100px] h-[100px] bg-muted border-8 border-muted-foreground"/>
                  <div className="w-[100px] h-[100px] bg-muted-foreground border-8 border-muted"/>
                  <div className="w-[100px] h-[100px] bg-accent border-8 border-accent-foreground"/>
                  <div className="w-[100px] h-[100px] bg-accent-foreground border-8 border-accent"/>
                  <div className="w-[100px] h-[100px] bg-destructive border-8 border-destructive-foreground"/>
                  <div className="w-[100px] h-[100px] bg-destructive-foreground border-8 border-destructive"/>
                  <div className="w-[100px] h-[100px] bg-border border-8 border-background"/>
                  <div className="w-[100px] h-[100px] bg-input border-8 border-background"/>
                </div>
              </ThemeController>
						</div>
					</div>
				</ScrollArea>
			</div>
  );
}

// export CodeEditor;