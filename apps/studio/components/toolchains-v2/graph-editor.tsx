"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

import ReactFlow, {
  Background,
  BaseEdge,
  Connection,
  Controls,
  Edge,
  EdgeChange,
  EdgeLabelRenderer,
  EdgeProps,
  Handle,
  MiniMap,
  Node,
  NodeProps,
  Position,
  ReactFlowInstance,
  Viewport,
  getBezierPath,
  useNodesState,
  useViewport,
} from "reactflow";
import "reactflow/dist/base.css";

import { useContextAction } from "@/app/context-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuLabel,
  ContextMenuSeparator,
  ContextMenuSub,
  ContextMenuSubContent,
  ContextMenuSubTrigger,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { fetchToolchainConfig, updateToolchainConfig } from "@/hooks/querylakeAPI";
import { cn } from "@/lib/utils";
import type { APIFunctionSpec } from "@/types/globalTypes";
import type {
  ToolChain,
  feedMapping,
  feedMappingOriginal,
  nodeInputArgument,
  staticRoute,
  toolchainNode,
} from "@/types/toolchains";
import { toast } from "sonner";

type Props = {
  params: { workspace: string; toolchainId: string };
};

type GraphNodeOutput = {
  index: number;
  destination: string;
  kind: "node" | "state" | "user";
  stream: boolean;
};

type GraphNodeData = {
  id: string;
  apiFunction?: string;
  inputKeys: string[];
  outputs: GraphNodeOutput[];
  selectedFeedIndex?: number | null;
  hoveredFeedIndex?: number | null;
  highlightedAsDestination?: boolean;
  onEditMapping?: (index: number) => void;
  onCreateMapping?: () => void;
  onToggleStream?: (index: number) => void;
  onCycleDestination?: (index: number) => void;
  onHoverMapping?: (index: number | null) => void;
  showDropHint?: boolean;
  isConnectSource?: boolean;
};

type GraphEdgeData = {
  destinationLabel: string;
  sourceModeLabel: string;
  routeText: string;
  stream: boolean;
  tooltip: string;
  onSelect?: (anchor?: CanvasOverlayPosition) => void;
  onEdit?: (anchor?: CanvasOverlayPosition) => void;
  onToggleStream?: () => void;
  onCycleDestination?: () => void;
  onCycleSourceMode?: () => void;
};

type SelectedFeed = {
  nodeId: string;
  index: number;
};

type CanvasOverlayPosition = {
  x: number;
  y: number;
};

function eventAnchorFromElement(element: HTMLElement): CanvasOverlayPosition {
  const rect = element.getBoundingClientRect();
  return {
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2,
  };
}

type MappingSourceMode = "dry" | "static" | "state" | "node_input" | "node_output";
type InputSourceMode =
  | "none"
  | "user_input"
  | "server_argument"
  | "static_value"
  | "toolchain_state"
  | "files";

type MappingEditorForm = {
  destination: string;
  stream: boolean;
  sourceMode: MappingSourceMode;
  valueText: string;
  routeText: string;
};

type InputEditorTarget = {
  nodeId: string;
  index: number | null;
};

type InputEditorForm = {
  key: string;
  typeHint: string;
  optional: boolean;
  sourceMode: InputSourceMode;
  valueText: string;
  routeText: string;
};

const SPECIAL_DESTINATIONS = ["<<STATE>>", "<<USER>>"] as const;
const HISTORY_LIMIT = 80;

function cloneToolchainSnapshot(toolchain: ToolChain): ToolChain {
  return JSON.parse(JSON.stringify(toolchain)) as ToolChain;
}

function isEdgeDestinationNode(destination: string) {
  return destination !== "<<STATE>>" && destination !== "<<USER>>";
}

function parseFeedEdgeId(edgeId: string): { source: string; index: number } | null {
  if (!edgeId.startsWith("e-")) return null;
  const rest = edgeId.slice(2);
  const lastDash = rest.lastIndexOf("-");
  if (lastDash <= 0) return null;
  const source = rest.slice(0, lastDash);
  const indexStr = rest.slice(lastDash + 1);
  const index = Number.parseInt(indexStr, 10);
  if (!Number.isFinite(index)) return null;
  return { source, index };
}

function parseFeedHandleIndex(handleId?: string | null): number | null {
  if (!handleId) return null;
  const match = /^feed-(\d+)$/.exec(handleId);
  if (!match) return null;
  const index = Number.parseInt(match[1], 10);
  return Number.isFinite(index) ? index : null;
}

function feedKind(destination: string): "node" | "state" | "user" {
  if (destination === "<<STATE>>") return "state";
  if (destination === "<<USER>>") return "user";
  return "node";
}

function destinationLabel(destination: string): string {
  if (destination === "<<STATE>>") return "STATE";
  if (destination === "<<USER>>") return "USER";
  return destination;
}

function mappingSourceMode(mapping: feedMappingOriginal): MappingSourceMode {
  const source = mapping as unknown as Record<string, unknown>;
  if ("value" in source) return "static";
  if ("getFromState" in source) return "state";
  if ("getFromInputs" in source) return "node_input";
  if ("getFromOutputs" in source) return "node_output";
  return "dry";
}

function mappingRoute(mapping: feedMappingOriginal): staticRoute | undefined {
  const source = mapping as unknown as Record<string, unknown>;
  if ("getFromState" in source) {
    return (source.getFromState as { route?: staticRoute } | undefined)?.route;
  }
  if ("getFromInputs" in source) {
    return (source.getFromInputs as { route?: staticRoute } | undefined)?.route;
  }
  if ("getFromOutputs" in source) {
    return (source.getFromOutputs as { route?: staticRoute } | undefined)?.route;
  }
  return undefined;
}

function cycleMappingSourceMode(mapping: feedMappingOriginal): feedMappingOriginal {
  const source = mapping as unknown as Record<string, unknown>;
  const sequence: MappingSourceMode[] = [
    "dry",
    "state",
    "node_input",
    "node_output",
    "static",
  ];
  const currentMode = mappingSourceMode(mapping);
  const currentIndex = sequence.indexOf(currentMode);
  const nextMode = sequence[(currentIndex + 1) % sequence.length];
  const preservedRoute = mappingRoute(mapping) ?? (["question"] as staticRoute);
  const base = {
    destination: mapping.destination,
    ...(mapping.stream ? { stream: true } : {}),
  };

  if (nextMode === "state") {
    return {
      ...base,
      getFromState: { route: preservedRoute },
    } as unknown as feedMappingOriginal;
  }
  if (nextMode === "node_input") {
    return {
      ...base,
      getFromInputs: { route: preservedRoute },
    } as unknown as feedMappingOriginal;
  }
  if (nextMode === "node_output") {
    return {
      ...base,
      getFromOutputs: { route: preservedRoute },
    } as unknown as feedMappingOriginal;
  }
  if (nextMode === "static") {
    const nextValue = "value" in source ? source.value : null;
    return {
      ...base,
      value: nextValue,
    } as unknown as feedMappingOriginal;
  }
  return base as feedMappingOriginal;
}

function summarizeMappingSource(mapping: feedMappingOriginal): {
  modeLabel: string;
  routeText: string;
} {
  const source = mapping as unknown as Record<string, unknown>;
  if ("value" in source) {
    return { modeLabel: "static", routeText: "" };
  }
  if ("getFromState" in source) {
    const route = (source.getFromState as { route?: staticRoute } | undefined)?.route;
    return { modeLabel: "state", routeText: routeToText(route) };
  }
  if ("getFromInputs" in source) {
    const route = (source.getFromInputs as { route?: staticRoute } | undefined)?.route;
    return { modeLabel: "input", routeText: routeToText(route) };
  }
  if ("getFromOutputs" in source) {
    const route = (source.getFromOutputs as { route?: staticRoute } | undefined)?.route;
    return { modeLabel: "output", routeText: routeToText(route) };
  }
  return { modeLabel: "dry", routeText: "" };
}

function sanitizeNodeId(raw: string): string {
  const normalized = raw
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return normalized || "node";
}

function uniqueNodeId(baseId: string, existingIds: Set<string>): string {
  if (!existingIds.has(baseId)) return baseId;
  let attempt = 2;
  while (existingIds.has(`${baseId}_${attempt}`)) {
    attempt += 1;
  }
  return `${baseId}_${attempt}`;
}

function nextMappingDestination(
  sourceNodeId: string,
  currentDestination: string,
  allNodeIds: string[]
): string {
  const orderedDestinations = [
    "<<STATE>>",
    "<<USER>>",
    ...allNodeIds.filter((nodeIdEntry) => nodeIdEntry !== sourceNodeId),
  ];
  const currentIndex = orderedDestinations.indexOf(currentDestination);
  if (currentIndex < 0) return orderedDestinations[0];
  return orderedDestinations[(currentIndex + 1) % orderedDestinations.length];
}

function parseRouteText(input: string): staticRoute {
  const raw = input.trim();
  if (!raw) return [];
  return raw
    .split(".")
    .map((token) => token.trim())
    .filter(Boolean)
    .map((token) => {
      if (/^-?\d+$/.test(token)) {
        return Number.parseInt(token, 10);
      }
      return token;
    }) as staticRoute;
}

function routeToText(route?: staticRoute): string {
  if (!route || !Array.isArray(route)) return "";
  return route
    .map((part) => {
      if (typeof part === "string" || typeof part === "number") {
        return String(part);
      }
      return "[complex]";
    })
    .join(".");
}

function routeTextToTokens(routeText: string): string[] {
  return routeText
    .split(".")
    .map((part) => part.trim())
    .filter(Boolean);
}

function routeTokensToText(tokens: string[]): string {
  return tokens.join(".");
}

function buildNodeData(
  node: toolchainNode,
  options?: {
    selectedFeedIndex?: number | null;
    hoveredFeedIndex?: number | null;
    highlightedAsDestination?: boolean;
    showDropHint?: boolean;
    isConnectSource?: boolean;
    onEditMapping?: (index: number) => void;
    onCreateMapping?: () => void;
    onToggleStream?: (index: number) => void;
    onCycleDestination?: (index: number) => void;
    onHoverMapping?: (index: number | null) => void;
  }
): GraphNodeData {
  return {
    id: node.id,
    apiFunction: node.api_function,
    inputKeys: (node.input_arguments ?? []).map((arg) => arg.key),
    outputs: (node.feed_mappings ?? []).map((mapping, index) => {
      const destination = (mapping as feedMapping).destination;
      return {
        index,
        destination,
        kind: feedKind(destination),
        stream: Boolean((mapping as feedMapping).stream),
      };
    }),
    selectedFeedIndex: options?.selectedFeedIndex ?? null,
    hoveredFeedIndex: options?.hoveredFeedIndex ?? null,
    highlightedAsDestination: options?.highlightedAsDestination ?? false,
    showDropHint: options?.showDropHint ?? false,
    isConnectSource: options?.isConnectSource ?? false,
    onEditMapping: options?.onEditMapping,
    onCreateMapping: options?.onCreateMapping,
    onToggleStream: options?.onToggleStream,
    onCycleDestination: options?.onCycleDestination,
    onHoverMapping: options?.onHoverMapping,
  };
}

function buildNodes(
  toolchain: ToolChain,
  options?: {
    selectedNodeId?: string | null;
    selectedFeed?: SelectedFeed | null;
    hoveredFeed?: SelectedFeed | null;
    highlightedDestinationNodeIds?: Set<string>;
    connectSourceNodeId?: string | null;
    onEditMapping?: (nodeId: string, index: number) => void;
    onCreateMapping?: (nodeId: string) => void;
    onToggleStream?: (nodeId: string, index: number) => void;
    onCycleDestination?: (nodeId: string, index: number) => void;
    onHoverMapping?: (nodeId: string, index: number | null) => void;
  }
): Node<GraphNodeData>[] {
  const positions = toolchain.editor_meta?.graph?.nodes ?? {};
  return toolchain.nodes.map((node, index) => ({
    id: node.id,
    type: "toolchainV2",
    selected: node.id === options?.selectedNodeId,
    position:
      positions[node.id] ?? {
        x: 180 + (index % 3) * 330,
        y: 100 + Math.floor(index / 3) * 230,
      },
    data: buildNodeData(node, {
      selectedFeedIndex:
        options?.selectedFeed?.nodeId === node.id ? options.selectedFeed.index : null,
      hoveredFeedIndex:
        options?.hoveredFeed?.nodeId === node.id ? options.hoveredFeed.index : null,
      highlightedAsDestination: Boolean(options?.highlightedDestinationNodeIds?.has(node.id)),
      showDropHint: Boolean(
        options?.connectSourceNodeId && options.connectSourceNodeId !== node.id
      ),
      isConnectSource: options?.connectSourceNodeId === node.id,
      onEditMapping:
        options?.onEditMapping
          ? (mappingIndex) => options.onEditMapping?.(node.id, mappingIndex)
          : undefined,
      onCreateMapping: options?.onCreateMapping
        ? () => options.onCreateMapping?.(node.id)
        : undefined,
      onToggleStream:
        options?.onToggleStream
          ? (mappingIndex) => options.onToggleStream?.(node.id, mappingIndex)
          : undefined,
      onCycleDestination:
        options?.onCycleDestination
          ? (mappingIndex) => options.onCycleDestination?.(node.id, mappingIndex)
          : undefined,
      onHoverMapping:
        options?.onHoverMapping
          ? (mappingIndex) => options.onHoverMapping?.(node.id, mappingIndex)
          : undefined,
    }),
  }));
}

function buildEdges(
  toolchain: ToolChain,
  options?: {
    selectedFeed?: SelectedFeed | null;
    hoveredFeed?: SelectedFeed | null;
    onSelectMapping?: (nodeId: string, index: number, anchor?: CanvasOverlayPosition) => void;
    onEditMapping?: (nodeId: string, index: number, anchor?: CanvasOverlayPosition) => void;
    onToggleStream?: (nodeId: string, index: number) => void;
    onCycleDestination?: (nodeId: string, index: number) => void;
    onCycleSourceMode?: (nodeId: string, index: number) => void;
  }
): Edge[] {
  const list: Edge[] = [];
  const activeFeed = options?.hoveredFeed ?? options?.selectedFeed ?? null;
  const hasActiveFeed = Boolean(activeFeed);
  for (const node of toolchain.nodes) {
    for (const [index, mapping] of (node.feed_mappings ?? []).entries()) {
      const destination = (mapping as feedMapping).destination;
      if (!isEdgeDestinationNode(destination)) continue;
      const isActive =
        activeFeed?.nodeId === node.id && activeFeed.index === index;
      const summary = summarizeMappingSource(mapping as feedMappingOriginal);
      const stream = Boolean((mapping as feedMapping).stream);
      const nextDestinationLabel = destinationLabel(destination);
      const tooltipParts = [
        `${node.id} #${index + 1} -> ${nextDestinationLabel}`,
        `Source: ${summary.modeLabel}`,
        summary.routeText ? `Route: ${summary.routeText}` : null,
        stream ? "Streaming: yes" : "Streaming: no",
      ].filter(Boolean) as string[];
      list.push({
        id: `e-${node.id}-${index}`,
        type: "mappingEdge",
        source: node.id,
        target: destination,
        sourceHandle: `feed-${index}`,
        animated: isActive || Boolean((mapping as feedMapping).stream),
        data: {
          destinationLabel: nextDestinationLabel,
          sourceModeLabel: summary.modeLabel,
          routeText: summary.routeText,
          stream,
          tooltip: tooltipParts.join("\n"),
          onSelect: options?.onSelectMapping
            ? (anchor) => options.onSelectMapping?.(node.id, index, anchor)
            : undefined,
          onEdit: options?.onEditMapping
            ? (anchor) => options.onEditMapping?.(node.id, index, anchor)
            : undefined,
          onToggleStream: options?.onToggleStream
            ? () => options.onToggleStream?.(node.id, index)
            : undefined,
          onCycleDestination: options?.onCycleDestination
            ? () => options.onCycleDestination?.(node.id, index)
            : undefined,
          onCycleSourceMode: options?.onCycleSourceMode
            ? () => options.onCycleSourceMode?.(node.id, index)
            : undefined,
        } as GraphEdgeData,
        style: {
          stroke: "url(#toolchain-edge-gradient)",
          strokeWidth: isActive ? 2.8 : 2,
          opacity: hasActiveFeed ? (isActive ? 1 : 0.3) : 1,
        },
        zIndex: isActive ? 20 : 5,
      });
    }
  }
  return list;
}

function MappingEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  markerEnd,
  style,
  data,
  selected,
}: EdgeProps<GraphEdgeData>) {
  const { zoom } = useViewport();
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });
  const label = `${data?.destinationLabel ?? "NODE"} · ${data?.sourceModeLabel ?? "dry"}${data?.stream ? " · S" : ""}`;
  const labelScale = Math.min(1.3, Math.max(0.92, 1 / Math.max(zoom, 0.01)));
  const showExpandedActions = selected;

  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <div
          className={cn(
            "group nodrag nopan pointer-events-auto absolute flex min-h-9 items-center gap-1.5 rounded-[11px] border px-2.5 py-1.5 font-mono text-[11px] shadow-[0_10px_26px_hsl(var(--background)/0.28)] backdrop-blur-sm",
            selected
              ? "border-cyan-300/60 bg-[linear-gradient(180deg,hsl(var(--background)/0.98),hsl(var(--card)/0.94))] text-foreground"
              : "border-border/70 bg-[linear-gradient(180deg,hsl(var(--background)/0.96),hsl(var(--card)/0.9))] text-muted-foreground"
          )}
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px) scale(${labelScale})`,
            transformOrigin: "center center",
          }}
          title={data?.tooltip}
        >
          <button
            type="button"
            className="truncate text-left hover:text-foreground"
            onMouseDown={(event) => event.stopPropagation()}
            onClick={(event) => {
              event.stopPropagation();
              data?.onSelect?.(eventAnchorFromElement(event.currentTarget));
            }}
            aria-label="Select mapping"
            title={data?.tooltip}
          >
            {label}
          </button>
          <div
            className={cn(
              "ml-0.5 flex items-center gap-1 transition-opacity",
              selected ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            )}
          >
            <button
              type="button"
              className="rounded-[8px] border border-border/70 px-1.5 py-0.5 text-[10px] hover:bg-muted/40 hover:text-foreground"
              onMouseDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                data?.onEdit?.(eventAnchorFromElement(event.currentTarget));
              }}
              aria-label="Open mapping editor"
              title="Open mapping editor"
            >
              {showExpandedActions ? "Edit" : "E"}
            </button>
            <button
              type="button"
              className="rounded-[8px] border border-border/70 px-1.5 py-0.5 text-[10px] hover:bg-muted/40 hover:text-foreground"
              onMouseDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                data?.onCycleDestination?.();
              }}
              aria-label="Cycle destination"
              title="Cycle destination"
            >
              {showExpandedActions ? "Dest" : "D"}
            </button>
            <button
              type="button"
              className="rounded-[8px] border border-border/70 px-1.5 py-0.5 text-[10px] hover:bg-muted/40 hover:text-foreground"
              onMouseDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                data?.onCycleSourceMode?.();
              }}
              aria-label="Cycle source mode"
              title="Cycle source mode"
            >
              {showExpandedActions ? "Mode" : "M"}
            </button>
            <button
              type="button"
              className={cn(
                "rounded-[8px] border px-1.5 py-0.5 text-[10px]",
                data?.stream
                  ? "border-amber-400/70 bg-amber-500/10 text-amber-300"
                  : "border-border/70 text-muted-foreground hover:bg-muted/40 hover:text-foreground"
              )}
              onMouseDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                data?.onToggleStream?.();
              }}
              aria-label={data?.stream ? "Disable stream" : "Enable stream"}
              title={data?.stream ? "Disable stream" : "Enable stream"}
            >
              {showExpandedActions ? (data?.stream ? "Stream off" : "Stream on") : "S"}
            </button>
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

function GraphNodeCard({ data, selected }: NodeProps<GraphNodeData>) {
  const maxRows = Math.max(data.inputKeys.length, data.outputs.length + 1, 3);
  const minHeight = 112 + maxRows * 18;

  return (
    <div
      className={cn(
        "relative w-[286px] rounded-[18px] p-[1px] transition-all duration-150",
        selected
          ? "bg-[linear-gradient(140deg,#ec4899_0%,#8b5cf6_50%,#22d3ee_100%)]"
          : "bg-[linear-gradient(140deg,rgba(236,72,153,0.55)_0%,rgba(139,92,246,0.45)_50%,rgba(34,211,238,0.55)_100%)]",
        selected ? "shadow-[0_0_0_1px_rgba(236,72,153,0.16),0_0_36px_rgba(120,80,220,0.38)]" : "shadow-[0_0_28px_rgba(120,80,220,0.24)]",
        data.highlightedAsDestination ? "ring-2 ring-cyan-300/70 shadow-[0_0_36px_rgba(34,211,238,0.34)]" : undefined,
        data.showDropHint ? "ring-2 ring-emerald-300/70 shadow-[0_0_36px_rgba(52,211,153,0.34)]" : undefined,
        data.isConnectSource ? "opacity-95 saturate-[1.05]" : undefined
      )}
      style={{ minHeight }}
    >
      {data.showDropHint ? (
        <div className="absolute left-3 top-2 z-20 rounded-sm border border-emerald-300/60 bg-emerald-500/10 px-1.5 py-0.5 font-mono text-[10px] text-emerald-200">
          Drop mapping here
        </div>
      ) : null}
      <Handle
        id="in"
        type="target"
        position={Position.Left}
        style={{ top: 38 }}
        className={cn(
          "!h-4 !w-4 !border-2 !bg-background/95",
          data.showDropHint ? "!border-emerald-300" : "!border-[#ec4899]"
        )}
      />

      {data.outputs.map((output) => {
        const top = 62 + output.index * 22;
        const color =
          output.kind === "node"
            ? "#22d3ee"
            : output.kind === "state"
              ? "#f59e0b"
              : "#60a5fa";
        return (
          <Handle
            key={output.index}
            id={`feed-${output.index}`}
            type="source"
            position={Position.Right}
            style={{ top }}
            isConnectable={output.kind === "node"}
            className="!h-4 !w-4 !border-2 !bg-background/95"
            aria-label={`Output ${output.index + 1}`}
          >
            <span
              className="pointer-events-none absolute inset-0 rounded-full"
              style={{ boxShadow: `0 0 0 1px ${color}` }}
            />
          </Handle>
        );
      })}

      <Handle
        id="new-feed"
        type="source"
        position={Position.Right}
        style={{ top: 62 + data.outputs.length * 22 }}
        className="!h-4 !w-4 !border-2 !border-dashed !border-[#a78bfa] !bg-background/95"
        aria-label="Create output mapping"
      />

      <div className="h-full rounded-[17px] bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.10),transparent_26%),radial-gradient(circle_at_top_right,rgba(236,72,153,0.10),transparent_24%),linear-gradient(180deg,rgba(20,20,28,0.97),rgba(12,12,18,0.985))] px-3.5 pb-3.5 pt-3 backdrop-blur-sm transition-colors duration-150">
        <div className="mb-2 flex items-start justify-between gap-2">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground/80">
              Toolchain node
            </div>
            <div className="truncate font-mono text-[12px] font-semibold tracking-[0.03em]">{data.id}</div>
          </div>
          <div className="rounded-full border border-border/60 bg-background/40 px-2 py-0.5 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            {data.apiFunction ? "API" : "Custom"}
          </div>
        </div>
        <div className="mb-3 rounded-[12px] border border-border/70 bg-background/35 px-2.5 py-1.5 text-[11px] text-muted-foreground shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]">
          API: {data.apiFunction ?? "Custom node"}
        </div>

        <div className="grid grid-cols-[1fr_1fr] gap-2 text-[11px]">
          <div className="space-y-1 rounded-[12px] border border-border/50 bg-background/25 p-2">
            <div className="flex items-center justify-between gap-2">
              <div className="font-semibold uppercase tracking-[0.16em] text-muted-foreground">Inputs</div>
              <div className="rounded-full border border-border/50 bg-background/45 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                {data.inputKeys.length}
              </div>
            </div>
            {data.inputKeys.length ? (
              data.inputKeys.map((key) => (
                <div key={key} className="truncate rounded-[9px] border border-border/40 bg-muted/15 px-1.5 py-1 font-mono">
                  {key}
                </div>
              ))
            ) : (
              <div className="text-muted-foreground/80">No inputs</div>
            )}
          </div>
          <div className="space-y-1 rounded-[12px] border border-border/50 bg-background/25 p-2">
            <div className="flex items-center justify-between gap-2">
              <div className="font-semibold uppercase tracking-[0.16em] text-muted-foreground">Outputs</div>
              <div className="rounded-full border border-border/50 bg-background/45 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                {data.outputs.length}
              </div>
            </div>
            {data.outputs.length ? (
              data.outputs.map((output) => (
                <div
                  key={output.index}
                  className={cn(
                    "flex items-center gap-1 rounded-[9px] border border-border/40 bg-muted/15 px-1.5 py-1 transition-colors duration-150",
                    data.selectedFeedIndex === output.index ? "ring-1 ring-primary/60" : undefined,
                    data.hoveredFeedIndex === output.index ? "bg-muted/45" : undefined
                  )}
                  onMouseEnter={() => data.onHoverMapping?.(output.index)}
                  onMouseLeave={() => data.onHoverMapping?.(null)}
                >
                  <button
                    type="button"
                    className="truncate font-mono text-left hover:text-foreground"
                    onMouseDown={(event) => event.stopPropagation()}
                    onClick={(event) => {
                      event.stopPropagation();
                      data.onEditMapping?.(output.index);
                    }}
                    >
                    {destinationLabel(output.destination)}
                  </button>
                  <button
                    type="button"
                    className="rounded-[8px] border border-border/70 px-1.5 font-mono text-[10px] text-muted-foreground hover:bg-muted/40 hover:text-foreground"
                    title="Cycle destination"
                    onMouseDown={(event) => event.stopPropagation()}
                    onClick={(event) => {
                      event.stopPropagation();
                      data.onCycleDestination?.(output.index);
                    }}
                  >
                    D
                  </button>
                  <button
                    type="button"
                    className={cn(
                      "ml-auto rounded-[8px] border px-1.5 font-mono text-[10px]",
                      output.stream
                        ? "border-amber-400/70 bg-amber-500/10 text-amber-300"
                        : "border-border/70 text-muted-foreground hover:bg-muted/40"
                    )}
                    title={output.stream ? "Disable stream" : "Enable stream"}
                    onMouseDown={(event) => event.stopPropagation()}
                    onClick={(event) => {
                      event.stopPropagation();
                      data.onToggleStream?.(output.index);
                    }}
                  >
                    S
                  </button>
                </div>
              ))
            ) : (
              <div className="text-muted-foreground/80">No mappings</div>
            )}
            <button
              type="button"
              className="w-full rounded-[10px] border border-dashed border-border/80 bg-background/20 px-2 py-1.5 text-left text-muted-foreground hover:bg-muted/35"
              onMouseDown={(event) => event.stopPropagation()}
              onClick={(event) => {
                event.stopPropagation();
                data.onCreateMapping?.();
              }}
            >
              + new mapping
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function mappingToForm(mapping: feedMappingOriginal): MappingEditorForm {
  const source = mapping as unknown as Record<string, unknown>;
  if ("value" in source) {
    return {
      destination: mapping.destination,
      stream: Boolean(mapping.stream),
      sourceMode: "static",
      valueText: JSON.stringify(source.value ?? null, null, 2),
      routeText: "",
    };
  }
  if ("getFromState" in source) {
    const route = (source.getFromState as { route?: staticRoute } | undefined)?.route;
    return {
      destination: mapping.destination,
      stream: Boolean(mapping.stream),
      sourceMode: "state",
      valueText: "",
      routeText: routeToText(route),
    };
  }
  if ("getFromInputs" in source) {
    const route = (source.getFromInputs as { route?: staticRoute } | undefined)?.route;
    return {
      destination: mapping.destination,
      stream: Boolean(mapping.stream),
      sourceMode: "node_input",
      valueText: "",
      routeText: routeToText(route),
    };
  }
  if ("getFromOutputs" in source) {
    const route = (source.getFromOutputs as { route?: staticRoute } | undefined)?.route;
    return {
      destination: mapping.destination,
      stream: Boolean(mapping.stream),
      sourceMode: "node_output",
      valueText: "",
      routeText: routeToText(route),
    };
  }
  return {
    destination: mapping.destination,
    stream: Boolean(mapping.stream),
    sourceMode: "dry",
    valueText: "",
    routeText: "",
  };
}

const NODE_TYPES = { toolchainV2: GraphNodeCard };
const EDGE_TYPES = { mappingEdge: MappingEdge };

function inputToForm(input: nodeInputArgument): InputEditorForm {
  if (input.from_user) {
    return {
      key: input.key,
      typeHint: input.type_hint ?? "",
      optional: Boolean(input.optional),
      sourceMode: "user_input",
      valueText: "",
      routeText: "",
    };
  }
  if (input.from_server) {
    return {
      key: input.key,
      typeHint: input.type_hint ?? "",
      optional: Boolean(input.optional),
      sourceMode: "server_argument",
      valueText: "",
      routeText: "",
    };
  }
  if (input.value !== undefined) {
    return {
      key: input.key,
      typeHint: input.type_hint ?? "",
      optional: Boolean(input.optional),
      sourceMode: "static_value",
      valueText: JSON.stringify(input.value, null, 2),
      routeText: "",
    };
  }
  if (input.from_state?.route) {
    return {
      key: input.key,
      typeHint: input.type_hint ?? "",
      optional: Boolean(input.optional),
      sourceMode: "toolchain_state",
      valueText: "",
      routeText: routeToText(input.from_state.route),
    };
  }
  if (input.from_files?.route || input.from_files?.routes?.[0]) {
    return {
      key: input.key,
      typeHint: input.type_hint ?? "",
      optional: Boolean(input.optional),
      sourceMode: "files",
      valueText: "",
      routeText: routeToText(input.from_files?.route ?? input.from_files?.routes?.[0]),
    };
  }
  return {
    key: input.key,
    typeHint: input.type_hint ?? "",
    optional: Boolean(input.optional),
    sourceMode: "none",
    valueText: "",
    routeText: "",
  };
}

export default function ToolchainGraphEditorClient({ params }: Props) {
  const { userData, authReviewed, loginValid, apiFunctionSpecs } = useContextAction();
  const searchParams = useSearchParams();
  const [toolchain, setToolchain] = useState<ToolChain | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);
  const [baselineToolchainSerialized, setBaselineToolchainSerialized] = useState("");
  const [undoStack, setUndoStack] = useState<ToolChain[]>([]);
  const [redoStack, setRedoStack] = useState<ToolChain[]>([]);
  const historyModeRef = useRef<"record" | "skip">("record");
  const previousToolchainRef = useRef<ToolChain | null>(null);
  const [focusCanvas, setFocusCanvas] = useState(false);
  const [editorSurface, setEditorSurface] = useState<"modal" | "drawer">("modal");
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedFeed, setSelectedFeed] = useState<SelectedFeed | null>(null);
  const [hoveredFeed, setHoveredFeed] = useState<SelectedFeed | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<GraphNodeData>([]);
  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance<GraphNodeData, Edge> | null>(null);
  const stableNodeTypes = useMemo(() => NODE_TYPES, []);
  const stableEdgeTypes = useMemo(() => EDGE_TYPES, []);
  const [contextMenuFlowPosition, setContextMenuFlowPosition] = useState<{
    x: number;
    y: number;
  } | null>(null);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const [canvasMappingPosition, setCanvasMappingPosition] = useState<CanvasOverlayPosition | null>(null);
  const [canvasInputPosition, setCanvasInputPosition] = useState<CanvasOverlayPosition | null>(null);
  const [hoveredApiFunctionId, setHoveredApiFunctionId] = useState<string | null>(null);
  const [urlEditorInitialized, setUrlEditorInitialized] = useState(false);
  const [connectSourceNodeId, setConnectSourceNodeId] = useState<string | null>(null);

  const [mappingEditorTarget, setMappingEditorTarget] = useState<SelectedFeed | null>(null);
  const [mappingEditorForm, setMappingEditorForm] = useState<MappingEditorForm>({
    destination: "<<STATE>>",
    stream: false,
    sourceMode: "dry",
    valueText: "",
    routeText: "",
  });

  const [inputEditorTarget, setInputEditorTarget] = useState<InputEditorTarget | null>(null);
  const [inputEditorSurfaceMode, setInputEditorSurfaceMode] = useState<"full" | "canvas">("full");
  const [inputEditorForm, setInputEditorForm] = useState<InputEditorForm>({
    key: "",
    typeHint: "",
    optional: false,
    sourceMode: "none",
    valueText: "",
    routeText: "",
  });
  const [inlineMappingForm, setInlineMappingForm] = useState<MappingEditorForm | null>(null);
  const [routeTokenDragIndex, setRouteTokenDragIndex] = useState<number | null>(null);
  const [newRouteSegment, setNewRouteSegment] = useState("");

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) return;
    fetchToolchainConfig({
      auth: userData.auth,
      toolchain_id: params.toolchainId,
      onFinish: (result: ToolChain) => {
        historyModeRef.current = "skip";
        previousToolchainRef.current = null;
        setUndoStack([]);
        setRedoStack([]);
        setToolchain(result);
        setBaselineToolchainSerialized(JSON.stringify(result));
        setFocusCanvas(Boolean(result.editor_meta?.graph?.focus_canvas));
        setEditorSurface(result.editor_meta?.graph?.editor_surface === "drawer" ? "drawer" : "modal");
        setCanvasMappingPosition(null);
        setCanvasInputPosition(null);
        setInputEditorSurfaceMode("full");
      },
    });
  }, [authReviewed, loginValid, userData?.auth, params.toolchainId]);

  useEffect(() => {
    if (!toolchain) {
      previousToolchainRef.current = null;
      return;
    }

    const currentSnapshot = cloneToolchainSnapshot(toolchain);
    if (!previousToolchainRef.current) {
      previousToolchainRef.current = currentSnapshot;
      historyModeRef.current = "record";
      return;
    }

    if (historyModeRef.current === "record") {
      const previousSnapshot = previousToolchainRef.current;
      setUndoStack((prev) => [...prev, previousSnapshot].slice(-HISTORY_LIMIT));
      setRedoStack([]);
    }

    previousToolchainRef.current = currentSnapshot;
    historyModeRef.current = "record";
  }, [toolchain]);

  useEffect(() => {
    if (!toolchain) return;
    const fallbackSelected =
      selectedNodeId && toolchain.nodes.some((node) => node.id === selectedNodeId)
        ? selectedNodeId
        : (toolchain.nodes[0]?.id ?? null);
    setSelectedNodeId(fallbackSelected);

    const selectNodeInline = (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setNodes((prev) =>
        prev.map((entry) => ({
          ...entry,
          selected: entry.id === nodeId,
          data: {
            ...entry.data,
            selectedFeedIndex:
              selectedFeed?.nodeId === entry.id ? selectedFeed.index : null,
          },
        }))
      );
    };

    const openMappingInline = (nodeId: string, index: number) => {
      const node = toolchain.nodes.find((entry) => entry.id === nodeId);
      const mapping = node?.feed_mappings?.[index] as feedMappingOriginal | undefined;
      if (!node || !mapping) return;
      setInputEditorTarget(null);
      setInputEditorSurfaceMode("full");
      setCanvasInputPosition(null);
      setCanvasMappingPosition(null);
      setMappingEditorForm(mappingToForm(mapping));
      setMappingEditorTarget({ nodeId, index });
      setSelectedFeed({ nodeId, index });
      setHoveredFeed(null);
      selectNodeInline(nodeId);
    };

    const createMappingInline = (nodeId: string) => {
      const sourceNode = toolchain.nodes.find((entry) => entry.id === nodeId);
      const nextIndex = sourceNode?.feed_mappings?.length ?? 0;
      setToolchain((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          nodes: prev.nodes.map((node) =>
            node.id === nodeId
              ? {
                  ...node,
                  feed_mappings: [
                    ...(node.feed_mappings ?? []),
                    { destination: "<<STATE>>" } as feedMappingOriginal,
                  ],
                }
              : node
          ),
        };
      });
      setCanvasMappingPosition(null);
      setMappingEditorForm({
        destination: "<<STATE>>",
        stream: false,
        sourceMode: "dry",
        valueText: "",
        routeText: "",
      });
      setInputEditorTarget(null);
      setMappingEditorTarget({ nodeId, index: nextIndex });
      setSelectedFeed({ nodeId, index: nextIndex });
      setHoveredFeed(null);
      selectNodeInline(nodeId);
    };

    const toggleStreamInline = (nodeId: string, index: number) => {
      setToolchain((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          nodes: prev.nodes.map((node) => {
            if (node.id !== nodeId) return node;
            const current = node.feed_mappings ?? [];
            if (index < 0 || index >= current.length) return node;
            const nextMappings = [...current];
            const currentMapping = nextMappings[index] as feedMappingOriginal;
            nextMappings[index] = {
              ...currentMapping,
              ...(currentMapping.stream ? { stream: undefined } : { stream: true }),
            } as feedMappingOriginal;
            return { ...node, feed_mappings: nextMappings };
          }),
        };
      });
    };

    const cycleDestinationInline = (nodeId: string, index: number) => {
      setToolchain((prev) => {
        if (!prev) return prev;
        const allNodeIds = prev.nodes.map((node) => node.id);
        return {
          ...prev,
          nodes: prev.nodes.map((node) => {
            if (node.id !== nodeId) return node;
            const currentMappings = node.feed_mappings ?? [];
            if (index < 0 || index >= currentMappings.length) return node;
            const nextMappings = [...currentMappings];
            const currentMapping = nextMappings[index] as feedMappingOriginal;
            nextMappings[index] = {
              ...currentMapping,
              destination: nextMappingDestination(
                nodeId,
                currentMapping.destination,
                allNodeIds
              ),
            } as feedMappingOriginal;
            return { ...node, feed_mappings: nextMappings };
          }),
        };
      });
      setSelectedFeed({ nodeId, index });
      setHoveredFeed({ nodeId, index });
      selectNodeInline(nodeId);
    };

    const hoverMappingInline = (nodeId: string, index: number | null) => {
      if (index === null) {
        setHoveredFeed(null);
        return;
      }
      setHoveredFeed({ nodeId, index });
    };

    const activeFeed = hoveredFeed ?? selectedFeed;
    const highlightedDestinationNodeIds = new Set<string>();
    if (activeFeed) {
      const sourceNode = toolchain.nodes.find((entry) => entry.id === activeFeed.nodeId);
      const mapping = sourceNode?.feed_mappings?.[activeFeed.index] as feedMappingOriginal | undefined;
      if (mapping && isEdgeDestinationNode(mapping.destination)) {
        highlightedDestinationNodeIds.add(mapping.destination);
      }
    }

    setNodes(
      buildNodes(toolchain, {
        selectedNodeId: fallbackSelected,
        selectedFeed,
        hoveredFeed,
        highlightedDestinationNodeIds,
        connectSourceNodeId,
        onEditMapping: openMappingInline,
        onCreateMapping: createMappingInline,
        onToggleStream: toggleStreamInline,
        onCycleDestination: cycleDestinationInline,
        onHoverMapping: hoverMappingInline,
      })
    );
  }, [connectSourceNodeId, hoveredFeed, selectedFeed, selectedNodeId, setNodes, toolchain]);

  useEffect(() => {
    if (!selectedFeed || !toolchain) return;
    const node = toolchain.nodes.find((entry) => entry.id === selectedFeed.nodeId);
    const feedMappings = node?.feed_mappings ?? [];
    if (!node || selectedFeed.index < 0 || selectedFeed.index >= feedMappings.length) {
      setSelectedFeed(null);
    }
  }, [selectedFeed, toolchain]);

  useEffect(() => {
    if (!hoveredFeed || !toolchain) return;
    const node = toolchain.nodes.find((entry) => entry.id === hoveredFeed.nodeId);
    const feedMappings = node?.feed_mappings ?? [];
    if (!node || hoveredFeed.index < 0 || hoveredFeed.index >= feedMappings.length) {
      setHoveredFeed(null);
    }
  }, [hoveredFeed, toolchain]);

  useEffect(() => {
    if (!mappingEditorTarget || !toolchain) return;
    const node = toolchain.nodes.find((entry) => entry.id === mappingEditorTarget.nodeId);
    const mapping = node?.feed_mappings?.[mappingEditorTarget.index] as feedMappingOriginal | undefined;
    if (!node || !mapping) {
      setMappingEditorTarget(null);
    }
  }, [mappingEditorTarget, toolchain]);

  useEffect(() => {
    if (!inputEditorTarget || !toolchain) return;
    const node = toolchain.nodes.find((entry) => entry.id === inputEditorTarget.nodeId);
    if (!node) {
      setInputEditorTarget(null);
      return;
    }
    if (inputEditorTarget.index === null) return;
    const exists = Boolean(node.input_arguments?.[inputEditorTarget.index]);
    if (!exists) {
      setInputEditorTarget(null);
    }
  }, [inputEditorTarget, toolchain]);

  const toggleFeedStreamFromEdge = useCallback((nodeId: string, index: number) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((node) => {
          if (node.id !== nodeId) return node;
          const currentMappings = node.feed_mappings ?? [];
          if (index < 0 || index >= currentMappings.length) return node;
          const nextMappings = [...currentMappings];
          const currentMapping = nextMappings[index] as feedMappingOriginal;
          nextMappings[index] = {
            ...currentMapping,
            ...(currentMapping.stream ? { stream: undefined } : { stream: true }),
          } as feedMappingOriginal;
          return { ...node, feed_mappings: nextMappings };
        }),
      };
    });
    setSelectedNodeId(nodeId);
    setSelectedFeed({ nodeId, index });
    setHoveredFeed({ nodeId, index });
  }, []);

  const cycleFeedDestinationFromEdge = useCallback((nodeId: string, index: number) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      const allNodeIds = prev.nodes.map((node) => node.id);
      return {
        ...prev,
        nodes: prev.nodes.map((node) => {
          if (node.id !== nodeId) return node;
          const currentMappings = node.feed_mappings ?? [];
          if (index < 0 || index >= currentMappings.length) return node;
          const nextMappings = [...currentMappings];
          const currentMapping = nextMappings[index] as feedMappingOriginal;
          nextMappings[index] = {
            ...currentMapping,
            destination: nextMappingDestination(
              nodeId,
              currentMapping.destination,
              allNodeIds
            ),
          } as feedMappingOriginal;
          return { ...node, feed_mappings: nextMappings };
        }),
      };
    });
    setSelectedNodeId(nodeId);
    setSelectedFeed({ nodeId, index });
    setHoveredFeed({ nodeId, index });
  }, []);

  const cycleFeedSourceModeFromEdge = useCallback((nodeId: string, index: number) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((node) => {
          if (node.id !== nodeId) return node;
          const currentMappings = node.feed_mappings ?? [];
          if (index < 0 || index >= currentMappings.length) return node;
          const nextMappings = [...currentMappings];
          const currentMapping = nextMappings[index] as feedMappingOriginal;
          nextMappings[index] = cycleMappingSourceMode(currentMapping);
          return { ...node, feed_mappings: nextMappings };
        }),
      };
    });
    setSelectedNodeId(nodeId);
    setSelectedFeed({ nodeId, index });
    setHoveredFeed({ nodeId, index });
  }, []);

  const toolchainNodeIds = useMemo(() => {
    if (!toolchain) return [] as string[];
    return toolchain.nodes.map((node) => node.id);
  }, [toolchain]);

  const sortedApiFunctionSpecs = useMemo(() => {
    return [...(apiFunctionSpecs ?? [])].sort((a, b) =>
      a.api_function_id.localeCompare(b.api_function_id)
    );
  }, [apiFunctionSpecs]);

  const hoveredApiFunction = useMemo(() => {
    if (!sortedApiFunctionSpecs.length) return null;
    if (!hoveredApiFunctionId) return sortedApiFunctionSpecs[0];
    return (
      sortedApiFunctionSpecs.find((spec) => spec.api_function_id === hoveredApiFunctionId) ??
      sortedApiFunctionSpecs[0]
    );
  }, [hoveredApiFunctionId, sortedApiFunctionSpecs]);

  const selectedNode = useMemo(() => {
    if (!toolchain || !selectedNodeId) return null;
    return toolchain.nodes.find((node) => node.id === selectedNodeId) ?? null;
  }, [selectedNodeId, toolchain]);

  const selectedFeedMapping = useMemo(() => {
    if (!selectedFeed || !toolchain) return null;
    const node = toolchain.nodes.find((entry) => entry.id === selectedFeed.nodeId);
    if (!node) return null;
    return (node.feed_mappings?.[selectedFeed.index] ?? null) as feedMappingOriginal | null;
  }, [selectedFeed, toolchain]);

  const selectedFeedSummary = useMemo(() => {
    if (!selectedFeed || !selectedFeedMapping) return null;
    const summary = summarizeMappingSource(selectedFeedMapping);
    return {
      label: `${selectedFeed.nodeId} #${selectedFeed.index + 1}`,
      destination: destinationLabel(selectedFeedMapping.destination),
      sourceMode: summary.modeLabel,
      routeText: summary.routeText,
      stream: Boolean((selectedFeedMapping as feedMapping).stream),
    };
  }, [selectedFeed, selectedFeedMapping]);

  const hasUnsavedChanges = useMemo(() => {
    if (!toolchain || !baselineToolchainSerialized) return false;
    return JSON.stringify(toolchain) !== baselineToolchainSerialized;
  }, [baselineToolchainSerialized, toolchain]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!hasUnsavedChanges) return;
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [hasUnsavedChanges]);

  useEffect(() => {
    if (!selectedFeed || !selectedFeedMapping) {
      setInlineMappingForm(null);
      setNewRouteSegment("");
      setRouteTokenDragIndex(null);
      return;
    }
    setInlineMappingForm(mappingToForm(selectedFeedMapping));
    setNewRouteSegment("");
    setRouteTokenDragIndex(null);
  }, [canvasMappingPosition, selectedFeed, selectedFeedMapping]);

  const mappingEditorNode = useMemo(() => {
    if (!toolchain || !mappingEditorTarget) return null;
    return toolchain.nodes.find((entry) => entry.id === mappingEditorTarget.nodeId) ?? null;
  }, [mappingEditorTarget, toolchain]);

  const mappingEditorMapping = useMemo(() => {
    if (!mappingEditorNode || !mappingEditorTarget) return null;
    return (mappingEditorNode.feed_mappings?.[mappingEditorTarget.index] ?? null) as
      | feedMappingOriginal
      | null;
  }, [mappingEditorNode, mappingEditorTarget]);

  const inputEditorNode = useMemo(() => {
    if (!toolchain || !inputEditorTarget) return null;
    return toolchain.nodes.find((entry) => entry.id === inputEditorTarget.nodeId) ?? null;
  }, [inputEditorTarget, toolchain]);

  const inputEditorInput = useMemo(() => {
    if (!inputEditorNode || !inputEditorTarget || inputEditorTarget.index === null) return null;
    return inputEditorNode.input_arguments?.[inputEditorTarget.index] ?? null;
  }, [inputEditorNode, inputEditorTarget]);

  const clampCanvasOverlayPosition = useCallback((x: number, y: number, width: number, height: number): CanvasOverlayPosition => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) {
      return { x: 16, y: 16 };
    }
    const margin = 16;
    return {
      x: Math.min(Math.max(x, margin), Math.max(margin, rect.width - width - margin)),
      y: Math.min(Math.max(y, margin), Math.max(margin, rect.height - height - margin)),
    };
  }, []);

  const resolveCanvasOverlayPosition = useCallback((clientX: number, clientY: number, width: number, height: number): CanvasOverlayPosition => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) {
      return { x: 16, y: 16 };
    }
    const margin = 16;
    const x = Math.min(Math.max(clientX - rect.left + 14, margin), Math.max(margin, rect.width - width - margin));
    const y = Math.min(Math.max(clientY - rect.top + 14, margin), Math.max(margin, rect.height - height - margin));
    return { x, y };
  }, []);

  const clearCanvasOverlays = useCallback(() => {
    setCanvasMappingPosition(null);
    setCanvasInputPosition(null);
  }, []);

  const selectNode = useCallback(
    (nodeId: string, options?: { preserveCanvasOverlays?: boolean }) => {
      if (!options?.preserveCanvasOverlays) {
        clearCanvasOverlays();
        setInputEditorSurfaceMode("full");
      }
      setSelectedNodeId(nodeId);
      setNodes((prev) =>
        prev.map((entry) => ({
          ...entry,
          selected: entry.id === nodeId,
        }))
      );
    },
    [clearCanvasOverlays, setNodes]
  );

  const selectFeedFromEdge = useCallback((nodeId: string, index: number, anchor?: CanvasOverlayPosition) => {
    const node = toolchain?.nodes.find((entry) => entry.id === nodeId);
    const mapping = node?.feed_mappings?.[index] as feedMappingOriginal | undefined;
    if (!node || !mapping) return;
    selectNode(nodeId, { preserveCanvasOverlays: true });
    setSelectedFeed({ nodeId, index });
    setHoveredFeed({ nodeId, index });
    setCanvasInputPosition(null);
    setMappingEditorTarget(null);
    setInlineMappingForm(mappingToForm(mapping));
    setNewRouteSegment("");
    setRouteTokenDragIndex(null);
    if (anchor) {
      setCanvasMappingPosition(resolveCanvasOverlayPosition(anchor.x, anchor.y, 390, 430));
    }
  }, [resolveCanvasOverlayPosition, selectNode, toolchain]);

  const openSelectedFeedQuickEditor = useCallback(() => {
    if (!selectedFeed) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    if (rect) {
      selectFeedFromEdge(selectedFeed.nodeId, selectedFeed.index, {
        x: rect.left + Math.min(rect.width * 0.7, rect.width - 220),
        y: rect.top + 96,
      });
      return;
    }
    selectFeedFromEdge(selectedFeed.nodeId, selectedFeed.index);
  }, [selectFeedFromEdge, selectedFeed]);

  const openFeedEditorFromEdge = useCallback(
    (nodeId: string, index: number, anchor?: CanvasOverlayPosition) => {
      const node = toolchain?.nodes.find((entry) => entry.id === nodeId);
      const mapping = node?.feed_mappings?.[index] as feedMappingOriginal | undefined;
      if (!node || !mapping) return;
      setInputEditorTarget(null);
      setInputEditorSurfaceMode("full");
      setCanvasInputPosition(null);
      setCanvasMappingPosition(null);
      setMappingEditorForm(mappingToForm(mapping));
      setMappingEditorTarget({ nodeId, index });
      setSelectedNodeId(nodeId);
      setSelectedFeed({ nodeId, index });
      setHoveredFeed({ nodeId, index });
    },
    [clampCanvasOverlayPosition, toolchain]
  );

  const edges = useMemo(() => {
    if (!toolchain) return [] as Edge[];
    return buildEdges(toolchain, {
      selectedFeed,
      hoveredFeed,
      onSelectMapping: selectFeedFromEdge,
      onEditMapping: openFeedEditorFromEdge,
      onToggleStream: toggleFeedStreamFromEdge,
      onCycleDestination: cycleFeedDestinationFromEdge,
      onCycleSourceMode: cycleFeedSourceModeFromEdge,
    });
  }, [
    cycleFeedDestinationFromEdge,
    cycleFeedSourceModeFromEdge,
    hoveredFeed,
    openFeedEditorFromEdge,
    selectFeedFromEdge,
    selectedFeed,
    toggleFeedStreamFromEdge,
    toolchain,
  ]);

  const persistNodePosition = (nodeId: string, position: { x: number; y: number }) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      const nextNodes = {
        ...(prev.editor_meta?.graph?.nodes ?? {}),
        [nodeId]: { x: position.x, y: position.y },
      };
      return {
        ...prev,
        editor_meta: {
          ...(prev.editor_meta ?? {}),
          graph: {
            ...(prev.editor_meta?.graph ?? {}),
            nodes: nextNodes,
          },
        },
      };
    });
  };

  const persistViewport = (viewport: Viewport) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        editor_meta: {
          ...(prev.editor_meta ?? {}),
          graph: {
            ...(prev.editor_meta?.graph ?? {}),
            viewport: { x: viewport.x, y: viewport.y, zoom: viewport.zoom },
          },
        },
      };
    });
  };

  const updateNode = (nodeId: string, updater: (node: toolchainNode) => toolchainNode) => {
    setToolchain((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        nodes: prev.nodes.map((node) => (node.id === nodeId ? updater(node) : node)),
      };
    });
  };

  const updateFeedMapping = (
    nodeId: string,
    index: number,
    updater: (mapping: feedMappingOriginal) => feedMappingOriginal
  ) => {
    updateNode(nodeId, (node) => {
      const current = node.feed_mappings ?? [];
      if (index < 0 || index >= current.length) return node;
      const nextMappings = [...current];
      nextMappings[index] = updater(nextMappings[index] as feedMappingOriginal);
      return { ...node, feed_mappings: nextMappings };
    });
  };

  const updateInputArgument = (
    nodeId: string,
    index: number,
    updater: (input: nodeInputArgument) => nodeInputArgument
  ) => {
    updateNode(nodeId, (node) => {
      const current = node.input_arguments ?? [];
      if (index < 0 || index >= current.length) return node;
      const next = [...current];
      next[index] = updater(next[index]);
      return { ...node, input_arguments: next };
    });
  };

  const addFeedMapping = (nodeId: string, destination: string) => {
    updateNode(nodeId, (node) => {
      const nextMappings = [
        ...(node.feed_mappings ?? []),
        { destination } as feedMappingOriginal,
      ];
      return { ...node, feed_mappings: nextMappings };
    });
  };

  const createMappingAndOpen = (nodeId: string, destination: string) => {
    const sourceNode = toolchain?.nodes.find((node) => node.id === nodeId);
    const nextIndex = sourceNode?.feed_mappings?.length ?? 0;
    addFeedMapping(nodeId, destination);
    setMappingEditorForm({
      destination,
      stream: false,
      sourceMode: "dry",
      valueText: "",
      routeText: "",
    });
    setMappingEditorTarget({ nodeId, index: nextIndex });
    setSelectedFeed({ nodeId, index: nextIndex });
    setHoveredFeed(null);
    selectNode(nodeId);
  };

  const addInputArgument = (nodeId: string, newInput: nodeInputArgument) => {
    updateNode(nodeId, (node) => ({
      ...node,
      input_arguments: [...(node.input_arguments ?? []), newInput],
    }));
  };

  const removeFeedMappingEdge = (nodeId: string, index: number) => {
    updateNode(nodeId, (node) => {
      const current = node.feed_mappings ?? [];
      if (index < 0 || index >= current.length) return node;
      return {
        ...node,
        feed_mappings: current.filter((_mapping, mappingIndex) => mappingIndex !== index),
      };
    });
    if (selectedFeed && selectedFeed.nodeId === nodeId && selectedFeed.index === index) {
      setSelectedFeed(null);
    }
    if (hoveredFeed && hoveredFeed.nodeId === nodeId && hoveredFeed.index === index) {
      setHoveredFeed(null);
    }
  };

  const removeInputArgument = (nodeId: string, index: number) => {
    updateNode(nodeId, (node) => {
      const current = node.input_arguments ?? [];
      if (index < 0 || index >= current.length) return node;
      return {
        ...node,
        input_arguments: current.filter((_input, inputIndex) => inputIndex !== index),
      };
    });
  };

  const createNodeAtContextPosition = ({
    idBase,
    apiFunction,
    inputArguments,
  }: {
    idBase: string;
    apiFunction?: string;
    inputArguments?: nodeInputArgument[];
  }) => {
    const position = contextMenuFlowPosition ?? { x: 220, y: 180 };
    let createdNodeId: string | null = null;
    setToolchain((prev) => {
      if (!prev) return prev;
      const existingIds = new Set(prev.nodes.map((node) => node.id));
      const nextId = uniqueNodeId(sanitizeNodeId(idBase), existingIds);
      createdNodeId = nextId;
      return {
        ...prev,
        nodes: [
          ...prev.nodes,
          {
            id: nextId,
            ...(apiFunction ? { api_function: apiFunction } : {}),
            input_arguments: inputArguments ?? [],
            feed_mappings: [],
          },
        ],
        editor_meta: {
          ...(prev.editor_meta ?? {}),
          graph: {
            ...(prev.editor_meta?.graph ?? {}),
            nodes: {
              ...(prev.editor_meta?.graph?.nodes ?? {}),
              [nextId]: { x: position.x, y: position.y },
            },
          },
        },
      };
    });
    if (createdNodeId) {
      setSelectedFeed(null);
      setHoveredFeed(null);
      setSelectedNodeId(createdNodeId);
      toast.success(`Added node ${createdNodeId}`);
    }
  };

  const addTestItemNode = () => {
    createNodeAtContextPosition({
      idBase: "test_item",
      inputArguments: [{ key: "query" }],
    });
  };

  const addEmptyNode = () => {
    createNodeAtContextPosition({ idBase: "node" });
  };

  const addApiFunctionNode = (spec: APIFunctionSpec) => {
    createNodeAtContextPosition({
      idBase: spec.api_function_id,
      apiFunction: spec.api_function_id,
      inputArguments: spec.function_args.map((arg) => ({
        key: arg.keyword,
        ...(arg.type_hint ? { type_hint: arg.type_hint } : {}),
        ...(arg.default_value !== undefined ? { value: arg.default_value, optional: true } : {}),
      })),
    });
  };

  const toggleFocusCanvas = () => {
    setFocusCanvas((prevFocus) => {
      const nextFocus = !prevFocus;
      setToolchain((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          editor_meta: {
            ...(prev.editor_meta ?? {}),
            graph: {
              ...(prev.editor_meta?.graph ?? {}),
              focus_canvas: nextFocus,
            },
          },
        };
      });
      return nextFocus;
    });
  };

  const toggleEditorSurface = () => {
    setEditorSurface((prevSurface) => {
      const nextSurface: "modal" | "drawer" = prevSurface === "modal" ? "drawer" : "modal";
      setToolchain((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          editor_meta: {
            ...(prev.editor_meta ?? {}),
            graph: {
              ...(prev.editor_meta?.graph ?? {}),
              editor_surface: nextSurface,
            },
          },
        };
      });
      return nextSurface;
    });
  };

  const undoChanges = useCallback(() => {
    if (!toolchain || undoStack.length === 0) return;
    const previousSnapshot = undoStack[undoStack.length - 1];
    historyModeRef.current = "skip";
    setUndoStack((prev) => prev.slice(0, -1));
    setRedoStack((prev) => [...prev, cloneToolchainSnapshot(toolchain)].slice(-HISTORY_LIMIT));
    setToolchain(cloneToolchainSnapshot(previousSnapshot));
    setMappingEditorTarget(null);
    setInputEditorTarget(null);
    toast.success("Undid latest graph edit.");
  }, [toolchain, undoStack]);

  const redoChanges = useCallback(() => {
    if (!toolchain || redoStack.length === 0) return;
    const nextSnapshot = redoStack[redoStack.length - 1];
    historyModeRef.current = "skip";
    setRedoStack((prev) => prev.slice(0, -1));
    setUndoStack((prev) => [...prev, cloneToolchainSnapshot(toolchain)].slice(-HISTORY_LIMIT));
    setToolchain(cloneToolchainSnapshot(nextSnapshot));
    setMappingEditorTarget(null);
    setInputEditorTarget(null);
    toast.success("Redid graph edit.");
  }, [redoStack, toolchain]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const isMetaPressed = event.metaKey || event.ctrlKey;
      if (!isMetaPressed) return;
      const target = event.target as HTMLElement | null;
      const tagName = target?.tagName?.toLowerCase();
      const isEditable =
        tagName === "input" || tagName === "textarea" || Boolean(target?.isContentEditable);
      if (isEditable) return;

      const key = event.key.toLowerCase();
      const wantsUndo = key === "z" && !event.shiftKey;
      const wantsRedo = (key === "z" && event.shiftKey) || key === "y";
      if (!wantsUndo && !wantsRedo) return;

      event.preventDefault();
      if (wantsUndo) {
        undoChanges();
      } else {
        redoChanges();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [redoChanges, undoChanges]);

  const openMappingEditor = useCallback(
    (nodeId: string, index: number) => {
      const node = toolchain?.nodes.find((entry) => entry.id === nodeId);
      const mapping = node?.feed_mappings?.[index] as feedMappingOriginal | undefined;
      if (!node || !mapping) return;
      setInputEditorTarget(null);
      setInputEditorSurfaceMode("full");
      setCanvasInputPosition(null);
      setCanvasMappingPosition(null);
      setMappingEditorForm(mappingToForm(mapping));
      setMappingEditorTarget({ nodeId, index });
      selectNode(nodeId);
      setSelectedFeed({ nodeId, index });
      setHoveredFeed(null);
    },
    [selectNode, toolchain]
  );

  const openInputEditor = useCallback(
    (
      nodeId: string,
      index: number | null,
      options?: { surface?: "full" | "canvas"; anchor?: CanvasOverlayPosition | null }
    ) => {
      const surface = options?.surface ?? "full";
      const node = toolchain?.nodes.find((entry) => entry.id === nodeId);
      if (!node) return;
      selectNode(nodeId, { preserveCanvasOverlays: surface === "canvas" });
      setInputEditorSurfaceMode(surface);
      if (surface === "canvas") {
        setCanvasInputPosition(options?.anchor ?? { x: 24, y: 24 });
        setCanvasMappingPosition(null);
      } else {
        setCanvasInputPosition(null);
      }
      if (index === null) {
        const nextIndex = (node.input_arguments ?? []).length + 1;
        setInputEditorForm({
          key: `input_${nextIndex}`,
          typeHint: "",
          optional: false,
          sourceMode: "none",
          valueText: "",
          routeText: "",
        });
        setMappingEditorTarget(null);
        setInputEditorTarget({ nodeId, index: null });
        return;
      }
      const target = node.input_arguments?.[index];
      if (!target) return;
      setMappingEditorTarget(null);
      setInputEditorForm(inputToForm(target));
      setInputEditorTarget({ nodeId, index });
    },
    [selectNode, toolchain]
  );

  useEffect(() => {
    if (!toolchain || urlEditorInitialized) return;
    if (!searchParams) {
      setUrlEditorInitialized(true);
      return;
    }
    const mappingParam = searchParams.get("editMapping");
    if (mappingParam) {
      const [nodeId, indexText] = mappingParam.split(":");
      const index = Number.parseInt(indexText ?? "", 10);
      if (nodeId && Number.isFinite(index)) {
        openMappingEditor(nodeId, index);
        setUrlEditorInitialized(true);
        return;
      }
    }
    const inputParam = searchParams.get("editInput");
    if (inputParam) {
      const [nodeId, indexText] = inputParam.split(":");
      if (nodeId) {
        if (indexText === "new") {
          openInputEditor(nodeId, null);
          setUrlEditorInitialized(true);
          return;
        }
        const index = Number.parseInt(indexText ?? "", 10);
        if (Number.isFinite(index)) {
          openInputEditor(nodeId, index);
          setUrlEditorInitialized(true);
          return;
        }
      }
    }
    setUrlEditorInitialized(true);
  }, [openInputEditor, openMappingEditor, searchParams, toolchain, urlEditorInitialized]);

  const formToMapping = (form: MappingEditorForm): feedMappingOriginal | null => {
    const base: Record<string, unknown> = {
      destination: form.destination,
      ...(form.stream ? { stream: true } : {}),
    };

    if (form.sourceMode === "static") {
      try {
        base.value = JSON.parse(form.valueText || "null");
      } catch {
        return null;
      }
    } else if (form.sourceMode === "state") {
      base.getFromState = {
        route: parseRouteText(form.routeText),
      };
    } else if (form.sourceMode === "node_input") {
      base.getFromInputs = {
        route: parseRouteText(form.routeText),
      };
    } else if (form.sourceMode === "node_output") {
      base.getFromOutputs = {
        route: parseRouteText(form.routeText),
      };
    }

    return base as unknown as feedMappingOriginal;
  };

  const saveMappingEditor = () => {
    if (!mappingEditorTarget) return;
    const nextMapping = formToMapping(mappingEditorForm);
    if (!nextMapping) {
      toast.error("Static value must be valid JSON.");
      return;
    }
    updateFeedMapping(mappingEditorTarget.nodeId, mappingEditorTarget.index, () => nextMapping);
    setMappingEditorTarget(null);
    setCanvasMappingPosition(null);
  };

  const inlineRouteTokens = useMemo(
    () => routeTextToTokens(inlineMappingForm?.routeText ?? ""),
    [inlineMappingForm?.routeText]
  );

  const setInlineRouteTokens = (tokens: string[]) => {
    setInlineMappingForm((prev) =>
      prev
        ? {
            ...prev,
            routeText: routeTokensToText(tokens),
          }
        : prev
    );
  };

  const inlineMappingValidationError = useMemo(() => {
    if (!inlineMappingForm) return null;
    if (inlineMappingForm.sourceMode === "static") {
      try {
        JSON.parse(inlineMappingForm.valueText || "null");
      } catch {
        return "Static JSON value is invalid.";
      }
    }

    if (
      inlineMappingForm.sourceMode === "state" ||
      inlineMappingForm.sourceMode === "node_input" ||
      inlineMappingForm.sourceMode === "node_output"
    ) {
      const raw = inlineMappingForm.routeText.trim();
      if (!raw) return "Route is required for route-based source modes.";
      if (raw.includes("..") || raw.startsWith(".") || raw.endsWith(".")) {
        return "Route dot-path is malformed.";
      }
      const tokens = raw.split(".");
      if (tokens.some((token) => !token.trim())) {
        return "Route contains an empty segment.";
      }
    }

    return null;
  }, [inlineMappingForm]);

  const applyInlineMappingEditor = () => {
    if (!selectedFeed || !inlineMappingForm) return;
    if (inlineMappingValidationError) {
      toast.error(inlineMappingValidationError);
      return;
    }
    const nextMapping = formToMapping(inlineMappingForm);
    if (!nextMapping) {
      toast.error("Static value must be valid JSON.");
      return;
    }
    updateFeedMapping(selectedFeed.nodeId, selectedFeed.index, () => nextMapping);
    toast.success("Applied mapping changes.");
  };

  const resetInlineMappingEditor = () => {
    if (!selectedFeedMapping) return;
    setInlineMappingForm(mappingToForm(selectedFeedMapping));
    setNewRouteSegment("");
    setRouteTokenDragIndex(null);
  };

  const saveInputEditor = () => {
    if (!inputEditorTarget) return;
    const key = inputEditorForm.key.trim();
    if (!key) {
      toast.error("Input key is required.");
      return;
    }

    const nextInput: nodeInputArgument = {
      key,
      ...(inputEditorForm.typeHint ? { type_hint: inputEditorForm.typeHint.trim() } : {}),
      ...(inputEditorForm.optional ? { optional: true } : {}),
    };

    if (inputEditorForm.sourceMode === "user_input") {
      nextInput.from_user = true;
    } else if (inputEditorForm.sourceMode === "server_argument") {
      nextInput.from_server = true;
    } else if (inputEditorForm.sourceMode === "static_value") {
      try {
        nextInput.value = JSON.parse(inputEditorForm.valueText || "null");
      } catch {
        toast.error("Static input value must be valid JSON.");
        return;
      }
    } else if (inputEditorForm.sourceMode === "toolchain_state") {
      nextInput.from_state = {
        route: parseRouteText(inputEditorForm.routeText),
      };
    } else if (inputEditorForm.sourceMode === "files") {
      nextInput.from_files = {
        type: "getFiles",
        route: parseRouteText(inputEditorForm.routeText),
      };
    }

    if (inputEditorTarget.index === null) {
      addInputArgument(inputEditorTarget.nodeId, nextInput);
    } else {
      updateInputArgument(inputEditorTarget.nodeId, inputEditorTarget.index, () => nextInput);
    }
    setInputEditorTarget(null);
  };

  const onConnect = (connection: Connection) => {
    if (!connection.source || !connection.target) return;
    const sourceId = connection.source;
    const sourceHandleIndex = parseFeedHandleIndex(connection.sourceHandle);
    if (sourceHandleIndex !== null) {
      updateFeedMapping(sourceId, sourceHandleIndex, (mapping) => ({
        ...mapping,
        destination: connection.target as string,
      }));
      setSelectedFeed({ nodeId: sourceId, index: sourceHandleIndex });
      openMappingEditor(sourceId, sourceHandleIndex);
      return;
    }

    createMappingAndOpen(sourceId, connection.target);
  };

  const onEdgesChange = (changes: EdgeChange[]) => {
    for (const change of changes) {
      if (change.type !== "remove") continue;
      const parsed = parseFeedEdgeId(change.id);
      if (!parsed) continue;
      removeFeedMappingEdge(parsed.source, parsed.index);
    }
  };

  const saveToolchain = () => {
    if (!userData?.auth || !toolchain) return;
    setSaveFailed(false);
    setSaving(true);
    updateToolchainConfig({
      auth: userData.auth,
      toolchain_id: params.toolchainId,
      toolchain: toolchain as unknown as Record<string, unknown>,
      onFinish: (result: { toolchain_id: string } | false) => {
        setSaving(false);
        if (!result) {
          setSaveFailed(true);
          toast.error("Failed to save graph. Retry without losing draft.");
          return;
        }
        setSaveFailed(false);
        setBaselineToolchainSerialized(JSON.stringify(toolchain));
        toast.success("Saved toolchain graph");
      },
    });
  };

  if (!authReviewed) {
    return <div className="ql-editor-state">Checking auth...</div>;
  }
  if (!loginValid || !userData?.auth) {
    return (
      <div className="ql-editor-state">
        You must be logged in to view this editor.
      </div>
    );
  }
  if (!toolchain) {
    return <div className="ql-editor-state">Loading toolchain...</div>;
  }

  const viewport = toolchain.editor_meta?.graph?.viewport;
  const showAnchoredDrawer =
    editorSurface === "drawer" &&
    (Boolean(mappingEditorTarget && mappingEditorMapping) || Boolean(inputEditorTarget && inputEditorSurfaceMode === "full"));
  const showCanvasQuickMapping = Boolean(
    !showAnchoredDrawer &&
      selectedFeed &&
      selectedFeedMapping &&
      inlineMappingForm &&
      canvasMappingPosition
  );
  const showCanvasQuickInput = Boolean(
    !showAnchoredDrawer && inputEditorTarget && inputEditorSurfaceMode === "canvas" && canvasInputPosition
  );
  const hasLocalCanvasEditor = showCanvasQuickMapping || showCanvasQuickInput;
  const activeCanvasEditorLabel = showCanvasQuickMapping
    ? `Mapping ${selectedFeed?.nodeId} #${(selectedFeed?.index ?? 0) + 1}`
    : showCanvasQuickInput
      ? `${inputEditorTarget?.nodeId} · ${inputEditorTarget?.index == null ? "new input" : `input #${inputEditorTarget.index + 1}`}`
      : null;

  return (
    <>
      <div className="ql-editor-shell">
        <div className="ql-editor-hero">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="space-y-3">
              <div className="ql-editor-kicker">Graph composition</div>
              <div className="space-y-1">
                <div className="text-xl font-semibold tracking-tight">Node graph editor</div>
                <div className="max-w-3xl text-sm text-muted-foreground">
                  Compose toolchain flow directly on the canvas. The side rails should support the graph, not compete with it.
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="outline">Nodes {toolchain.nodes.length}</Badge>
                <Badge variant="outline">Edges {edges.length}</Badge>
                <Badge variant="outline">
                  Surface {editorSurface === "drawer" ? "drawer" : "modal"}
                </Badge>
                <Badge variant="outline">
                  {focusCanvas ? "Canvas priority" : "Context rails visible"}
                </Badge>
                {hasLocalCanvasEditor ? (
                  <Badge variant="outline" className="border-cyan-400/50 bg-cyan-500/10 text-cyan-100">
                    Local canvas edit active
                  </Badge>
                ) : null}
                {selectedNode ? (
                  <Badge variant="outline">
                    Selected <span className="ml-1 font-mono">{selectedNode.id}</span>
                  </Badge>
                ) : null}
              </div>
            </div>
            <div className="ql-editor-toolbar">
              <div
                className={cn(
                  "ql-editor-status mr-1",
                  hasUnsavedChanges ? "ql-editor-status-unsaved" : "ql-editor-status-saved"
                )}
              >
                {hasUnsavedChanges ? "Unsaved graph changes" : "All graph changes saved"}
              </div>
              <Button size="sm" variant="outline" onClick={undoChanges} disabled={undoStack.length === 0}>
                Undo
              </Button>
              <Button size="sm" variant="outline" onClick={redoChanges} disabled={redoStack.length === 0}>
                Redo
              </Button>
              <Button size="sm" variant="outline" onClick={toggleEditorSurface}>
                {editorSurface === "drawer" ? "Use modal editor" : "Use drawer editor"}
              </Button>
              <Button size="sm" variant="outline" onClick={toggleFocusCanvas}>
                {focusCanvas ? "Restore rails" : "Prioritize canvas"}
              </Button>
              <Button size="sm" variant="outline" onClick={saveToolchain} disabled={!saveFailed || saving}>
                Retry save
              </Button>
              <Button size="sm" onClick={saveToolchain} disabled={saving}>
                {saving ? "Saving..." : "Save graph"}
              </Button>
            </div>
          </div>
          <div className="mt-4 grid gap-2 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <div className="rounded-[14px] border border-border/70 bg-background/35 px-3 py-2">
              <div className="text-xs font-medium text-foreground">Primary interaction model</div>
              <div className="mt-1 text-xs text-muted-foreground">
                Drag nodes, wire handles, double-click nodes for inputs, and double-click edges for full mapping edits.
              </div>
            </div>
            <div className="rounded-[14px] border border-border/70 bg-background/35 px-3 py-2">
              <div className="text-xs font-medium text-foreground">Current focus</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {selectedFeed
                  ? `Mapping ${selectedFeed.nodeId} #${selectedFeed.index + 1} is active.`
                  : selectedNode
                    ? `Node ${selectedNode.id} is selected in the context rail.`
                    : "No node selected yet. The graph canvas should remain the dominant surface."}
              </div>
            </div>
          </div>
        </div>

        {saveFailed ? (
          <div className="ql-editor-alert-warning">
            Last graph save failed. Use <span className="font-semibold">Retry save</span> or keep editing.
          </div>
        ) : null}

        <div
          className={cn(
            "grid gap-4",
            focusCanvas ? "xl:grid-cols-1" : "xl:grid-cols-[240px_minmax(0,1fr)_320px]"
          )}
        >
          {focusCanvas ? null : (
          <div
            className={cn(
              "ql-editor-panel p-3 transition-all duration-200",
              hasLocalCanvasEditor ? "opacity-55 saturate-[0.75] xl:scale-[0.985]" : undefined
            )}
          >
            <div className="space-y-1">
              <div className="text-sm font-semibold">Node roster</div>
              <div className="ql-editor-caption">
                Select context here, but keep authoring on the graph itself.
              </div>
            </div>
            <div className="mt-3 space-y-2">
              {toolchain.nodes.map((node) => {
                const isSelected = node.id === selectedNodeId;
                return (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => selectNode(node.id)}
                    className={cn(
                      "w-full rounded-sm border px-2 py-1.5 text-left transition-colors",
                      isSelected
                        ? "border-primary/50 bg-primary/10"
                        : "border-border/70 hover:bg-muted/35"
                    )}
                  >
                    <div className="truncate font-mono text-xs font-semibold">{node.id}</div>
                    <div className="truncate text-[11px] text-muted-foreground">
                      {node.api_function ?? "Custom node"}
                    </div>
                    <div className="mt-1 flex gap-1 text-[10px] text-muted-foreground">
                      <span>in {(node.input_arguments ?? []).length}</span>
                      <span>out {(node.feed_mappings ?? []).length}</span>
                    </div>
                  </button>
                );
              })}
            </div>
            <Separator className="my-3" />
            <div className="space-y-1 text-[11px] text-muted-foreground">
              <div className="font-medium text-foreground">Handle legend</div>
              <div>- cyan: node destination</div>
              <div>- amber: state destination</div>
              <div>- blue: user destination</div>
              <div>- dashed: create new mapping</div>
            </div>
          </div>
          )}

          <div
            className={cn(
              "ql-editor-stage transition-all duration-200",
              hasLocalCanvasEditor
                ? "border-cyan-400/45 shadow-[inset_0_1px_0_hsl(var(--foreground)/0.04),0_18px_42px_rgba(20,184,166,0.16)]"
                : undefined
            )}
          >
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2 px-1">
              <div>
                <div className="text-sm font-semibold">Live graph canvas</div>
                <div className="ql-editor-caption">
                  The graph should read as the primary artifact. Side editors are secondary.
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                <span className="rounded-full border border-border/70 bg-background/40 px-2 py-1">
                  {selectedFeed ? "Quick mapping active" : "Canvas browsing"}
                </span>
                {hasLocalCanvasEditor && activeCanvasEditorLabel ? (
                  <span className="rounded-full border border-cyan-400/45 bg-cyan-500/10 px-2 py-1 text-cyan-100">
                    Editing {activeCanvasEditorLabel}
                  </span>
                ) : null}
                <span className="rounded-full border border-border/70 bg-background/40 px-2 py-1">
                  Right-click canvas to add nodes
                </span>
              </div>
            </div>
            {selectedFeed && selectedFeedSummary ? (
              <div className="mb-3 rounded-[16px] border border-cyan-400/35 bg-[radial-gradient(circle_at_top_left,hsl(var(--chart-2)/0.15),transparent_26%),linear-gradient(180deg,hsl(var(--background)/0.96),hsl(var(--card)/0.9))] p-3 shadow-[0_16px_34px_rgba(20,184,166,0.12)]">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div>
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200/80">
                        Active mapping
                      </div>
                      <div className="mt-1 text-sm font-semibold text-foreground">
                        {selectedFeedSummary.label}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-2 text-[11px]">
                      <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                        Dest: <span className="font-mono">{selectedFeedSummary.destination}</span>
                      </span>
                      <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                        Source: <span className="font-mono">{selectedFeedSummary.sourceMode}</span>
                      </span>
                      {selectedFeedSummary.routeText ? (
                        <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                          Route: <span className="font-mono">{selectedFeedSummary.routeText}</span>
                        </span>
                      ) : null}
                      {selectedFeedSummary.stream ? (
                        <span className="rounded-full border border-amber-400/45 bg-amber-500/10 px-2.5 py-1 text-amber-100">
                          Streaming
                        </span>
                      ) : (
                        <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-muted-foreground">
                          Non-streaming
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Keep mapping authoring anchored to the graph. Use the quick editor first, then escalate only when needed.
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Button size="sm" variant="outline" onClick={openSelectedFeedQuickEditor}>
                      Quick edit
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openMappingEditor(selectedFeed.nodeId, selectedFeed.index)}
                    >
                      Full editor
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => cycleFeedDestinationFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                    >
                      Cycle dest
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => cycleFeedSourceModeFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                    >
                      Cycle source
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleFeedStreamFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                    >
                      {selectedFeedSummary.stream ? "Stream off" : "Stream on"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedFeed(null);
                        setHoveredFeed(null);
                        setCanvasMappingPosition(null);
                      }}
                    >
                      Clear
                    </Button>
                  </div>
                </div>
              </div>
            ) : null}
            <ContextMenu>
              <ContextMenuTrigger asChild>
                <div
                  className={cn(
                    "ql-editor-canvas",
                    focusCanvas ? "h-[820px]" : "h-[740px]",
                    hasLocalCanvasEditor ? "ring-1 ring-cyan-400/35" : undefined
                  )}
                  onContextMenuCapture={(event) => {
                    if (!reactFlowInstance) return;
                    const flowPosition = reactFlowInstance.screenToFlowPosition({
                      x: event.clientX,
                      y: event.clientY,
                    });
                    setContextMenuFlowPosition(flowPosition);
                  }}
                >
                  {hasLocalCanvasEditor && activeCanvasEditorLabel ? (
                    <div className="pointer-events-none absolute left-4 top-4 z-10 rounded-full border border-cyan-400/40 bg-background/88 px-3 py-1 text-[11px] font-medium tracking-[0.08em] text-cyan-100 backdrop-blur-sm">
                      Canvas editing mode · {activeCanvasEditorLabel}
                    </div>
                  ) : null}
                  {selectedFeed && selectedFeedSummary ? (
                    <div className="pointer-events-auto absolute bottom-4 left-4 z-10 max-w-[min(720px,calc(100%-2rem))] rounded-[14px] border border-cyan-400/40 bg-background/90 px-3 py-2 shadow-[0_16px_34px_rgba(20,184,166,0.16)] backdrop-blur-sm">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full border border-cyan-400/45 bg-cyan-500/10 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-100">
                          Selected edge tools
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {selectedFeedSummary.label}
                        </span>
                        <span className="rounded-full border border-border/70 bg-background/45 px-2 py-1 text-[11px] text-foreground">
                          {selectedFeedSummary.destination}
                        </span>
                        <span className="rounded-full border border-border/70 bg-background/45 px-2 py-1 text-[11px] text-foreground">
                          {selectedFeedSummary.sourceMode}
                        </span>
                        {selectedFeedSummary.routeText ? (
                          <span className="rounded-full border border-border/70 bg-background/45 px-2 py-1 font-mono text-[11px] text-foreground">
                            {selectedFeedSummary.routeText}
                          </span>
                        ) : null}
                        <div className="ml-auto flex flex-wrap items-center gap-1.5">
                          <Button size="sm" variant="outline" onClick={openSelectedFeedQuickEditor}>
                            Quick edit
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openMappingEditor(selectedFeed.nodeId, selectedFeed.index)}
                          >
                            Full editor
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => cycleFeedDestinationFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                          >
                            Dest
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => cycleFeedSourceModeFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                          >
                            Mode
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => toggleFeedStreamFromEdge(selectedFeed.nodeId, selectedFeed.index)}
                          >
                            {selectedFeedSummary.stream ? "Stream off" : "Stream on"}
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}
                  <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    nodeTypes={stableNodeTypes}
                    edgeTypes={stableEdgeTypes}
                    onInit={setReactFlowInstance}
                    onNodesChange={onNodesChange}
                    onNodeDragStop={(_event, node) => persistNodePosition(node.id, node.position)}
                    onNodeClick={(_event, node) => {
                      selectNode(node.id);
                      setSelectedFeed(null);
                      setHoveredFeed(null);
                    }}
                    onPaneClick={() => {
                      setSelectedFeed(null);
                      setHoveredFeed(null);
                      setInputEditorTarget(null);
                      clearCanvasOverlays();
                    }}
                    onNodeDoubleClick={(event, node) => {
                      const firstInput = toolchain.nodes.find((entry) => entry.id === node.id)?.input_arguments?.[0];
                      const anchor = resolveCanvasOverlayPosition(event.clientX, event.clientY, 360, 340);
                      if (firstInput) {
                        openInputEditor(node.id, 0, { surface: "canvas", anchor });
                      } else {
                        openInputEditor(node.id, null, { surface: "canvas", anchor });
                      }
                    }}
                    onEdgeClick={(event, edge) => {
                      const parsed = parseFeedEdgeId(edge.id);
                      if (!parsed) return;
                      selectFeedFromEdge(parsed.source, parsed.index, {
                        x: event.clientX,
                        y: event.clientY,
                      });
                    }}
                    onEdgeMouseEnter={(_event, edge) => {
                      const parsed = parseFeedEdgeId(edge.id);
                      if (!parsed) return;
                      setHoveredFeed({ nodeId: parsed.source, index: parsed.index });
                    }}
                    onEdgeMouseLeave={() => {
                      setHoveredFeed(null);
                    }}
                    onEdgeDoubleClick={(event, edge) => {
                      const parsed = parseFeedEdgeId(edge.id);
                      if (!parsed) return;
                      setCanvasMappingPosition(resolveCanvasOverlayPosition(event.clientX, event.clientY, 390, 430));
                      openMappingEditor(parsed.source, parsed.index);
                    }}
                    onMoveEnd={(_event, nextViewport) => persistViewport(nextViewport)}
                    onConnect={onConnect}
                    onConnectStart={(_event, params) => {
                      if (params.handleType !== "source") {
                        setConnectSourceNodeId(null);
                        return;
                      }
                      setConnectSourceNodeId(params.nodeId ?? null);
                    }}
                    onConnectEnd={() => {
                      setConnectSourceNodeId(null);
                    }}
                    onEdgesChange={onEdgesChange}
                  defaultViewport={viewport}
                  fitView={!viewport}
                >
                    <Background gap={18} size={1} color="hsl(var(--border) / 0.9)" />
                    <MiniMap
                      pannable
                      zoomable
                      nodeBorderRadius={4}
                      maskColor="hsl(var(--background) / 0.75)"
                      style={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                      }}
                    />
                    <Controls />
                    <svg>
                      <defs>
                        <linearGradient id="toolchain-edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="#ec4899" />
                          <stop offset="60%" stopColor="#8b5cf6" />
                          <stop offset="100%" stopColor="#22d3ee" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </ReactFlow>

                  {showCanvasQuickMapping && selectedFeed && inlineMappingForm ? (
                    <div
                      className="pointer-events-auto absolute z-20 w-[390px] rounded-[14px] border border-primary/40 bg-background/96 p-2.5 shadow-[0_24px_60px_rgba(0,0,0,0.45)] backdrop-blur-sm"
                      style={{ left: canvasMappingPosition?.x ?? 16, top: canvasMappingPosition?.y ?? 16 }}
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-primary/80">On-canvas mapping edit</div>
                          <div className="text-xs font-semibold">
                            {selectedFeed.nodeId} #{selectedFeed.index + 1}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() =>
                              openMappingEditor(selectedFeed.nodeId, selectedFeed.index)
                            }
                          >
                            Full editor
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setSelectedFeed(null);
                              setHoveredFeed(null);
                              setCanvasMappingPosition(null);
                            }}
                          >
                            Close
                          </Button>
                        </div>
                      </div>

                      <div className="grid gap-2 md:grid-cols-2">
                        <div className="space-y-1">
                          <Label className="text-xs">Destination</Label>
                          <select
                            className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                            value={inlineMappingForm.destination}
                            onChange={(event) =>
                              setInlineMappingForm((prev) =>
                                prev
                                  ? {
                                      ...prev,
                                      destination: event.target.value,
                                    }
                                  : prev
                              )
                            }
                          >
                            {SPECIAL_DESTINATIONS.map((specialDestination) => (
                              <option key={specialDestination} value={specialDestination}>
                                {destinationLabel(specialDestination)}
                              </option>
                            ))}
                            {toolchainNodeIds
                              .filter((nodeId) => nodeId !== selectedFeed.nodeId)
                              .map((nodeId) => (
                                <option key={nodeId} value={nodeId}>
                                  {nodeId}
                                </option>
                              ))}
                          </select>
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Source mode</Label>
                          <select
                            className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                            value={inlineMappingForm.sourceMode}
                            onChange={(event) =>
                              setInlineMappingForm((prev) =>
                                prev
                                  ? {
                                      ...prev,
                                      sourceMode: event.target.value as MappingSourceMode,
                                    }
                                  : prev
                              )
                            }
                          >
                            <option value="dry">Dry trigger</option>
                            <option value="static">Static value (JSON)</option>
                            <option value="state">Toolchain state route</option>
                            <option value="node_input">Node input route</option>
                            <option value="node_output">Node output route</option>
                          </select>
                        </div>
                      </div>

                      {inlineMappingForm.sourceMode === "static" ? (
                        <div className="mt-2 space-y-1">
                          <Label className="text-xs">Static JSON value</Label>
                          <Textarea
                            rows={3}
                            value={inlineMappingForm.valueText}
                            onChange={(event) =>
                              setInlineMappingForm((prev) =>
                                prev
                                  ? {
                                      ...prev,
                                      valueText: event.target.value,
                                    }
                                  : prev
                              )
                            }
                          />
                        </div>
                      ) : null}

                      {inlineMappingForm.sourceMode === "state" ||
                      inlineMappingForm.sourceMode === "node_input" ||
                      inlineMappingForm.sourceMode === "node_output" ? (
                        <div className="mt-2 space-y-2">
                          <div className="space-y-1">
                            <Label className="text-xs">Route tokens (drag to reorder)</Label>
                            <div className="flex min-h-[34px] flex-wrap items-center gap-1 rounded-sm border border-border/70 bg-background/70 p-1">
                              {inlineRouteTokens.map((token, index) => (
                                <div
                                  key={`${token}-${index}`}
                                  draggable
                                  onDragStart={() => setRouteTokenDragIndex(index)}
                                  onDragOver={(event) => event.preventDefault()}
                                  onDrop={(event) => {
                                    event.preventDefault();
                                    if (routeTokenDragIndex === null || routeTokenDragIndex === index) {
                                      setRouteTokenDragIndex(null);
                                      return;
                                    }
                                    const nextTokens = [...inlineRouteTokens];
                                    const [moved] = nextTokens.splice(routeTokenDragIndex, 1);
                                    nextTokens.splice(index, 0, moved);
                                    setInlineRouteTokens(nextTokens);
                                    setRouteTokenDragIndex(null);
                                  }}
                                  onDragEnd={() => setRouteTokenDragIndex(null)}
                                  className={cn(
                                    "flex items-center gap-1 rounded-sm border border-border/70 bg-muted/25 px-1.5 py-0.5 font-mono text-[11px] transition-all duration-150",
                                    routeTokenDragIndex === index
                                      ? "scale-[0.98] opacity-70"
                                      : "hover:bg-muted/45 hover:border-cyan-400/40"
                                  )}
                                >
                                  <span>{token}</span>
                                  <button
                                    type="button"
                                    className="text-muted-foreground hover:text-foreground"
                                    onClick={() => {
                                      const nextTokens = inlineRouteTokens.filter(
                                        (_part, tokenIndex) => tokenIndex !== index
                                      );
                                      setInlineRouteTokens(nextTokens);
                                    }}
                                  >
                                    x
                                  </button>
                                </div>
                              ))}
                              {inlineRouteTokens.length === 0 ? (
                                <span className="px-1 text-[11px] text-muted-foreground">
                                  No route segments
                                </span>
                              ) : null}
                            </div>
                          </div>

                          <div className="flex items-center gap-1">
                            <Input
                              value={newRouteSegment}
                              placeholder="Add segment"
                              onChange={(event) => setNewRouteSegment(event.target.value)}
                              onKeyDown={(event) => {
                                if (event.key !== "Enter") return;
                                const segment = newRouteSegment.trim();
                                if (!segment) return;
                                setInlineRouteTokens([...inlineRouteTokens, segment]);
                                setNewRouteSegment("");
                              }}
                            />
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                const segment = newRouteSegment.trim();
                                if (!segment) return;
                                setInlineRouteTokens([...inlineRouteTokens, segment]);
                                setNewRouteSegment("");
                              }}
                            >
                              Add
                            </Button>
                          </div>

                          <div className="space-y-1">
                            <Label className="text-xs">Route (dot path)</Label>
                            <Input
                              placeholder="e.g. request.query"
                              value={inlineMappingForm.routeText}
                              onChange={(event) =>
                                setInlineMappingForm((prev) =>
                                  prev
                                    ? {
                                        ...prev,
                                        routeText: event.target.value,
                                      }
                                    : prev
                                )
                              }
                            />
                          </div>
                        </div>
                      ) : null}

                      {inlineMappingValidationError ? (
                        <div className="ql-editor-alert-inline mt-2">
                          {inlineMappingValidationError}
                        </div>
                      ) : null}

                      <div className="mt-2 flex items-center justify-between gap-2">
                        <label className="flex items-center gap-2 text-[11px] text-muted-foreground">
                          <input
                            type="checkbox"
                            checked={inlineMappingForm.stream}
                            onChange={(event) =>
                              setInlineMappingForm((prev) =>
                                prev
                                  ? {
                                      ...prev,
                                      stream: event.target.checked,
                                    }
                                  : prev
                              )
                            }
                          />
                          Stream output
                        </label>
                        <div className="flex items-center gap-1">
                          <Button size="sm" variant="outline" onClick={resetInlineMappingEditor}>
                            Reset
                          </Button>
                          <Button
                            size="sm"
                            onClick={applyInlineMappingEditor}
                            disabled={Boolean(inlineMappingValidationError)}
                          >
                            Apply
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              removeFeedMappingEdge(selectedFeed.nodeId, selectedFeed.index)
                            }
                          >
                            Remove
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {showCanvasQuickInput && inputEditorTarget ? (
                    <div
                      className="pointer-events-auto absolute z-20 w-[360px] rounded-[14px] border border-cyan-400/35 bg-background/96 p-2.5 shadow-[0_24px_60px_rgba(0,0,0,0.45)] backdrop-blur-sm"
                      style={{ left: canvasInputPosition?.x ?? 24, top: canvasInputPosition?.y ?? 24 }}
                    >
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300/80">On-canvas input edit</div>
                          <div className="text-xs font-semibold">
                            {inputEditorTarget.nodeId} · {inputEditorTarget.index === null ? "New input" : `Input #${inputEditorTarget.index + 1}`}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setInputEditorSurfaceMode("full");
                              setCanvasInputPosition(null);
                            }}
                          >
                            Full editor
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setInputEditorTarget(null);
                              setCanvasInputPosition(null);
                            }}
                          >
                            Close
                          </Button>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <div className="grid gap-2 md:grid-cols-2">
                          <div className="space-y-1">
                            <Label className="text-xs">Argument key</Label>
                            <Input
                              value={inputEditorForm.key}
                              onChange={(event) =>
                                setInputEditorForm((prev) => ({
                                  ...prev,
                                  key: event.target.value,
                                }))
                              }
                            />
                          </div>
                          <div className="space-y-1">
                            <Label className="text-xs">Type hint</Label>
                            <Input
                              placeholder="string | number | boolean"
                              value={inputEditorForm.typeHint}
                              onChange={(event) =>
                                setInputEditorForm((prev) => ({
                                  ...prev,
                                  typeHint: event.target.value,
                                }))
                              }
                            />
                          </div>
                        </div>

                        <div className="space-y-1">
                          <Label className="text-xs">Value source</Label>
                          <select
                            className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                            value={inputEditorForm.sourceMode}
                            onChange={(event) =>
                              setInputEditorForm((prev) => ({
                                ...prev,
                                sourceMode: event.target.value as InputSourceMode,
                              }))
                            }
                          >
                            <option value="none">None</option>
                            <option value="user_input">User input</option>
                            <option value="server_argument">Server argument</option>
                            <option value="static_value">Static value (JSON)</option>
                            <option value="toolchain_state">Toolchain state route</option>
                            <option value="files">File input route</option>
                          </select>
                        </div>

                        {inputEditorForm.sourceMode === "static_value" ? (
                          <div className="space-y-1">
                            <Label className="text-xs">Static JSON value</Label>
                            <Textarea
                              rows={4}
                              value={inputEditorForm.valueText}
                              onChange={(event) =>
                                setInputEditorForm((prev) => ({
                                  ...prev,
                                  valueText: event.target.value,
                                }))
                              }
                            />
                          </div>
                        ) : null}

                        {inputEditorForm.sourceMode === "toolchain_state" || inputEditorForm.sourceMode === "files" ? (
                          <div className="space-y-1">
                            <Label className="text-xs">Route (dot path)</Label>
                            <Input
                              placeholder="e.g. request.files or context.0"
                              value={inputEditorForm.routeText}
                              onChange={(event) =>
                                setInputEditorForm((prev) => ({
                                  ...prev,
                                  routeText: event.target.value,
                                }))
                              }
                            />
                          </div>
                        ) : null}

                        <label className="flex items-center gap-2 text-[11px] text-muted-foreground">
                          <input
                            type="checkbox"
                            checked={inputEditorForm.optional}
                            onChange={(event) =>
                              setInputEditorForm((prev) => ({
                                ...prev,
                                optional: event.target.checked,
                              }))
                            }
                          />
                          Optional argument
                        </label>

                        <div className="flex items-center justify-between gap-2">
                          {inputEditorTarget.index !== null ? (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                const index = inputEditorTarget.index;
                                if (index === null) return;
                                removeInputArgument(inputEditorTarget.nodeId, index);
                                setInputEditorTarget(null);
                                setCanvasInputPosition(null);
                              }}
                            >
                              Delete
                            </Button>
                          ) : <span />}
                          <Button size="sm" onClick={saveInputEditor}>
                            Save changes
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : null}

                  {showAnchoredDrawer ? (
                    <div className="absolute inset-y-2 right-2 z-20 w-[390px] rounded-sm border border-border bg-background/95 shadow-xl backdrop-blur-sm">
                      <div className="flex items-start justify-between gap-2 border-b border-border/70 px-3 py-2">
                        <div>
                          <div className="text-sm font-semibold">
                            {mappingEditorTarget ? "Feed Mapping Editor" : "Input Argument Editor"}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {mappingEditorTarget
                              ? `${mappingEditorTarget.nodeId} → Mapping #${mappingEditorTarget.index + 1}`
                              : inputEditorTarget
                                ? `${inputEditorTarget.nodeId} · ${
                                    inputEditorTarget.index === null
                                      ? "New input argument"
                                      : `Input #${inputEditorTarget.index + 1}`
                                  }`
                                : ""}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={toggleEditorSurface}
                          >
                            Modal
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              setMappingEditorTarget(null);
                              setInputEditorTarget(null);
                            }}
                          >
                            Close
                          </Button>
                        </div>
                      </div>

                      <div className="h-[calc(100%-58px)] overflow-auto px-3 py-3">
                        {mappingEditorTarget && mappingEditorMapping ? (
                          <div className="space-y-3">
                            <div className="grid gap-3 md:grid-cols-2">
                              <div className="space-y-1">
                                <Label className="text-xs">Destination</Label>
                                <select
                                  className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                                  value={mappingEditorForm.destination}
                                  onChange={(event) =>
                                    setMappingEditorForm((prev) => ({
                                      ...prev,
                                      destination: event.target.value,
                                    }))
                                  }
                                >
                                  {SPECIAL_DESTINATIONS.map((specialDestination) => (
                                    <option key={specialDestination} value={specialDestination}>
                                      {destinationLabel(specialDestination)}
                                    </option>
                                  ))}
                                  {toolchainNodeIds
                                    .filter((nodeId) => nodeId !== mappingEditorTarget?.nodeId)
                                    .map((nodeId) => (
                                      <option key={nodeId} value={nodeId}>
                                        {nodeId}
                                      </option>
                                    ))}
                                </select>
                              </div>
                              <div className="space-y-1">
                                <Label className="text-xs">Source Mode</Label>
                                <select
                                  className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                                  value={mappingEditorForm.sourceMode}
                                  onChange={(event) =>
                                    setMappingEditorForm((prev) => ({
                                      ...prev,
                                      sourceMode: event.target.value as MappingSourceMode,
                                    }))
                                  }
                                >
                                  <option value="dry">Dry trigger</option>
                                  <option value="static">Static value (JSON)</option>
                                  <option value="state">Toolchain state route</option>
                                  <option value="node_input">Node input route</option>
                                  <option value="node_output">Node output route</option>
                                </select>
                              </div>
                            </div>

                            {mappingEditorForm.sourceMode === "static" ? (
                              <div className="space-y-1">
                                <Label className="text-xs">Static JSON Value</Label>
                                <Textarea
                                  rows={6}
                                  value={mappingEditorForm.valueText}
                                  onChange={(event) =>
                                    setMappingEditorForm((prev) => ({
                                      ...prev,
                                      valueText: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                            ) : null}

                            {mappingEditorForm.sourceMode === "state" ||
                            mappingEditorForm.sourceMode === "node_input" ||
                            mappingEditorForm.sourceMode === "node_output" ? (
                              <div className="space-y-1">
                                <Label className="text-xs">Route (dot path)</Label>
                                <Input
                                  placeholder="e.g. request.query or history.0.text"
                                  value={mappingEditorForm.routeText}
                                  onChange={(event) =>
                                    setMappingEditorForm((prev) => ({
                                      ...prev,
                                      routeText: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                            ) : null}

                            <label className="flex items-center gap-2 text-xs text-muted-foreground">
                              <input
                                type="checkbox"
                                checked={mappingEditorForm.stream}
                                onChange={(event) =>
                                  setMappingEditorForm((prev) => ({
                                    ...prev,
                                    stream: event.target.checked,
                                  }))
                                }
                              />
                              Stream output
                            </label>

                            <div className="flex items-center gap-1 pt-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  removeFeedMappingEdge(
                                    mappingEditorTarget.nodeId,
                                    mappingEditorTarget.index
                                  );
                                  setMappingEditorTarget(null);
                                }}
                              >
                                Delete mapping
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setMappingEditorTarget(null)}
                              >
                                Cancel
                              </Button>
                              <Button size="sm" onClick={saveMappingEditor}>
                                Save changes
                              </Button>
                            </div>
                          </div>
                        ) : null}

                        {inputEditorTarget ? (
                          <div className="space-y-3">
                            <div className="grid gap-3 md:grid-cols-2">
                              <div className="space-y-1">
                                <Label className="text-xs">Argument key</Label>
                                <Input
                                  value={inputEditorForm.key}
                                  onChange={(event) =>
                                    setInputEditorForm((prev) => ({
                                      ...prev,
                                      key: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                              <div className="space-y-1">
                                <Label className="text-xs">Type hint</Label>
                                <Input
                                  placeholder="string | number | boolean"
                                  value={inputEditorForm.typeHint}
                                  onChange={(event) =>
                                    setInputEditorForm((prev) => ({
                                      ...prev,
                                      typeHint: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                            </div>

                            <div className="space-y-1">
                              <Label className="text-xs">Value source</Label>
                              <select
                                className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                                value={inputEditorForm.sourceMode}
                                onChange={(event) =>
                                  setInputEditorForm((prev) => ({
                                    ...prev,
                                    sourceMode: event.target.value as InputSourceMode,
                                  }))
                                }
                              >
                                <option value="none">None</option>
                                <option value="user_input">User input</option>
                                <option value="server_argument">Server argument</option>
                                <option value="static_value">Static value (JSON)</option>
                                <option value="toolchain_state">Toolchain state route</option>
                                <option value="files">File input route</option>
                              </select>
                            </div>

                            {inputEditorForm.sourceMode === "static_value" ? (
                              <div className="space-y-1">
                                <Label className="text-xs">Static JSON value</Label>
                                <Textarea
                                  rows={5}
                                  value={inputEditorForm.valueText}
                                  onChange={(event) =>
                                    setInputEditorForm((prev) => ({
                                      ...prev,
                                      valueText: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                            ) : null}

                            {inputEditorForm.sourceMode === "toolchain_state" ||
                            inputEditorForm.sourceMode === "files" ? (
                              <div className="space-y-1">
                                <Label className="text-xs">Route (dot path)</Label>
                                <Input
                                  placeholder="e.g. request.files or context.0"
                                  value={inputEditorForm.routeText}
                                  onChange={(event) =>
                                    setInputEditorForm((prev) => ({
                                      ...prev,
                                      routeText: event.target.value,
                                    }))
                                  }
                                />
                              </div>
                            ) : null}

                            <label className="flex items-center gap-2 text-xs text-muted-foreground">
                              <input
                                type="checkbox"
                                checked={inputEditorForm.optional}
                                onChange={(event) =>
                                  setInputEditorForm((prev) => ({
                                    ...prev,
                                    optional: event.target.checked,
                                  }))
                                }
                              />
                              Optional argument
                            </label>

                            <div className="flex items-center gap-1 pt-1">
                              {inputEditorTarget.index !== null ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    const index = inputEditorTarget.index;
                                    if (index === null) return;
                                    removeInputArgument(inputEditorTarget.nodeId, index);
                                    setInputEditorTarget(null);
                                  }}
                                >
                                  Delete argument
                                </Button>
                              ) : null}
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setInputEditorTarget(null)}
                              >
                                Cancel
                              </Button>
                              <Button size="sm" onClick={saveInputEditor}>
                                Save changes
                              </Button>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </div>
              </ContextMenuTrigger>
              <ContextMenuContent className="w-56">
                <ContextMenuLabel>Create node</ContextMenuLabel>
                <ContextMenuSeparator />
                <ContextMenuItem onSelect={addTestItemNode}>Add test item</ContextMenuItem>
                <ContextMenuItem onSelect={addEmptyNode}>Add empty node</ContextMenuItem>
                <ContextMenuSub
                  onOpenChange={(open) => {
                    if (!open) return;
                    if (!sortedApiFunctionSpecs.length) return;
                    setHoveredApiFunctionId((prev) => prev ?? sortedApiFunctionSpecs[0].api_function_id);
                  }}
                >
                  <ContextMenuSubTrigger>Add API call</ContextMenuSubTrigger>
                  <ContextMenuSubContent className="min-w-[700px] p-0">
                    <div className="grid h-[380px] grid-cols-[280px_1fr]">
                      <div className="border-r border-border/70 bg-muted/20 p-3">
                        {hoveredApiFunction ? (
                          <div className="space-y-3 text-xs">
                            <div>
                              <div className="font-semibold">{hoveredApiFunction.api_function_id}</div>
                              <div className="font-mono text-muted-foreground">
                                {hoveredApiFunction.endpoint}
                              </div>
                            </div>
                            {hoveredApiFunction.description ? (
                              <div className="text-muted-foreground">
                                {hoveredApiFunction.description}
                              </div>
                            ) : null}
                            <div>
                              <div className="mb-1 text-muted-foreground">Arguments</div>
                              <div className="space-y-1">
                                {hoveredApiFunction.function_args.length ? (
                                  hoveredApiFunction.function_args.map((arg) => (
                                    <div
                                      key={`${hoveredApiFunction.api_function_id}-${arg.keyword}`}
                                      className="rounded-sm border border-border/70 bg-background px-2 py-1"
                                    >
                                      <div className="font-mono text-[11px]">{arg.keyword}</div>
                                      <div className="text-[11px] text-muted-foreground">
                                        {arg.type_hint ?? "(any)"}
                                      </div>
                                    </div>
                                  ))
                                ) : (
                                  <div className="text-[11px] text-muted-foreground">No arguments</div>
                                )}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="text-xs text-muted-foreground">No API functions available.</div>
                        )}
                      </div>
                      <ScrollArea className="h-[380px]">
                        <div className="p-1">
                          {sortedApiFunctionSpecs.map((spec) => (
                            <ContextMenuItem
                              key={spec.api_function_id}
                              onMouseEnter={() => setHoveredApiFunctionId(spec.api_function_id)}
                              onSelect={() => addApiFunctionNode(spec)}
                              className="font-mono text-xs"
                            >
                              {spec.api_function_id}
                            </ContextMenuItem>
                          ))}
                          {sortedApiFunctionSpecs.length ? null : (
                            <div className="p-2 text-xs text-muted-foreground">
                              API function index unavailable.
                            </div>
                          )}
                        </div>
                      </ScrollArea>
                    </div>
                  </ContextMenuSubContent>
                </ContextMenuSub>
              </ContextMenuContent>
            </ContextMenu>
          </div>

          {focusCanvas ? null : (
          <div
            className={cn(
              "ql-editor-panel p-3 transition-all duration-200",
              hasLocalCanvasEditor ? "opacity-60 saturate-[0.78] xl:scale-[0.99]" : undefined
            )}
          >
            <div className="space-y-1">
              <div className="text-sm font-semibold">Context inspector</div>
              <div className="ql-editor-caption">
                Edit details here after selecting nodes and mappings on canvas.
              </div>
            </div>
            {!selectedNode ? (
              <div className="mt-4 text-sm text-muted-foreground">Select a node to edit mappings.</div>
            ) : (
              <div className="mt-3 space-y-3">
                <div className="ql-editor-inset p-2">
                  <div className="font-mono text-xs font-semibold">{selectedNode.id}</div>
                  <div className="text-xs text-muted-foreground">
                    API: {selectedNode.api_function ?? "Custom node"}
                  </div>
                  <div className="mt-2 flex gap-1">
                    <Badge variant="outline">Inputs {(selectedNode.input_arguments ?? []).length}</Badge>
                    <Badge variant="outline">Mappings {(selectedNode.feed_mappings ?? []).length}</Badge>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-muted-foreground">Input arguments</div>
                  <Button size="sm" variant="outline" onClick={() => openInputEditor(selectedNode.id, null)}>
                    Add input
                  </Button>
                </div>
                <div className="max-h-[180px] space-y-2 overflow-auto pr-1">
                  {(selectedNode.input_arguments ?? []).map((input, index) => (
                    <div
                      key={`${selectedNode.id}-input-${index}`}
                      className="rounded-sm border border-border/70 bg-muted/20 p-2"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs font-semibold">{input.key}</div>
                        <div className="flex items-center gap-1">
                          <Button size="sm" variant="ghost" onClick={() => openInputEditor(selectedNode.id, index)}>
                            Edit
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => removeInputArgument(selectedNode.id, index)}>
                            Remove
                          </Button>
                        </div>
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        {input.type_hint ? `type: ${input.type_hint}` : "type: (unset)"}
                      </div>
                    </div>
                  ))}
                  {(selectedNode.input_arguments ?? []).length ? null : (
                    <div className="rounded-sm border border-dashed border-border/70 p-2 text-xs text-muted-foreground">
                      No input arguments defined.
                    </div>
                  )}
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold text-muted-foreground">Feed mappings</div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => createMappingAndOpen(selectedNode.id, "<<STATE>>")}
                  >
                    Add mapping
                  </Button>
                </div>

                <div className="max-h-[300px] space-y-2 overflow-auto pr-1">
                  {(selectedNode.feed_mappings ?? []).map((mapping, index) => {
                    const destination = (mapping as feedMapping).destination;
                    const isFocused =
                      selectedFeed?.nodeId === selectedNode.id && selectedFeed.index === index;
                    const isHovered =
                      hoveredFeed?.nodeId === selectedNode.id && hoveredFeed.index === index;
                    return (
                      <div
                        key={`${selectedNode.id}-${index}`}
                        onMouseEnter={() =>
                          setHoveredFeed({ nodeId: selectedNode.id, index })
                        }
                        onMouseLeave={() => setHoveredFeed(null)}
                        className={cn(
                          "rounded-sm border p-2 transition-all duration-150",
                          isFocused
                            ? "border-primary/60 bg-primary/10"
                            : isHovered
                              ? "border-cyan-400/50 bg-cyan-500/5"
                              : "border-border/70 bg-muted/20"
                        )}
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <div className="text-xs font-semibold">Mapping #{index + 1}</div>
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                updateFeedMapping(
                                  selectedNode.id,
                                  index,
                                  (current) =>
                                    ({
                                      ...current,
                                      destination: nextMappingDestination(
                                        selectedNode.id,
                                        current.destination,
                                        toolchainNodeIds
                                      ),
                                    }) as feedMappingOriginal
                                );
                                setSelectedFeed({ nodeId: selectedNode.id, index });
                                setHoveredFeed({ nodeId: selectedNode.id, index });
                              }}
                              className="transition-colors"
                            >
                              Dest
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                updateFeedMapping(
                                  selectedNode.id,
                                  index,
                                  (current) =>
                                    ({
                                      ...current,
                                      ...(current.stream
                                        ? { stream: undefined }
                                        : { stream: true }),
                                    }) as feedMappingOriginal
                                );
                                setSelectedFeed({ nodeId: selectedNode.id, index });
                                setHoveredFeed({ nodeId: selectedNode.id, index });
                              }}
                              className="transition-colors"
                            >
                              {(mapping as feedMapping).stream ? "S on" : "S off"}
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => openMappingEditor(selectedNode.id, index)}>
                              Edit
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => removeFeedMappingEdge(selectedNode.id, index)}>
                              Remove
                            </Button>
                          </div>
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          Destination: <span className="font-mono">{destinationLabel(destination)}</span>
                        </div>
                        <div className="text-[11px] text-muted-foreground">
                          {Boolean((mapping as feedMapping).stream) ? "Streaming" : "Non-streaming"}
                        </div>
                      </div>
                    );
                  })}
                  {selectedNode.feed_mappings?.length ? null : (
                    <div className="rounded-sm border border-dashed border-border/70 p-3 text-xs text-muted-foreground">
                      No mappings yet. Use &quot;Add mapping&quot; or drag from the dashed output handle.
                    </div>
                  )}
                </div>

                {selectedFeed && selectedFeedMapping && inlineMappingForm ? (
                  <div className="space-y-3 rounded-sm border border-primary/40 bg-primary/5 p-2 transition-colors duration-150">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold">Quick mapping editor</div>
                      <div className="flex items-center gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            openMappingEditor(selectedFeed.nodeId, selectedFeed.index)
                          }
                        >
                          {editorSurface === "drawer" ? "Open editor" : "Open modal"}
                        </Button>
                      </div>
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      <div className="space-y-1">
                        <Label className="text-xs">Destination</Label>
                        <select
                          className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                          value={inlineMappingForm.destination}
                          onChange={(event) =>
                            setInlineMappingForm((prev) =>
                              prev
                                ? {
                                    ...prev,
                                    destination: event.target.value,
                                  }
                                : prev
                            )
                          }
                        >
                          {SPECIAL_DESTINATIONS.map((specialDestination) => (
                            <option key={specialDestination} value={specialDestination}>
                              {destinationLabel(specialDestination)}
                            </option>
                          ))}
                          {toolchainNodeIds
                            .filter((nodeId) => nodeId !== selectedFeed.nodeId)
                            .map((nodeId) => (
                              <option key={nodeId} value={nodeId}>
                                {nodeId}
                              </option>
                            ))}
                        </select>
                      </div>
                      <div className="space-y-1">
                        <Label className="text-xs">Source mode</Label>
                        <select
                          className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                          value={inlineMappingForm.sourceMode}
                          onChange={(event) =>
                            setInlineMappingForm((prev) =>
                              prev
                                ? {
                                    ...prev,
                                    sourceMode: event.target.value as MappingSourceMode,
                                  }
                                : prev
                            )
                          }
                        >
                          <option value="dry">Dry trigger</option>
                          <option value="static">Static value (JSON)</option>
                          <option value="state">Toolchain state route</option>
                          <option value="node_input">Node input route</option>
                          <option value="node_output">Node output route</option>
                        </select>
                      </div>
                    </div>

                    {inlineMappingForm.sourceMode === "static" ? (
                      <div className="space-y-1">
                        <Label className="text-xs">Static JSON value</Label>
                        <Textarea
                          rows={4}
                          value={inlineMappingForm.valueText}
                          onChange={(event) =>
                            setInlineMappingForm((prev) =>
                              prev
                                ? {
                                    ...prev,
                                    valueText: event.target.value,
                                  }
                                : prev
                            )
                          }
                        />
                      </div>
                    ) : null}

                    {inlineMappingForm.sourceMode === "state" ||
                    inlineMappingForm.sourceMode === "node_input" ||
                    inlineMappingForm.sourceMode === "node_output" ? (
                      <div className="space-y-2">
                        <div className="space-y-1">
                          <Label className="text-xs">Route tokens (drag to reorder)</Label>
                          <div className="flex min-h-[34px] flex-wrap items-center gap-1 rounded-sm border border-border/70 bg-background/70 p-1">
                            {inlineRouteTokens.map((token, index) => (
                              <div
                                key={`${token}-${index}`}
                                draggable
                                onDragStart={() => setRouteTokenDragIndex(index)}
                                onDragOver={(event) => event.preventDefault()}
                                onDrop={(event) => {
                                  event.preventDefault();
                                  if (
                                    routeTokenDragIndex === null ||
                                    routeTokenDragIndex === index
                                  ) {
                                    setRouteTokenDragIndex(null);
                                    return;
                                  }
                                  const nextTokens = [...inlineRouteTokens];
                                  const [moved] = nextTokens.splice(routeTokenDragIndex, 1);
                                  nextTokens.splice(index, 0, moved);
                                  setInlineRouteTokens(nextTokens);
                                  setRouteTokenDragIndex(null);
                                }}
                                onDragEnd={() => setRouteTokenDragIndex(null)}
                                className={cn(
                                  "flex items-center gap-1 rounded-sm border border-border/70 bg-muted/25 px-1.5 py-0.5 font-mono text-[11px] transition-all duration-150",
                                  routeTokenDragIndex === index
                                    ? "scale-[0.98] opacity-70"
                                    : "hover:bg-muted/45 hover:border-cyan-400/40"
                                )}
                              >
                                <span>{token}</span>
                                <button
                                  type="button"
                                  className="text-muted-foreground hover:text-foreground"
                                  onClick={() => {
                                    const nextTokens = inlineRouteTokens.filter(
                                      (_part, tokenIndex) => tokenIndex !== index
                                    );
                                    setInlineRouteTokens(nextTokens);
                                  }}
                                >
                                  x
                                </button>
                              </div>
                            ))}
                            {inlineRouteTokens.length === 0 ? (
                              <span className="px-1 text-[11px] text-muted-foreground">
                                No route segments
                              </span>
                            ) : null}
                          </div>
                        </div>

                        <div className="flex items-center gap-1">
                          <Input
                            value={newRouteSegment}
                            placeholder="Add segment"
                            onChange={(event) => setNewRouteSegment(event.target.value)}
                            onKeyDown={(event) => {
                              if (event.key !== "Enter") return;
                              const segment = newRouteSegment.trim();
                              if (!segment) return;
                              setInlineRouteTokens([...inlineRouteTokens, segment]);
                              setNewRouteSegment("");
                            }}
                          />
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              const segment = newRouteSegment.trim();
                              if (!segment) return;
                              setInlineRouteTokens([...inlineRouteTokens, segment]);
                              setNewRouteSegment("");
                            }}
                          >
                            Add
                          </Button>
                        </div>

                        <div className="space-y-1">
                          <Label className="text-xs">Route (dot path)</Label>
                          <Input
                            value={inlineMappingForm.routeText}
                            onChange={(event) =>
                              setInlineMappingForm((prev) =>
                                prev
                                  ? {
                                      ...prev,
                                      routeText: event.target.value,
                                    }
                                  : prev
                              )
                            }
                          />
                        </div>
                      </div>
                    ) : null}

                    {inlineMappingValidationError ? (
                      <div className="ql-editor-alert-inline">
                        {inlineMappingValidationError}
                      </div>
                    ) : null}

                    <label className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <input
                        type="checkbox"
                        checked={inlineMappingForm.stream}
                        onChange={(event) =>
                          setInlineMappingForm((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  stream: event.target.checked,
                                }
                              : prev
                          )
                        }
                      />
                      Stream output
                    </label>

                    <div className="flex items-center gap-1">
                      <Button size="sm" variant="outline" onClick={resetInlineMappingEditor}>
                        Reset
                      </Button>
                      <Button
                        size="sm"
                        onClick={applyInlineMappingEditor}
                        disabled={Boolean(inlineMappingValidationError)}
                      >
                        Apply
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            )}
          </div>
          )}
        </div>
      </div>

      <Dialog
        open={editorSurface === "modal" && Boolean(mappingEditorTarget && mappingEditorMapping)}
        onOpenChange={(open) => {
          if (!open) setMappingEditorTarget(null);
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Feed Mapping Editor</DialogTitle>
            <DialogDescription>
              {mappingEditorTarget ? `${mappingEditorTarget.nodeId} → Mapping #${mappingEditorTarget.index + 1}` : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Destination</Label>
              <select
                className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                value={mappingEditorForm.destination}
                onChange={(event) =>
                  setMappingEditorForm((prev) => ({
                    ...prev,
                    destination: event.target.value,
                  }))
                }
              >
                {SPECIAL_DESTINATIONS.map((specialDestination) => (
                  <option key={specialDestination} value={specialDestination}>
                    {destinationLabel(specialDestination)}
                  </option>
                ))}
                {toolchainNodeIds
                  .filter((nodeId) => nodeId !== mappingEditorTarget?.nodeId)
                  .map((nodeId) => (
                    <option key={nodeId} value={nodeId}>
                      {nodeId}
                    </option>
                  ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label>Source Mode</Label>
              <select
                className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
                value={mappingEditorForm.sourceMode}
                onChange={(event) =>
                  setMappingEditorForm((prev) => ({
                    ...prev,
                    sourceMode: event.target.value as MappingSourceMode,
                  }))
                }
              >
                <option value="dry">Dry trigger</option>
                <option value="static">Static value (JSON)</option>
                <option value="state">Toolchain state route</option>
                <option value="node_input">Node input route</option>
                <option value="node_output">Node output route</option>
              </select>
            </div>
          </div>

          {mappingEditorForm.sourceMode === "static" ? (
            <div className="space-y-2">
              <Label>Static JSON Value</Label>
              <Textarea
                rows={6}
                value={mappingEditorForm.valueText}
                onChange={(event) =>
                  setMappingEditorForm((prev) => ({
                    ...prev,
                    valueText: event.target.value,
                  }))
                }
              />
            </div>
          ) : null}

          {mappingEditorForm.sourceMode === "state" ||
          mappingEditorForm.sourceMode === "node_input" ||
          mappingEditorForm.sourceMode === "node_output" ? (
            <div className="space-y-2">
              <Label>Route (dot path)</Label>
              <Input
                placeholder="e.g. request.query or history.0.text"
                value={mappingEditorForm.routeText}
                onChange={(event) =>
                  setMappingEditorForm((prev) => ({
                    ...prev,
                    routeText: event.target.value,
                  }))
                }
              />
            </div>
          ) : null}

          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={mappingEditorForm.stream}
              onChange={(event) =>
                setMappingEditorForm((prev) => ({
                  ...prev,
                  stream: event.target.checked,
                }))
              }
            />
            Stream output
          </label>

          <DialogFooter>
            {mappingEditorTarget ? (
              <Button
                variant="outline"
                onClick={() => {
                  removeFeedMappingEdge(mappingEditorTarget.nodeId, mappingEditorTarget.index);
                  setMappingEditorTarget(null);
                }}
              >
                Delete mapping
              </Button>
            ) : null}
            <Button variant="outline" onClick={() => setMappingEditorTarget(null)}>
              Cancel
            </Button>
            <Button onClick={saveMappingEditor}>Save changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={editorSurface === "modal" && inputEditorSurfaceMode === "full" && Boolean(inputEditorTarget)}
        onOpenChange={(open) => {
          if (!open) {
            setInputEditorTarget(null);
            setCanvasInputPosition(null);
            setInputEditorSurfaceMode("full");
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Input Argument Editor</DialogTitle>
            <DialogDescription>
              {inputEditorTarget
                ? `${inputEditorTarget.nodeId} · ${
                    inputEditorTarget.index === null
                      ? "New input argument"
                      : `Input #${inputEditorTarget.index + 1}`
                  }`
                : ""}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Argument key</Label>
              <Input
                value={inputEditorForm.key}
                onChange={(event) =>
                  setInputEditorForm((prev) => ({
                    ...prev,
                    key: event.target.value,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label>Type hint</Label>
              <Input
                placeholder="string | number | boolean"
                value={inputEditorForm.typeHint}
                onChange={(event) =>
                  setInputEditorForm((prev) => ({
                    ...prev,
                    typeHint: event.target.value,
                  }))
                }
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Value source</Label>
            <select
              className="h-8 w-full rounded-sm border border-border bg-background px-2 text-xs"
              value={inputEditorForm.sourceMode}
              onChange={(event) =>
                setInputEditorForm((prev) => ({
                  ...prev,
                  sourceMode: event.target.value as InputSourceMode,
                }))
              }
            >
              <option value="none">None</option>
              <option value="user_input">User input</option>
              <option value="server_argument">Server argument</option>
              <option value="static_value">Static value (JSON)</option>
              <option value="toolchain_state">Toolchain state route</option>
              <option value="files">File input route</option>
            </select>
          </div>

          {inputEditorForm.sourceMode === "static_value" ? (
            <div className="space-y-2">
              <Label>Static JSON value</Label>
              <Textarea
                rows={5}
                value={inputEditorForm.valueText}
                onChange={(event) =>
                  setInputEditorForm((prev) => ({
                    ...prev,
                    valueText: event.target.value,
                  }))
                }
              />
            </div>
          ) : null}

          {inputEditorForm.sourceMode === "toolchain_state" ||
          inputEditorForm.sourceMode === "files" ? (
            <div className="space-y-2">
              <Label>Route (dot path)</Label>
              <Input
                placeholder="e.g. request.files or context.0"
                value={inputEditorForm.routeText}
                onChange={(event) =>
                  setInputEditorForm((prev) => ({
                    ...prev,
                    routeText: event.target.value,
                  }))
                }
              />
            </div>
          ) : null}

          <label className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={inputEditorForm.optional}
              onChange={(event) =>
                setInputEditorForm((prev) => ({
                  ...prev,
                  optional: event.target.checked,
                }))
              }
            />
            Optional argument
          </label>

          <DialogFooter>
            {inputEditorTarget?.index !== null && inputEditorTarget ? (
              <Button
                variant="outline"
                onClick={() => {
                  const index = inputEditorTarget.index;
                  if (index === null) return;
                  removeInputArgument(inputEditorTarget.nodeId, index);
                  setInputEditorTarget(null);
                }}
              >
                Delete argument
              </Button>
            ) : null}
            <Button variant="outline" onClick={() => setInputEditorTarget(null)}>
              Cancel
            </Button>
            <Button onClick={saveInputEditor}>Save changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
