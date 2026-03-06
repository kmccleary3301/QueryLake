import Link from "next/link";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default async function ToolchainEditorLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ workspace: string; toolchainId: string }>;
}) {
  const { workspace, toolchainId } = await params;
  const base = `/w/${workspace}/toolchains/${toolchainId}/edit`;

  const tabs = [
    { href: `${base}/graph`, label: "Graph" },
    { href: `${base}/interface`, label: "Interface" },
    { href: `${base}/settings`, label: "Settings" },
  ];

  return (
    <div className="ql-editor-shell">
      <div className="ql-editor-hero">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="ql-editor-kicker">Toolchain Studio V2</div>
            <div className="space-y-1">
              <div className="text-2xl font-semibold tracking-tight">{toolchainId}</div>
              <div className="max-w-3xl text-sm text-muted-foreground">
                Compose graph logic, shape interface layouts, and iterate on the toolchain as a visual artifact instead of a form-bound admin surface.
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-full border border-border/70 bg-background/45 px-3 py-1 text-xs text-muted-foreground">
              Workspace <span className="font-mono text-foreground">{workspace}</span>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href={`/w/${workspace}/toolchains/${toolchainId}`}>
                Back to toolchain
              </Link>
            </Button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <Button
              key={tab.href}
              asChild
              variant="outline"
              size="sm"
              className={cn("h-8 rounded-full px-3 text-xs")}
            >
              <Link href={tab.href}>{tab.label}</Link>
            </Button>
          ))}
        </div>
      </div>
      <div className="ql-editor-surface">
        {children}
      </div>
    </div>
  );
}
