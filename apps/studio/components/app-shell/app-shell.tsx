"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import {
  ActivitySquare,
  BarChart3,
  ChevronsUpDown,
  Files,
  FolderKanban,
  KeyRound,
  LayoutDashboard,
  PlayCircle,
  PlugZap,
  Settings2,
  Shield,
  UserCircle2,
  Users2,
  Workflow,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { useContextAction } from "@/app/context-provider";
import WorkspaceCommandPalette from "@/components/app-shell/workspace-command-palette";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
};

type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

type NavSection = {
  label: string;
  items: NavItem[];
};

const navSections: NavSection[] = [
  {
    label: "Core",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Collections", href: "/collections", icon: FolderKanban },
      { label: "Files", href: "/files", icon: Files },
      { label: "Playground", href: "/playground", icon: PlayCircle },
    ],
  },
  {
    label: "Toolchains",
    items: [
      { label: "Toolchains", href: "/toolchains", icon: Workflow },
      { label: "Runs", href: "/runs", icon: ActivitySquare },
    ],
  },
  {
    label: "Platform",
    items: [
      { label: "API Keys", href: "/platform/api-keys", icon: KeyRound },
      { label: "Usage", href: "/platform/usage", icon: BarChart3 },
      { label: "Members", href: "/settings/members", icon: Users2 },
      { label: "Integrations", href: "/settings/integrations", icon: PlugZap },
    ],
  },
];

function getWorkspaceFromPath(pathname: string) {
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length >= 2 && segments[0] === "w") {
    return segments[1];
  }
  return "personal";
}

function resolveWorkspaceLabel(
  workspace: string,
  userData?: { username: string; memberships: { organization_id: string; organization_name: string }[] }
) {
  if (workspace === "personal") {
    return userData?.username ? `${userData.username} (Personal)` : "Personal";
  }
  const match = userData?.memberships?.find((membership) => membership.organization_id === workspace);
  return match?.organization_name ?? workspace;
}

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname() ?? "";
  const workspace = getWorkspaceFromPath(pathname);
  const { userData } = useContextAction();
  const workspaceLabel = resolveWorkspaceLabel(workspace, userData);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (workspace) {
      window.localStorage.setItem("ql_last_workspace", workspace);
    }
  }, [workspace]);

  return (
    <div className="ql-app-shell">
      <aside className="ql-app-sidebar">
        <div className="ql-app-brand">
          <div className="ql-app-brand-mark">QueryLake Studio</div>
          <div className="ql-app-brand-title">Research operating console</div>
          <div className="ql-app-brand-copy">
            Toolchains, retrieval, documents, and runtime instrumentation in one workspace.
          </div>
        </div>

        <Link href="/select-workspace" className="mt-4 block">
          <Button variant="outline" className="w-full justify-between">
            <span className="truncate">{workspaceLabel}</span>
            <ChevronsUpDown className="h-4 w-4 shrink-0" />
          </Button>
        </Link>

        <nav className="mt-4 flex min-h-0 flex-1 flex-col overflow-auto pr-1">
          {navSections.map((section) => (
            <div key={section.label}>
              <div className="ql-nav-section-label">{section.label}</div>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const href = `/w/${workspace}${item.href}`;
                  const active = pathname === href || pathname.startsWith(`${href}/`);
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={href}
                      className={cn("ql-nav-link", active && "ql-nav-link-active")}
                    >
                      <Icon className="ql-nav-link-icon" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="mt-4 space-y-1 border-t border-border/70 pt-4">
          <Link href="/account/profile" className="ql-nav-link">
            <UserCircle2 className="ql-nav-link-icon" />
            <span className="truncate">{userData?.username ? userData.username : "Account profile"}</span>
          </Link>
          <Link href="/account/preferences" className="ql-nav-link">
            <Settings2 className="ql-nav-link-icon" />
            <span>Preferences</span>
          </Link>
          <Link href="/account/security" className="ql-nav-link">
            <Shield className="ql-nav-link-icon" />
            <span>Security</span>
          </Link>
        </div>
      </aside>

      <div className="ql-app-main">
        <header className="ql-app-header">
          <div className="ql-app-header-meta">
            <div className="ql-page-kicker">Workspace context</div>
            <div className="mt-1 text-lg font-semibold tracking-[-0.03em] text-foreground">{workspaceLabel}</div>
            <div className="text-xs text-muted-foreground" title={workspace}>
              /w/{workspace}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <WorkspaceCommandPalette workspace={workspace} workspaceLabel={workspaceLabel} />
            <Button asChild size="sm" variant="outline">
              <Link href={`/w/${workspace}/toolchains`}>Open toolchains</Link>
            </Button>
            <Button asChild size="sm">
              <Link href={`/w/${workspace}/runs/new`}>New run</Link>
            </Button>
          </div>
        </header>
        <main className="ql-app-content">
          <div className="ql-page">{children}</div>
        </main>
      </div>
    </div>
  );
}
