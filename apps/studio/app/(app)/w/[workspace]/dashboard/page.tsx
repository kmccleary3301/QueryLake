"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { useContextAction } from "@/app/context-provider";
import { QuerylakeFetchUsage, UsageEntryType } from "@/hooks/querylakeAPI";
import { collectionGroup } from "@/types/globalTypes";

const isPersonalWorkspace = (workspace: string) =>
  workspace === "personal" || workspace === "me";

const quickLinks = [
  {
    title: "Collections",
    description: "Organize knowledge bases and retrieval-ready corpora.",
    href: "collections",
  },
  {
    title: "Files",
    description: "Upload and parse documents into your collections.",
    href: "files",
  },
  {
    title: "Toolchains",
    description: "Build and version workflow graphs for your apps.",
    href: "toolchains",
  },
  {
    title: "Runs",
    description: "Monitor live runs and replay historical sessions.",
    href: "runs",
  },
];

export default function DashboardPage() {
  const params = useParams<{ workspace: string }>()!;
  const workspace = params.workspace;
  const {
    userData,
    authReviewed,
    loginValid,
    collectionGroups,
    refreshCollectionGroups,
    toolchainSessions,
    refreshToolchainSessions,
  } = useContextAction();

  const [usage, setUsage] = useState<UsageEntryType[] | null>(null);
  const [usageLoading, setUsageLoading] = useState(false);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) return;
    if (collectionGroups.length === 0) {
      refreshCollectionGroups();
    }
  }, [
    authReviewed,
    loginValid,
    userData?.auth,
    collectionGroups.length,
    refreshCollectionGroups,
  ]);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) return;
    if (toolchainSessions.size === 0) {
      refreshToolchainSessions();
    }
  }, [
    authReviewed,
    loginValid,
    userData?.auth,
    toolchainSessions.size,
    refreshToolchainSessions,
  ]);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) {
      setUsage(null);
      setUsageLoading(false);
      return;
    }

    const endTime = Math.floor(Date.now() / 1000);
    const startTime = endTime - 60 * 60 * 24 * 30;
    setUsageLoading(true);

    QuerylakeFetchUsage({
      auth: userData.auth,
      start_time: startTime,
      end_time: endTime,
      window: "day",
      onFinish: (result) => {
        if (result && Array.isArray(result)) {
          setUsage(result);
        } else {
          setUsage([]);
        }
        setUsageLoading(false);
      },
    });
  }, [authReviewed, loginValid, userData?.auth]);

  const filteredGroups: collectionGroup[] = useMemo(() => {
    if (collectionGroups.length === 0) return [];
    if (isPersonalWorkspace(workspace)) {
      return collectionGroups.filter((group) =>
        ["My Collections", "Global Collections"].includes(group.title)
      );
    }
    const membership = userData?.memberships.find(
      (member) => member.organization_id === workspace
    );
    if (!membership) return collectionGroups;
    const match = collectionGroups.filter(
      (group) => group.title === membership.organization_name
    );
    return match.length ? match : collectionGroups;
  }, [collectionGroups, userData?.memberships, workspace]);

  const collectionsCount = useMemo(() => {
    const groupsToCount = filteredGroups.length ? filteredGroups : collectionGroups;
    return groupsToCount.reduce((acc, group) => acc + group.collections.length, 0);
  }, [collectionGroups, filteredGroups]);

  const usageEntriesCount = useMemo(() => {
    if (!usage || usage.length === 0) return 0;
    if (isPersonalWorkspace(workspace)) {
      return usage.filter((entry) => entry.organization_id == null).length;
    }
    return usage.filter((entry) => entry.organization_id === workspace).length;
  }, [usage, workspace]);

  const runsCount = toolchainSessions.size;

  if (!authReviewed) {
    return (
      <div className="space-y-6">
        <div className="ql-page-header">
          <div className="space-y-2">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-4 w-80" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-40 w-full rounded-[18px]" />
          <Skeleton className="h-40 w-full rounded-[18px]" />
          <Skeleton className="h-40 w-full rounded-[18px]" />
        </div>
      </div>
    );
  }

  if (!loginValid || !userData) {
    return (
      <div className="space-y-6">
        <div className="ql-page-header">
          <div>
            <div className="ql-page-kicker">Workspace overview</div>
            <h1 className="ql-page-title">Workspace dashboard</h1>
            <p className="ql-page-copy">Sign in to view collections, activity, and usage for this workspace.</p>
          </div>
        </div>
        <div className="ql-panel p-6 text-sm text-muted-foreground">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Authentication required</div>
          <div className="mt-2 max-w-2xl leading-6">You need an authenticated session to view workspace metrics, recent runs, and operational activity.</div>
          <div className="mt-4">
            <Button asChild size="sm">
              <Link href="/auth/login">Go to login</Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="ql-page-header">
        <div>
          <div className="ql-page-kicker">Workspace overview</div>
          <Breadcrumb className="mt-2">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href={`/w/${workspace}`}>Workspace</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbItem>
                <BreadcrumbPage>Dashboard</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="ql-page-title">Workspace dashboard</h1>
          <p className="ql-page-copy">
            Operational view of collections, toolchain activity, and usage in this workspace.
          </p>
        </div>
        <div className="ql-toolbar-strip">
          <Button asChild size="sm" variant="outline">
            <Link href={`/w/${workspace}/collections`}>Open collections</Link>
          </Button>
          <Button asChild size="sm" variant="outline">
            <Link href={`/w/${workspace}/runs`}>Open runs</Link>
          </Button>
          <Button asChild size="sm">
            <Link href={`/w/${workspace}/toolchains`}>Open toolchains</Link>
          </Button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="ql-metric-card">
          <div className="ql-metric-label">Collections</div>
          <div className="ql-metric-value">{collectionsCount}</div>
          <div className="ql-metric-copy">Knowledge bases available for retrieval, search, and downstream toolchain execution.</div>
          <div className="mt-4">
            <Button asChild size="sm" variant="outline">
              <Link href={`/w/${workspace}/collections`}>View collections</Link>
            </Button>
          </div>
        </div>

        <div className="ql-metric-card">
          <div className="ql-metric-label">Runs</div>
          <div className="ql-metric-value">{runsCount}</div>
          <div className="ql-metric-copy">Active and historical sessions currently indexed in the workspace runtime ledger.</div>
          <div className="mt-4">
            <Button asChild size="sm" variant="outline">
              <Link href={`/w/${workspace}/runs`}>View runs</Link>
            </Button>
          </div>
        </div>

        <div className="ql-metric-card">
          <div className="ql-metric-label">Usage entries · 30d</div>
          <div className="ql-metric-value">{usageLoading ? "—" : usageEntriesCount}</div>
          <div className="ql-metric-copy">Metering events recorded during the last thirty days for this workspace scope.</div>
          <div className="mt-4">
            <Button asChild size="sm" variant="outline">
              <Link href={`/w/${workspace}/platform/usage`}>View usage</Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        {quickLinks.map((link) => (
          <div key={link.title} className="ql-panel p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="ql-page-kicker">Navigate</div>
                <h2 className="mt-2 text-base font-semibold text-foreground">{link.title}</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{link.description}</p>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link href={`/w/${workspace}/${link.href}`}>Open</Link>
              </Button>
            </div>
          </div>
        ))}
      </section>

      <section className="ql-search-surface p-5">
        <div className="ql-page-kicker">Roadmap surface</div>
        <div className="mt-2 text-base font-semibold text-foreground">Activity and ingestion ledger</div>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          This dashboard is the future home for upload activity, ingestion status, retrieval health,
          runtime events, and background job instrumentation as the v2 files and toolchain systems
          become the primary workspace workflow.
        </p>
      </section>
    </div>
  );
}
