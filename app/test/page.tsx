"use client";
import React from "react";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Button } from "@/registry/default/ui/button";
import ToolchainSession from "@/components/manual_components/toolchain-session";

interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

export default function TestPage() {

  const testWebsocket = () => {
    const tc_ws = new ToolchainSession(() => {}, () => {});
  }
  
  return (
    <div>
      <Button onClick={testWebsocket}>
        Test websocket.
      </Button>
    </div>
  );
}