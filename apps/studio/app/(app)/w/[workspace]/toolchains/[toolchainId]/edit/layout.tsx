import Link from "next/link";

import { Button } from "@/components/ui/button";

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
    <div className="space-y-3">
      <div className="ql-toolbar-strip justify-between">
        <div className="min-w-0">
          <div className="ql-editor-kicker">Toolchain studio</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium text-foreground">{toolchainId}</span>
            <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
              workspace {workspace}
            </span>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((tab) => (
            <Button key={tab.href} asChild variant="outline" size="sm">
              <Link href={tab.href}>{tab.label}</Link>
            </Button>
          ))}
          <Button asChild variant="outline" size="sm">
            <Link href={`/w/${workspace}/toolchains/${toolchainId}`}>Back to toolchain</Link>
          </Button>
        </div>
      </div>
      {children}
    </div>
  );
}
