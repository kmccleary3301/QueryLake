"use client";

import { DragEvent, Fragment, ReactNode, useMemo, useState } from "react";
import { Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type {
  BoxNode,
  ComponentNode,
  DividerNode,
  LayoutNode,
  ScrollNode,
  SplitNode,
  StackNode,
  StyleSpec,
  TextNode,
  ToolchainUISpecV2,
  UINode,
} from "@/types/toolchain-ui-spec-v2";

function styleToClassName(style?: StyleSpec) {
  if (!style) return "";

  const padding = {
    none: "p-0",
    xs: "p-2",
    sm: "p-3",
    md: "p-3",
    lg: "p-4",
  } as const;
  const gap = {
    none: "gap-0",
    xs: "gap-2",
    sm: "gap-3",
    md: "gap-3",
    lg: "gap-4",
  } as const;
  const width = {
    auto: "w-auto",
    full: "w-full",
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
  } as const;
  const height = {
    auto: "h-auto",
    full: "h-full",
  } as const;
  const overflow = {
    visible: "overflow-visible",
    hidden: "overflow-hidden",
    auto: "overflow-auto",
  } as const;
  const surface = {
    none: "",
    panel: "bg-card",
    muted: "bg-muted/40",
    inset: "bg-muted/25",
  } as const;
  const border = {
    none: "",
    hairline: "border border-border/60",
  } as const;
  const radius = {
    none: "",
    sm: "rounded-sm",
    md: "rounded-sm",
  } as const;

  return cn(
    style.padding ? padding[style.padding] : undefined,
    style.gap ? gap[style.gap] : undefined,
    style.width ? width[style.width] : undefined,
    style.height ? height[style.height] : undefined,
    style.overflow ? overflow[style.overflow] : undefined,
    style.surface ? surface[style.surface] : undefined,
    style.border ? border[style.border] : undefined,
    style.radius ? radius[style.radius] : undefined,
    style.className
  );
}

function ComponentPlaceholder({ node }: { node: ComponentNode }) {
  return (
    <div
      className={cn(
        "rounded-sm border border-dashed border-border/70 bg-muted/10 px-3 py-2 text-xs text-muted-foreground",
        styleToClassName(node.style)
      )}
    >
      <div className="font-medium text-foreground/80">{node.label ?? node.componentId}</div>
      <div className="text-[11px] opacity-80">{node.componentId}</div>
    </div>
  );
}

export type ToolchainUISpecRendererV2Props = {
  spec: ToolchainUISpecV2;
  renderComponent?: (node: ComponentNode) => ReactNode;
  selectedNodeId?: string;
  onSelectNode?: (nodeId: string) => void;
  showNodeFrames?: boolean;
  enableNodeReorderDnD?: boolean;
  draggingNodeId?: string | null;
  onNodeDragStart?: (nodeId: string) => void;
  onNodeDragEnd?: () => void;
  onNodeDropRelative?: (
    sourceNodeId: string,
    targetNodeId: string,
    placement: "before" | "after"
  ) => void;
  onNodeDropInside?: (sourceNodeId: string, targetNodeId: string) => void;
  showInlineControls?: boolean;
  onInsertRelative?: (targetNodeId: string, placement: "before" | "after") => void;
  onWrapNode?: (
    targetNodeId: string,
    mode: "split-horizontal" | "split-vertical" | "stack-vertical" | "box"
  ) => void;
  onAddLayoutChild?: (
    targetNodeId: string,
    kind: "stack" | "box" | "split" | "scroll" | "text" | "divider"
  ) => void;
  onDeleteNode?: (nodeId: string) => void;
};

export default function ToolchainUISpecRendererV2({
  spec,
  renderComponent,
  selectedNodeId,
  onSelectNode,
  showNodeFrames = false,
  enableNodeReorderDnD = false,
  draggingNodeId = null,
  onNodeDragStart,
  onNodeDragEnd,
  onNodeDropRelative,
  onNodeDropInside,
  showInlineControls = false,
  onInsertRelative,
  onWrapNode,
  onAddLayoutChild,
  onDeleteNode,
}: ToolchainUISpecRendererV2Props) {
  const nodeMap = useMemo(() => spec.nodes, [spec.nodes]);
  const renderComponentImpl = renderComponent ?? ((node) => <ComponentPlaceholder node={node} />);
  const [dropTarget, setDropTarget] = useState<{
    nodeId: string;
    placement: "before" | "inside" | "after";
  } | null>(null);

  const wrapNodeFrame = (node: UINode, content: ReactNode) => {
    const isSelected = selectedNodeId === node.id;
    const isInteractive = Boolean(onSelectNode);
    const shouldFrame = showNodeFrames || isInteractive || isSelected;
    const canWrapNode = Boolean(onWrapNode && node.id !== spec.root);
    const canAddLayoutChildren =
      Boolean(onAddLayoutChild) &&
      node.kind === "layout" &&
      node.type !== "divider" &&
      node.type !== "text";

    if (!shouldFrame) return content;

    const handleDragStart = (event: DragEvent<HTMLDivElement>) => {
      if (!enableNodeReorderDnD) return;
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", node.id);
      onNodeDragStart?.(node.id);
    };

    const handleDrop = (event: DragEvent<HTMLDivElement>) => {
      if (!enableNodeReorderDnD || !onNodeDropRelative) return;
      event.preventDefault();
      const sourceNodeId = event.dataTransfer.getData("text/plain");
      setDropTarget(null);
      if (!sourceNodeId) return;
      const rect = event.currentTarget.getBoundingClientRect();
      const relativeY = event.clientY - rect.top;
      const relativeRatio = rect.height > 0 ? relativeY / rect.height : 0.5;
      if (
        onNodeDropInside &&
        node.kind === "layout" &&
        node.type !== "divider" &&
        node.type !== "text" &&
        relativeRatio >= 0.34 &&
        relativeRatio <= 0.66
      ) {
        onNodeDropInside(sourceNodeId, node.id);
        onNodeDragEnd?.();
        return;
      }
      const placement: "before" | "after" = relativeRatio < 0.5 ? "before" : "after";
      onNodeDropRelative(sourceNodeId, node.id, placement);
      onNodeDragEnd?.();
    };

    return (
      <div
        className={cn(
          "group relative min-w-0 min-h-0 rounded-[14px] transition-all duration-150",
          "ring-1 ring-transparent hover:ring-border/70 hover:bg-muted/10",
          isSelected
            ? "ring-cyan-400/70 bg-cyan-500/[0.08] shadow-[0_0_0_1px_rgba(34,211,238,0.18),0_18px_36px_hsl(var(--background)/0.24)]"
            : undefined,
          dropTarget?.nodeId === node.id
            ? "ring-2 ring-cyan-300/60 bg-cyan-500/[0.06] shadow-[0_0_0_1px_rgba(34,211,238,0.16),0_18px_40px_hsl(var(--background)/0.28)]"
            : undefined,
          isInteractive ? "cursor-pointer" : undefined,
          enableNodeReorderDnD && draggingNodeId === node.id ? "opacity-60" : undefined
        )}
        draggable={enableNodeReorderDnD}
        onDragStart={handleDragStart}
        onDragEnd={() => {
          if (!enableNodeReorderDnD) return;
          setDropTarget(null);
          onNodeDragEnd?.();
        }}
        onDragOver={(event) => {
          if (!enableNodeReorderDnD) return;
          event.preventDefault();
          event.dataTransfer.dropEffect = "move";
          const rect = event.currentTarget.getBoundingClientRect();
          const relativeY = event.clientY - rect.top;
          const relativeRatio = rect.height > 0 ? relativeY / rect.height : 0.5;
          const placement =
            onNodeDropInside &&
            node.kind === "layout" &&
            node.type !== "divider" &&
            node.type !== "text" &&
            relativeRatio >= 0.34 &&
            relativeRatio <= 0.66
              ? "inside"
              : relativeRatio < 0.5
                ? "before"
                : "after";
          setDropTarget({ nodeId: node.id, placement });
        }}
        onDragLeave={(event) => {
          if (!enableNodeReorderDnD) return;
          const nextTarget = event.relatedTarget;
          if (nextTarget instanceof Node && event.currentTarget.contains(nextTarget)) {
            return;
          }
          setDropTarget((current) => (current?.nodeId === node.id ? null : current));
        }}
        onDrop={handleDrop}
        onClick={
          isInteractive
            ? (event) => {
                event.stopPropagation();
                onSelectNode?.(node.id);
              }
            : undefined
        }
      >
        {showNodeFrames ? (
          <>
            <span className="pointer-events-none absolute left-1 top-1 z-10 rounded-full border border-border/70 bg-background/90 px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-muted-foreground shadow-sm">
              {node.kind === "layout" ? node.type : "component"}
            </span>
            <span className="pointer-events-none absolute right-1 top-1 z-10 rounded-full border border-border/70 bg-background/90 px-2 py-0.5 font-mono text-[10px] text-muted-foreground shadow-sm">
              {node.id}
            </span>
            {isSelected ? (
              <span className="pointer-events-none absolute left-1 top-8 z-10 rounded-full border border-cyan-400/45 bg-background/92 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] text-cyan-100 shadow-sm">
                Selected
              </span>
            ) : null}
          </>
        ) : null}
        {enableNodeReorderDnD && draggingNodeId && draggingNodeId !== node.id ? (
          <>
            <div
              className={cn(
                "pointer-events-none absolute left-3 right-3 top-1 z-20 h-[3px] rounded-full bg-transparent transition-all duration-100",
                dropTarget?.nodeId === node.id && dropTarget.placement === "before"
                  ? "bg-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.55)]"
                  : undefined
              )}
            />
            {canAddLayoutChildren ? (
              <div
                className={cn(
                  "pointer-events-none absolute inset-x-4 top-1/2 z-20 flex -translate-y-1/2 justify-center transition-all duration-100",
                  dropTarget?.nodeId === node.id && dropTarget.placement === "inside"
                    ? "opacity-100"
                    : "opacity-0"
                )}
              >
                <div className="rounded-full border border-cyan-300/65 bg-cyan-500/12 px-3 py-1 text-[10px] font-medium uppercase tracking-[0.16em] text-cyan-100 shadow-[0_0_20px_rgba(34,211,238,0.22)]">
                  Drop inside
                </div>
              </div>
            ) : null}
            <div
              className={cn(
                "pointer-events-none absolute left-3 right-3 bottom-1 z-20 h-[3px] rounded-full bg-transparent transition-all duration-100",
                dropTarget?.nodeId === node.id && dropTarget.placement === "after"
                  ? "bg-cyan-300 shadow-[0_0_18px_rgba(34,211,238,0.55)]"
                  : undefined
              )}
            />
          </>
        ) : null}
        {showInlineControls ? (
          <div
            className={cn(
              "absolute right-1 top-8 z-20 flex items-center gap-1 transition-all duration-150",
              isSelected
                ? "translate-y-0 opacity-100"
                : "translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100"
            )}
          >
            {onInsertRelative ? (
              <>
                <button
                  type="button"
                  className="rounded-full border border-border/70 bg-background/95 px-2.5 py-1 text-[10px] text-muted-foreground shadow-sm hover:text-foreground"
                  title="Insert sibling before"
                  aria-label="Insert sibling before"
                  onClick={(event) => {
                    event.stopPropagation();
                    onInsertRelative(node.id, "before");
                  }}
                >
                  + before
                </button>
                <button
                  type="button"
                  className="rounded-full border border-border/70 bg-background/95 px-2.5 py-1 text-[10px] text-muted-foreground shadow-sm hover:text-foreground"
                  title="Insert sibling after"
                  aria-label="Insert sibling after"
                  onClick={(event) => {
                    event.stopPropagation();
                    onInsertRelative(node.id, "after");
                  }}
                >
                  + after
                </button>
              </>
            ) : null}
            {onDeleteNode && node.id !== spec.root ? (
              <button
                type="button"
                className="rounded-full border border-border/70 bg-background/95 p-1.5 text-muted-foreground shadow-sm hover:text-destructive"
                title="Delete node"
                aria-label="Delete node"
                onClick={(event) => {
                  event.stopPropagation();
                  onDeleteNode(node.id);
                }}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            ) : null}
          </div>
        ) : null}
        {showInlineControls && (canWrapNode || canAddLayoutChildren) ? (
          <div
            className={cn(
              "absolute left-1 right-1 bottom-9 z-20 transition-all duration-150",
              isSelected
                ? "translate-y-0 opacity-100"
                : "translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100"
            )}
          >
            <div className="flex flex-wrap items-center gap-1 rounded-[12px] border border-border/70 bg-background/95 px-2 py-1.5 shadow-sm backdrop-blur-sm">
              {canWrapNode ? (
                <>
                  <span className="px-1 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                    Wrap
                  </span>
                  <button
                    type="button"
                    className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    onClick={(event) => {
                      event.stopPropagation();
                      onWrapNode?.(node.id, "split-horizontal");
                    }}
                  >
                    Split H
                  </button>
                  <button
                    type="button"
                    className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    onClick={(event) => {
                      event.stopPropagation();
                      onWrapNode?.(node.id, "split-vertical");
                    }}
                  >
                    Split V
                  </button>
                  <button
                    type="button"
                    className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    onClick={(event) => {
                      event.stopPropagation();
                      onWrapNode?.(node.id, "stack-vertical");
                    }}
                  >
                    Stack
                  </button>
                  <button
                    type="button"
                    className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                    onClick={(event) => {
                      event.stopPropagation();
                      onWrapNode?.(node.id, "box");
                    }}
                  >
                    Box
                  </button>
                </>
              ) : null}
              {canWrapNode && canAddLayoutChildren ? (
                <div className="mx-1 h-3 w-px bg-border/60" />
              ) : null}
              {canAddLayoutChildren ? (
                <>
                  <span className="px-1 text-[10px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                    Add child
                  </span>
                  {(["box", "stack", "split", "text", "divider"] as const).map((kind) => (
                    <button
                      key={`${node.id}-${kind}`}
                      type="button"
                      className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                      onClick={(event) => {
                        event.stopPropagation();
                        onAddLayoutChild?.(node.id, kind);
                      }}
                    >
                      {kind === "divider" ? "Rule" : kind[0].toUpperCase() + kind.slice(1)}
                    </button>
                  ))}
                </>
              ) : null}
            </div>
          </div>
        ) : null}
        {showInlineControls && onInsertRelative ? (
          <div
            className={cn(
              "absolute inset-x-0 -bottom-3 z-20 flex justify-center transition-all duration-150",
              isSelected
                ? "translate-y-0 opacity-100"
                : "translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100"
            )}
          >
            <div className="flex items-center gap-1 rounded-full border border-border/70 bg-background/95 px-2 py-1 shadow-sm">
              <button
                type="button"
                className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                aria-label="Insert sibling before"
                onClick={(event) => {
                  event.stopPropagation();
                  onInsertRelative(node.id, "before");
                }}
              >
                Insert before
              </button>
              <div className="h-3 w-px bg-border/60" />
              <button
                type="button"
                className="rounded-full px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted/50 hover:text-foreground"
                aria-label="Insert sibling after"
                onClick={(event) => {
                  event.stopPropagation();
                  onInsertRelative(node.id, "after");
                }}
              >
                Insert after
              </button>
            </div>
          </div>
        ) : null}
        {content}
      </div>
    );
  };

  const renderById = (id: string, visited: Set<string>): ReactNode => {
    if (visited.has(id)) {
      return (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          Cycle detected at node &quot;{id}&quot;
        </div>
      );
    }
    const node = nodeMap[id];
    if (!node) {
      return (
        <div className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-xs text-destructive">
          Missing node &quot;{id}&quot;
        </div>
      );
    }
    const nextVisited = new Set(visited);
    nextVisited.add(id);
    return renderNode(node, nextVisited);
  };

  const renderLayoutNode = (node: LayoutNode, visited: Set<string>) => {
    switch (node.type) {
      case "box":
        return renderBoxNode(node as BoxNode, visited);
      case "split":
        return renderSplitNode(node as SplitNode, visited);
      case "stack":
        return renderStackNode(node as StackNode, visited);
      case "scroll":
        return renderScrollNode(node as ScrollNode, visited);
      case "divider":
        return renderDividerNode(node as DividerNode);
      case "text":
        return renderTextNode(node as TextNode);
      default: {
        const exhaustive: never = node;
        return exhaustive;
      }
    }
  };

  const renderBoxNode = (node: BoxNode, visited: Set<string>) => {
    return (
      <div className={cn("flex flex-col", styleToClassName(node.style))}>
        {node.header ? <div className="mb-2">{renderById(node.header, visited)}</div> : null}
        <div className={cn("flex flex-col", node.style?.gap ? undefined : "gap-2")}>
          {node.children.map((child) => (
            <Fragment key={child}>{renderById(child, visited)}</Fragment>
          ))}
        </div>
        {node.footer ? <div className="mt-2">{renderById(node.footer, visited)}</div> : null}
      </div>
    );
  };

  const renderSplitNode = (node: SplitNode, visited: Set<string>) => {
    const directionClass =
      node.direction === "horizontal" ? "flex-row" : "flex-col";
    return (
      <div className={cn("flex", directionClass, styleToClassName(node.style))}>
        {node.header ? <div className="mb-2">{renderById(node.header, visited)}</div> : null}
        <div
          className={cn(
            "flex flex-1",
            directionClass,
            node.style?.gap ? undefined : "gap-2"
          )}
        >
          {node.children.map((child, index) => {
            const size = node.sizes?.[index];
            return (
              <div
                key={child}
                className={cn("min-w-0 min-h-0", node.direction === "horizontal" ? "flex" : undefined)}
                style={size ? { flexBasis: `${size}%`, flexGrow: 0 } : undefined}
              >
                {renderById(child, visited)}
              </div>
            );
          })}
        </div>
        {node.footer ? <div className="mt-2">{renderById(node.footer, visited)}</div> : null}
      </div>
    );
  };

  const renderStackNode = (node: StackNode, visited: Set<string>) => {
    const directionClass =
      node.direction === "horizontal" ? "flex-row" : "flex-col";
    return (
      <div
        className={cn(
          "flex",
          directionClass,
          node.style?.gap ? undefined : "gap-2",
          styleToClassName(node.style)
        )}
      >
        {node.children.map((child) => (
          <Fragment key={child}>{renderById(child, visited)}</Fragment>
        ))}
      </div>
    );
  };

  const renderScrollNode = (node: ScrollNode, visited: Set<string>) => {
    return (
      <div className={cn("min-h-0", styleToClassName({ ...node.style, overflow: "auto" }))}>
        {node.children.map((child) => (
          <Fragment key={child}>{renderById(child, visited)}</Fragment>
        ))}
      </div>
    );
  };

  const renderDividerNode = (_node: DividerNode) => {
    return <div className="my-2 h-px w-full bg-border/60" />;
  };

  const renderTextNode = (node: TextNode) => {
    return (
      <div className={cn("text-sm text-foreground", styleToClassName(node.style))}>
        {node.text}
      </div>
    );
  };

  const renderNode = (node: UINode, visited: Set<string>): ReactNode => {
    if (node.kind === "component") {
      const content = renderComponentImpl(node);
      const className = styleToClassName(node.style);
      const rendered = className ? <div className={className}>{content}</div> : content;
      return wrapNodeFrame(node, rendered);
    }
    return wrapNodeFrame(node, renderLayoutNode(node, visited));
  };

  return <div className="min-h-0">{renderById(spec.root, new Set())}</div>;
}
