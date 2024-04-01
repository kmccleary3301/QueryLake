"use client";
import React from "react";
import { ScrollArea } from "@/registry/default/ui/scroll-area";
import { Button } from "@/registry/default/ui/button";

interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}

export default function TestPage() {
  return (
    <div>
      <Button onClick={() => {}}>
        Test websocket.
      </Button>
    </div>
  );
}