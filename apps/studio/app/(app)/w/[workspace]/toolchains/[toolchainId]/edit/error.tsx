"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function ToolchainEditorError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Keep browser/server logs available while surfacing a stable fallback UI.
    // eslint-disable-next-line no-console
    console.error("Toolchain editor route error:", error);
  }, [error]);

  return (
    <div className="ql-editor-alert-error space-y-3 p-4">
      <div className="text-sm font-semibold text-destructive">
        The Toolchains V2 editor failed to render.
      </div>
      <div className="text-xs text-destructive/90">
        {error.message || "Unexpected editor error."}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="outline" onClick={reset}>
          Try again
        </Button>
      </div>
    </div>
  );
}
