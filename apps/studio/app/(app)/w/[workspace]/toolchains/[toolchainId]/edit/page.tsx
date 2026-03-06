"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

function getParam(value: string | string[] | undefined): string | null {
  if (!value) return null;
  if (Array.isArray(value)) return value[0] ?? null;
  return value;
}

export default function ToolchainEditorRedirect() {
  const router = useRouter();
  const params = useParams();
  const workspace = getParam(params?.workspace);
  const toolchainId = getParam(params?.toolchainId);

  useEffect(() => {
    if (!workspace || !toolchainId) return;
    router.replace(`/w/${workspace}/toolchains/${toolchainId}/edit/graph`);
  }, [router, workspace, toolchainId]);

  return (
    <div className="mx-auto max-w-screen-xl px-6 py-6">
      <div className="ql-editor-shell">
        <div className="ql-editor-state">Opening graph editor...</div>
      </div>
    </div>
  );
}
