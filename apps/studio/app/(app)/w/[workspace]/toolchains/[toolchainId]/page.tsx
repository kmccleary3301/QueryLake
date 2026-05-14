"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import RuntimeModeBanner from "@/components/toolchains/runtime-mode-banner";
import { useRuntimeMode } from "@/components/toolchains/runtime-mode";
import { useContextAction } from "@/app/context-provider";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { fetchToolchainConfig } from "@/hooks/querylakeAPI";
import { toolchain_session } from "@/types/globalTypes";
import { ToolChain } from "@/types/toolchains";

export default function ToolchainPage() {
  const params = useParams<{ workspace: string; toolchainId: string }>()!;
  const router = useRouter();
  const {
    userData,
    setSelectedToolchain,
    toolchainSessions,
    refreshToolchainSessions,
    authReviewed,
    loginValid,
  } = useContextAction();
  const { mode } = useRuntimeMode();
  const [toolchain, setToolchain] = useState<ToolChain | null>(null);
  const [loading, setLoading] = useState(true);
  const [creatingSession, setCreatingSession] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchToolchainConfig({
      auth: userData.auth,
      toolchain_id: params.toolchainId,
      onFinish: (result: ToolChain) => {
        setToolchain(result);
        setLoading(false);
      },
    });
  }, [authReviewed, loginValid, userData?.auth, params.toolchainId]);

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

  const nodePreview = useMemo(() => {
    return toolchain?.nodes?.slice(0, 6) ?? [];
  }, [toolchain?.nodes]);

  const recentRuns: toolchain_session[] = useMemo(() => {
    const runs = Array.from(toolchainSessions.values()).filter(
      (run) => run.toolchain === params.toolchainId
    );
    return runs.sort((a, b) => b.time - a.time).slice(0, 10);
  }, [params.toolchainId, toolchainSessions]);

  const openLegacyRunner = () => {
    setSelectedToolchain(params.toolchainId);
    router.push("/app/create");
  };

  const createV2Session = async () => {
    if (!userData?.auth) return;
    setCreatingSession(true);
    setCreateError(null);
    try {
      const response = await fetch("/v2/kernel/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${userData.auth}`,
        },
        body: JSON.stringify({
          toolchain_id: params.toolchainId,
          title: toolchain?.name,
        }),
      });
      if (!response.ok) {
        setCreateError(`Failed to create session (${response.status}).`);
        setCreatingSession(false);
        return;
      }
      const data = await response.json();
      const sessionId = data?.session_id;
      if (!sessionId) {
        setCreateError("Session created but no session_id returned.");
        setCreatingSession(false);
        return;
      }
      router.push(`/w/${params.workspace}/runs/${sessionId}`);
    } catch (error) {
      setCreateError(`Failed to create session: ${String(error)}`);
      setCreatingSession(false);
    }
  };

  return (
    <div className="space-y-6">
      <RuntimeModeBanner />

      <header className="ql-page-header">
        <div>
          <div className="ql-page-kicker">Workflow detail</div>
          <Breadcrumb className="mt-2">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink href={`/w/${params.workspace}`}>Workspace</BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink href={`/w/${params.workspace}/toolchains`}>
                  Toolchains
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage>{params.toolchainId}</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="ql-page-title">{toolchain?.name ?? params.toolchainId}</h1>
          <p className="ql-page-copy">
            Runtime entry points, graph editing surfaces, and recent execution history for this toolchain.
          </p>
        </div>

        <div className="ql-toolbar-strip">
          <Button asChild size="sm" variant="outline">
            <Link href={`/w/${params.workspace}/toolchains`}>Back to toolchains</Link>
          </Button>
          <Button size="sm" variant="outline" onClick={openLegacyRunner}>
            Open legacy runner
          </Button>
          {mode === "v2" ? (
            <Button size="sm" onClick={createV2Session} disabled={creatingSession}>
              {creatingSession ? "Creating session..." : "Create v2 session"}
            </Button>
          ) : null}
          <Button asChild size="sm" variant="outline">
            <Link href={`/w/${params.workspace}/toolchains/${params.toolchainId}/edit`}>
              Open v2 editor
            </Link>
          </Button>
        </div>
      </header>

      {createError ? (
        <div className="ql-editor-alert-error text-sm">{createError}</div>
      ) : null}

      {loading ? (
        <div className="ql-panel space-y-3 p-5">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-52" />
          <Skeleton className="h-4 w-56" />
          <Skeleton className="h-4 w-44" />
        </div>
      ) : !toolchain ? (
        <div className="ql-panel p-6 text-sm text-muted-foreground">
          Unable to load toolchain details. Check your auth state and backend availability.
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.45fr_0.95fr]">
          <section className="ql-panel p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
              <div>
                <div className="ql-page-kicker">Overview</div>
                <h2 className="mt-2 text-base font-semibold text-foreground">Workflow facts</h2>
              </div>
              <div className="rounded-full border border-border/70 bg-background/55 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                Runtime {mode === "v2" ? "v2 sessions" : "legacy runtime"}
              </div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <div className="ql-panel-inset p-3">
                <div className="ql-metric-label">Identifier</div>
                <div className="mt-2 break-all font-mono text-sm text-foreground">{toolchain.id}</div>
              </div>
              <div className="ql-panel-inset p-3">
                <div className="ql-metric-label">Category</div>
                <div className="mt-2 text-sm font-medium text-foreground">{toolchain.category}</div>
              </div>
              <div className="ql-panel-inset p-3">
                <div className="ql-metric-label">Nodes</div>
                <div className="mt-2 text-sm font-medium text-foreground">{toolchain.nodes?.length ?? 0}</div>
              </div>
              <div className="ql-panel-inset p-3">
                <div className="ql-metric-label">First event</div>
                <div className="mt-2 text-sm font-medium text-foreground">{toolchain.first_event_follow_up ?? "—"}</div>
              </div>
            </div>
          </section>

          <section className="ql-panel p-5">
            <div className="ql-page-kicker">Runtime notes</div>
            <div className="mt-2 text-base font-semibold text-foreground">Execution path</div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">
              {mode === "v2"
                ? "v2 sessions are available for the new runtime flow. Use the editor to refine the graph and interface surface, then create a session to validate end-to-end behavior."
                : "Legacy WebSocket runtime is active for this workspace mode. Use the legacy runner for compatibility while the v2 execution path continues to land."}
            </p>
          </section>
        </div>
      )}

      {toolchain ? (
        <section className="ql-panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
            <div>
              <div className="ql-page-kicker">Graph snapshot</div>
              <h2 className="mt-2 text-base font-semibold text-foreground">Node preview</h2>
            </div>
            <div className="rounded-full border border-border/70 bg-background/55 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              Showing {nodePreview.length} of {toolchain.nodes.length}
            </div>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {nodePreview.map((node) => (
              <div key={node.id} className="ql-panel-inset p-4 text-sm">
                <div className="font-medium text-foreground">{node.id}</div>
                <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">
                  {node.api_function ?? "Custom node"}
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="ql-panel p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 pb-4">
          <div>
            <div className="ql-page-kicker">Execution history</div>
            <h2 className="mt-2 text-base font-semibold text-foreground">Recent runs</h2>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button asChild size="sm">
              <Link href={`/w/${params.workspace}/runs/new?toolchain=${params.toolchainId}`}>
                New run
              </Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href={`/w/${params.workspace}/runs`}>View all runs</Link>
            </Button>
          </div>
        </div>

        {recentRuns.length === 0 ? (
          <div className="ql-runtime-inset mt-4 p-4 text-sm text-muted-foreground">
            No runs recorded for this toolchain yet.
          </div>
        ) : (
          <div className="mt-4 divide-y divide-border rounded-[16px] border border-border/80 bg-card/65">
            {recentRuns.map((run) => (
              <div
                key={run.id}
                className="flex flex-wrap items-center justify-between gap-4 px-4 py-3 text-sm"
              >
                <div>
                  <div className="font-medium text-foreground">{run.title}</div>
                  <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">{run.id}</div>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>{new Date(run.time * 1000).toLocaleString()}</span>
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/w/${params.workspace}/runs/${run.id}`}>Open</Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
