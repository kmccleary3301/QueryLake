"use client";
interface DocPageProps {
  params: {
    slug: string[],
  },
  searchParams: object
}


type collection_mode_type = "create" | "session" | "view" | undefined;

/**
 * v0 by Vercel.
 * @see https://v0.dev/t/n2FrFZXZwwu
 * Documentation: https://v0.dev/docs#integrating-generated-code-into-your-nextjs-app
 */

import { useEffect, useState } from "react";
import { useContextAction } from "@/app/context-provider";
import { useRouter } from 'next/navigation';
import { ToolChain } from '@/types/toolchains';


export default function AppPage({ params, searchParams }: DocPageProps) {

  const router = useRouter();
  const collection_mode_immediate = (["create", "session", "view"].indexOf(params["slug"][0]) > -1) ? params["slug"][0] as collection_mode_type : undefined;
  const [CollectionMode, setCollectionMode] = useState<collection_mode_type>(collection_mode_immediate);
  const [toolchainActive, setToolchainActive] = useState<ToolChain | undefined>(undefined);

  useEffect(() => {

  }, [])

  const {
    userData,
    refreshCollectionGroups,
    selectedToolchain,
  } = useContextAction();

  
  return (
      <>
      </>
  );
}

