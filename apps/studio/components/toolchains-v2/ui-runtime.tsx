"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { ComponentType } from "react";

import ToolchainUISpecRendererV2 from "@/components/toolchains-v2/ui-spec-renderer";
import { TOOLCHAIN_COMPONENT_REGISTRY } from "@/lib/toolchains-v2/component-registry";
import {
  resolveBindingRecord,
  runHook,
  ToolchainUIRuntimeContext,
} from "@/lib/toolchains-v2/runtime";
import type {
  ComponentNode,
  ToolchainUISpecV2,
} from "@/types/toolchain-ui-spec-v2";

export type ToolchainUISpecRuntimeProps = {
  spec: ToolchainUISpecV2;
  state: unknown;
  ui: unknown;
  prefs?: Record<string, unknown>;
  session?: ToolchainUIRuntimeContext["session"];
  actions: ToolchainUIRuntimeContext["actions"];
};

function ToolchainComponentRuntime({
  node,
  ctx,
}: {
  node: ComponentNode;
  ctx: ToolchainUIRuntimeContext;
}) {
  const entry = TOOLCHAIN_COMPONENT_REGISTRY[node.componentId];
  const loader = entry?.load;
  const [Component, setComponent] = useState<ComponentType<any> | null>(null);

  useEffect(() => {
    if (!loader) return;
    let active = true;
    loader().then((mod) => {
      if (!active) return;
      setComponent(() => mod.default);
    });
    return () => {
      active = false;
    };
  }, [loader]);

  const bindings = useMemo(() => {
    if (!node.bindings) return {};
    return resolveBindingRecord(node.bindings, ctx);
  }, [node.bindings, ctx]);

  const emit = useCallback(
    (hook: string, payload?: unknown) => runHook(node.hooks, hook, ctx, payload),
    [node.hooks, ctx]
  );

  if (!entry) {
    return (
      <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
        Unknown component &quot;{node.componentId}&quot;
      </div>
    );
  }

  if (!Component) {
    return (
      <div className="rounded-md border border-border/60 bg-muted/10 px-3 py-2 text-xs text-muted-foreground">
        Loading {node.componentId}...
      </div>
    );
  }

  return (
    <Component
      componentId={node.componentId}
      nodeId={node.id}
      config={node.config ?? {}}
      bindings={bindings}
      emit={emit}
      ctx={ctx}
    />
  );
}

export default function ToolchainUISpecRuntime({
  spec,
  state,
  ui,
  prefs = {},
  session = {},
  actions,
}: ToolchainUISpecRuntimeProps) {
  const runtimeCtx = useMemo<ToolchainUIRuntimeContext>(
    () => ({
      state,
      session,
      ui,
      prefs,
      actions,
    }),
    [actions, prefs, session, state, ui]
  );

  const renderComponent = useCallback(
    (node: ComponentNode) => (
      <ToolchainComponentRuntime node={node} ctx={runtimeCtx} />
    ),
    [runtimeCtx]
  );

  return <ToolchainUISpecRendererV2 spec={spec} renderComponent={renderComponent} />;
}

