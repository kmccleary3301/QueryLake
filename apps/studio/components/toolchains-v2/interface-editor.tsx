"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Droplets, Flame, Paperclip, SendHorizontal, Wind } from "lucide-react";

import { useContextAction } from "@/app/context-provider";
import ToolchainUISpecRendererV2 from "@/components/toolchains-v2/ui-spec-renderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { fetchToolchainConfig, updateToolchainConfig } from "@/hooks/querylakeAPI";
import { cn } from "@/lib/utils";
import {
  getToolchainComponentManifest,
  listToolchainComponents,
  type ToolchainComponentRegistryEntry,
} from "@/lib/toolchains-v2/component-registry";
import { validateToolchainUISpecV2 } from "@/lib/toolchains-v2/validation";
import type { ToolChain } from "@/types/toolchains";
import type { FieldSchema } from "@/types/toolchain-component-manifest";
import type {
  ComponentNode,
  HookBindingSpec,
  JSONValue,
  LayoutNode,
  StyleSpec,
  ToolchainUISpecV2,
  UINode,
} from "@/types/toolchain-ui-spec-v2";

type Props = {
  params: { workspace: string; toolchainId: string };
};

type PreviewWrapAction = "split-horizontal" | "split-vertical" | "stack-vertical" | "box";

const UNSET_SELECT_VALUE = "__unset__";
const SPEC_HISTORY_LIMIT = 80;

type StyleSelectKey = "padding" | "gap" | "surface" | "border" | "radius";
const STYLE_SELECT_KEYS: StyleSelectKey[] = [
  "padding",
  "gap",
  "surface",
  "border",
  "radius",
];
const STYLE_OPTIONS: Record<StyleSelectKey, string[]> = {
  padding: ["none", "xs", "sm", "md", "lg"],
  gap: ["none", "xs", "sm", "md", "lg"],
  surface: ["none", "panel", "muted", "inset"],
  border: ["none", "hairline"],
  radius: ["none", "sm", "md"],
};

function makeId(prefix: string): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return `${prefix}_${crypto.randomUUID()}`;
  }
  return `${prefix}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function createDefaultSpec(): ToolchainUISpecV2 {
  const rootId = "root";
  const headerId = "header";
  const contentId = "content";
  const chatId = "chat";

  return {
    version: 2,
    root: rootId,
    nodes: {
      [rootId]: {
        id: rootId,
        kind: "layout",
        type: "stack",
        direction: "vertical",
        style: { gap: "sm" },
        children: [headerId, contentId],
        label: "Root",
      },
      [headerId]: {
        id: headerId,
        kind: "layout",
        type: "text",
        text: "Toolchain UI (v2)",
        style: { padding: "sm" },
        label: "Header",
      },
      [contentId]: {
        id: contentId,
        kind: "layout",
        type: "box",
        style: { padding: "sm", surface: "panel", radius: "md" },
        children: [chatId],
        label: "Content",
      },
      [chatId]: {
        id: chatId,
        kind: "component",
        componentId: "chat",
        label: "Chat",
        config: {},
      },
    },
    meta: {
      name: "default",
      updatedAt: Date.now(),
    },
  };
}

function cloneSpecSnapshot(spec: ToolchainUISpecV2): ToolchainUISpecV2 {
  return JSON.parse(JSON.stringify(spec)) as ToolchainUISpecV2;
}

function isLayoutNode(node: UINode): node is LayoutNode {
  return node.kind === "layout";
}

function isComponentNode(node: UINode): node is ComponentNode {
  return node.kind === "component";
}

function nodeDisplayName(node: UINode): string {
  if (node.label) return node.label;
  if (node.kind === "component") return node.componentId;
  return node.type;
}

function getLayoutRefs(node: LayoutNode): string[] {
  switch (node.type) {
    case "split":
    case "box":
      return [
        ...(node.header ? [node.header] : []),
        ...node.children,
        ...(node.footer ? [node.footer] : []),
      ];
    case "stack":
    case "scroll":
      return [...node.children];
    case "divider":
    case "text":
      return [];
    default: {
      const exhaustive: never = node;
      return exhaustive;
    }
  }
}

type ParentRef = {
  parentId: string;
  slot: "children" | "header" | "footer";
  index: number | null;
};

function findParentRef(spec: ToolchainUISpecV2, targetId: string): ParentRef | null {
  for (const [parentId, node] of Object.entries(spec.nodes)) {
    if (!isLayoutNode(node)) continue;

    switch (node.type) {
      case "stack":
      case "scroll": {
        const index = node.children.indexOf(targetId);
        if (index >= 0) {
          return { parentId, slot: "children", index };
        }
        break;
      }
      case "split":
      case "box": {
        if (node.header === targetId) {
          return { parentId, slot: "header", index: null };
        }
        if (node.footer === targetId) {
          return { parentId, slot: "footer", index: null };
        }
        const index = node.children.indexOf(targetId);
        if (index >= 0) {
          return { parentId, slot: "children", index };
        }
        break;
      }
      case "divider":
      case "text":
        break;
      default: {
        const exhaustive: never = node;
        return exhaustive;
      }
    }
  }
  return null;
}

function appendChildToLayout(node: LayoutNode, childId: string): LayoutNode | null {
  switch (node.type) {
    case "split":
    case "box":
    case "stack":
    case "scroll":
      return { ...node, children: [...node.children, childId] };
    case "divider":
    case "text":
      return null;
    default: {
      const exhaustive: never = node;
      return exhaustive;
    }
  }
}

function removeSubtreeRefs(node: LayoutNode, subtree: Set<string>): LayoutNode {
  switch (node.type) {
    case "split":
    case "box":
      return {
        ...node,
        children: node.children.filter((id) => !subtree.has(id)),
        header: node.header && subtree.has(node.header) ? undefined : node.header,
        footer: node.footer && subtree.has(node.footer) ? undefined : node.footer,
      };
    case "stack":
    case "scroll":
      return {
        ...node,
        children: node.children.filter((id) => !subtree.has(id)),
      };
    case "divider":
    case "text":
      return node;
    default: {
      const exhaustive: never = node;
      return exhaustive;
    }
  }
}

function collectSubtreeIds(spec: ToolchainUISpecV2, rootId: string): Set<string> {
  const visited = new Set<string>();
  const walk = (id: string) => {
    if (visited.has(id)) return;
    visited.add(id);
    const node = spec.nodes[id];
    if (!node || node.kind !== "layout") return;
    for (const child of getLayoutRefs(node)) {
      walk(child);
    }
  };
  walk(rootId);
  return visited;
}

function findPathToNode(spec: ToolchainUISpecV2, targetId: string): string[] {
  const walk = (id: string, seen: Set<string>): string[] | null => {
    if (seen.has(id)) return null;
    const nextSeen = new Set(seen);
    nextSeen.add(id);

    if (id === targetId) return [id];
    const node = spec.nodes[id];
    if (!node || node.kind !== "layout") return null;
    for (const child of getLayoutRefs(node)) {
      const childPath = walk(child, nextSeen);
      if (childPath) return [id, ...childPath];
    }
    return null;
  };

  return walk(spec.root, new Set()) ?? [];
}

function createLayoutChild(kind: "stack" | "box" | "split" | "scroll" | "text" | "divider"): LayoutNode {
  switch (kind) {
    case "stack":
      return {
        id: makeId("stack"),
        kind: "layout",
        type: "stack",
        direction: "vertical",
        children: [],
        style: { gap: "sm" },
        label: "Stack",
      };
    case "box":
      return {
        id: makeId("box"),
        kind: "layout",
        type: "box",
        children: [],
        style: { padding: "sm", surface: "panel", radius: "md" },
        label: "Box",
      };
    case "split":
      return {
        id: makeId("split"),
        kind: "layout",
        type: "split",
        direction: "horizontal",
        children: [],
        style: { gap: "sm" },
        label: "Split",
      };
    case "scroll":
      return {
        id: makeId("scroll"),
        kind: "layout",
        type: "scroll",
        children: [],
        style: { padding: "sm" },
        label: "Scroll",
      };
    case "text":
      return {
        id: makeId("text"),
        kind: "layout",
        type: "text",
        text: "Text",
        style: {},
        label: "Text",
      };
    case "divider":
      return {
        id: makeId("divider"),
        kind: "layout",
        type: "divider",
        style: {},
        label: "Divider",
      };
    default: {
      const exhaustive: never = kind;
      return exhaustive;
    }
  }
}

function cloneNodeWithNewRefs(
  node: UINode,
  idMap: Record<string, string>
): UINode {
  const nextId = idMap[node.id] ?? node.id;
  if (isComponentNode(node)) {
    return {
      ...node,
      id: nextId,
    };
  }

  switch (node.type) {
    case "stack":
    case "scroll":
      return {
        ...node,
        id: nextId,
        children: node.children.map((childId) => idMap[childId] ?? childId),
      };
    case "split":
    case "box":
      return {
        ...node,
        id: nextId,
        children: node.children.map((childId) => idMap[childId] ?? childId),
        header: node.header ? (idMap[node.header] ?? node.header) : undefined,
        footer: node.footer ? (idMap[node.footer] ?? node.footer) : undefined,
      };
    case "divider":
    case "text":
      return {
        ...node,
        id: nextId,
      };
    default: {
      const exhaustive: never = node;
      return exhaustive;
    }
  }
}

function cloneSubtree(spec: ToolchainUISpecV2, rootId: string): {
  nodes: Record<string, UINode>;
  rootId: string;
} {
  const subtreeIds = Array.from(collectSubtreeIds(spec, rootId));
  const idMap: Record<string, string> = {};
  for (const oldId of subtreeIds) {
    const node = spec.nodes[oldId];
    if (!node) continue;
    const prefix = isLayoutNode(node) ? node.type : "cmp";
    idMap[oldId] = makeId(prefix);
  }

  const clonedNodes: Record<string, UINode> = {};
  for (const oldId of subtreeIds) {
    const node = spec.nodes[oldId];
    if (!node) continue;
    const cloned = cloneNodeWithNewRefs(node, idMap);
    clonedNodes[cloned.id] = cloned;
  }

  return {
    nodes: clonedNodes,
    rootId: idMap[rootId] ?? rootId,
  };
}

function buildDefaultConfig(
  manifest: ReturnType<typeof getToolchainComponentManifest> | undefined
): Record<string, JSONValue> {
  const defaults: Record<string, JSONValue> = {};
  if (!manifest?.config) return defaults;
  for (const [key, field] of Object.entries(manifest.config)) {
    if (field.default !== undefined) {
      defaults[key] = field.default as JSONValue;
    }
  }
  return defaults;
}

type ComponentHookDraft = {
  id: string;
  hook: string;
  fireIndex: number;
  targetEvent: string;
  targetRoute: string;
  payloadPath: string;
  store: boolean;
};

function hookBindingToDraft(binding: HookBindingSpec, fallbackId: string): ComponentHookDraft {
  const firstFire = [...binding.fires].sort((a, b) => a.index - b.index)[0];
  const emitAction = firstFire?.actions.find(
    (
      action
    ): action is Extract<
      HookBindingSpec["fires"][number]["actions"][number],
      { type: "emitEvent" }
    > => action.type === "emitEvent"
  );
  const firstInput = emitAction ? Object.entries(emitAction.inputs ?? {})[0] : undefined;
  const payloadPath =
    firstInput && "path" in firstInput[1] ? firstInput[1].path : "/";
  return {
    id: fallbackId,
    hook: binding.hook,
    fireIndex: firstFire?.index ?? 1,
    targetEvent: emitAction?.nodeId ?? "",
    targetRoute: firstInput?.[0] ?? "value",
    payloadPath,
    store: Boolean(emitAction?.await),
  };
}

function hookDraftToBinding(draft: ComponentHookDraft): HookBindingSpec | null {
  const hook = draft.hook.trim();
  const targetEvent = draft.targetEvent.trim();
  if (!hook || !targetEvent) return null;
  const targetRoute = draft.targetRoute.trim() || "value";
  const payloadPath = draft.payloadPath.trim() || "/";
  return {
    hook,
    fires: [
      {
        index: Math.max(1, Math.floor(draft.fireIndex || 1)),
        actions: [
          {
            type: "emitEvent",
            nodeId: targetEvent,
            inputs: {
              [targetRoute]: {
                kind: "payload",
                path: payloadPath,
              },
            },
            ...(draft.store ? { await: true } : {}),
          },
        ],
      },
    ],
  };
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function MockChatPreview() {
  return (
    <div className="rounded-[14px] border border-border/70 bg-background/95 px-3 py-3 text-sm shadow-[0_10px_30px_hsl(var(--background)/0.18)]">
      <div className="mb-2 text-xs text-muted-foreground">chat_history</div>
      <div className="space-y-2">
        <div className="rounded-[10px] bg-muted/40 px-2 py-1.5">
          <div className="text-[11px] text-muted-foreground">You</div>
          <div>Lorem ipsum dolor sit amet.</div>
        </div>
        <div className="rounded-[10px] border border-border/60 bg-card px-2 py-1.5">
          <div className="text-[11px] text-muted-foreground">QueryLake</div>
          <div className="font-medium">Lorem Ipsum</div>
          <div className="text-muted-foreground">dolor sit amet, consectetur adipiscing elit.</div>
        </div>
      </div>
    </div>
  );
}

function MockChatInputPreview() {
  return (
    <div className="rounded-[14px] border border-dashed border-border/70 bg-background/95 px-2 py-2 shadow-[0_10px_30px_hsl(var(--background)/0.14)]">
      <div className="flex items-center gap-2 rounded-[10px] border border-border/70 bg-card px-2 py-1.5">
        <span className="flex-1 text-sm text-muted-foreground">Message</span>
        <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
        <SendHorizontal className="h-3.5 w-3.5 text-muted-foreground" />
      </div>
    </div>
  );
}

function MockBasfIntroPreview() {
  const chips = [
    { label: "How do we handle vapor recovery?", icon: Flame },
    { label: "Tell me about mineral oil procedures.", icon: Droplets },
    { label: "Flue-gas analysis guides.", icon: Wind },
  ];
  return (
    <div className="rounded-[16px] border border-border/70 bg-background/95 px-3 py-3 shadow-[0_12px_36px_hsl(var(--background)/0.18)]">
      <div className="mb-3 text-center text-base font-semibold">What can I help you find?</div>
      <div className="grid gap-2 md:grid-cols-3">
        {chips.map((chip) => {
          const Icon = chip.icon;
          return (
            <div
              key={chip.label}
              className="rounded-[12px] border border-border/60 bg-muted/25 px-2 py-3 text-center"
            >
              <Icon className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
              <div className="text-xs text-muted-foreground">{chip.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ToolchainInterfaceEditorV2({ params }: Props) {
  const { userData, authReviewed, loginValid } = useContextAction();
  const [toolchain, setToolchain] = useState<ToolChain | null>(null);
  const [spec, setSpec] = useState<ToolchainUISpecV2 | null>(null);
  const [baselineSpecSerialized, setBaselineSpecSerialized] = useState("");
  const [undoStack, setUndoStack] = useState<ToolchainUISpecV2[]>([]);
  const [redoStack, setRedoStack] = useState<ToolchainUISpecV2[]>([]);
  const historyModeRef = useRef<"record" | "skip">("record");
  const previousSpecRef = useRef<ToolchainUISpecV2 | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draggingNodeId, setDraggingNodeId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) return;
    fetchToolchainConfig({
      auth: userData.auth,
      toolchain_id: params.toolchainId,
      onFinish: (result: ToolChain) => {
        historyModeRef.current = "skip";
        previousSpecRef.current = null;
        setUndoStack([]);
        setRedoStack([]);
        setToolchain(result);
        const parsed = result.ui_spec_v2
          ? validateToolchainUISpecV2(result.ui_spec_v2)
          : null;
        const nextSpec =
          parsed && parsed.success ? parsed.data : createDefaultSpec();
        setSpec(nextSpec);
        setBaselineSpecSerialized(JSON.stringify(nextSpec));
        setSelectedId(nextSpec.root);
      },
    });
  }, [authReviewed, loginValid, userData?.auth, params.toolchainId]);

  useEffect(() => {
    if (!spec) {
      previousSpecRef.current = null;
      return;
    }

    const currentSnapshot = cloneSpecSnapshot(spec);
    if (!previousSpecRef.current) {
      previousSpecRef.current = currentSnapshot;
      historyModeRef.current = "record";
      return;
    }

    if (historyModeRef.current === "record") {
      const previousSnapshot = previousSpecRef.current;
      setUndoStack((prev) => [...prev, previousSnapshot].slice(-SPEC_HISTORY_LIMIT));
      setRedoStack([]);
    }

    previousSpecRef.current = currentSnapshot;
    historyModeRef.current = "record";
  }, [spec]);

  useEffect(() => {
    if (!spec) return;
    if (selectedId && spec.nodes[selectedId]) return;
    setSelectedId(spec.root);
  }, [selectedId, spec]);

  const registry = useMemo(() => {
    const entries = listToolchainComponents().slice();
    entries.sort((a, b) =>
      (a.manifest.title ?? a.manifest.id).localeCompare(
        b.manifest.title ?? b.manifest.id
      )
    );
    return entries;
  }, []);

  const validation = useMemo(() => {
    if (!spec) return null;
    return validateToolchainUISpecV2(spec);
  }, [spec]);

  const validationErrors = useMemo(() => {
    if (!validation || validation.success) return [];
    return validation.error.issues.map((issue) => issue.message);
  }, [validation]);

  const treeItems = useMemo(() => {
    if (!spec) return [] as Array<{ id: string; depth: number }>;
    const items: Array<{ id: string; depth: number }> = [];
    const visited = new Set<string>();

    const walk = (id: string, depth: number) => {
      if (visited.has(id)) return;
      visited.add(id);
      items.push({ id, depth });

      const node = spec.nodes[id];
      if (!node || node.kind !== "layout") return;
      for (const child of getLayoutRefs(node)) {
        walk(child, depth + 1);
      }
    };

    walk(spec.root, 0);
    return items;
  }, [spec]);

  const selectedNode = useMemo(() => {
    if (!spec || !selectedId) return null;
    return spec.nodes[selectedId] ?? null;
  }, [spec, selectedId]);

  const selectedComponentNode = useMemo(
    () => (selectedNode && selectedNode.kind === "component" ? selectedNode : null),
    [selectedNode]
  );

  const selectedComponentManifest = useMemo(
    () =>
      selectedComponentNode
        ? getToolchainComponentManifest(selectedComponentNode.componentId)
        : null,
    [selectedComponentNode]
  );

  const selectedComponentQuickFields = useMemo(() => {
    if (!selectedComponentManifest) return [] as Array<[string, FieldSchema]>;
    return Object.entries(selectedComponentManifest.config ?? {}).slice(0, 3);
  }, [selectedComponentManifest]);

  const [componentQuickJsonDrafts, setComponentQuickJsonDrafts] = useState<Record<string, string>>(
    {}
  );
  const [componentDrawerRequestNonce, setComponentDrawerRequestNonce] = useState(0);

  useEffect(() => {
    setComponentQuickJsonDrafts({});
  }, [selectedComponentNode?.id]);

  const hasUnsavedChanges = useMemo(() => {
    if (!spec || !baselineSpecSerialized) return false;
    return JSON.stringify(spec) !== baselineSpecSerialized;
  }, [baselineSpecSerialized, spec]);

  const selectedPath = useMemo(() => {
    if (!spec || !selectedId) return [] as string[];
    return findPathToNode(spec, selectedId);
  }, [spec, selectedId]);

  const selectedParentRef = useMemo(() => {
    if (!spec || !selectedId) return null;
    return findParentRef(spec, selectedId);
  }, [spec, selectedId]);

  const canMoveSelectedUp = useMemo(() => {
    return Boolean(
      selectedParentRef &&
        selectedParentRef.slot === "children" &&
        selectedParentRef.index !== null &&
        selectedParentRef.index > 0
    );
  }, [selectedParentRef]);

  const canMoveSelectedDown = useMemo(() => {
    if (!spec || !selectedParentRef) return false;
    if (selectedParentRef.slot !== "children" || selectedParentRef.index === null) {
      return false;
    }
    const parent = spec.nodes[selectedParentRef.parentId];
    if (!parent || !isLayoutNode(parent)) return false;
    if (parent.type === "divider" || parent.type === "text") return false;
    return selectedParentRef.index < parent.children.length - 1;
  }, [selectedParentRef, spec]);

  const canDuplicateSelected = useMemo(() => {
    return Boolean(selectedParentRef && selectedParentRef.slot === "children");
  }, [selectedParentRef]);

  const renderPreviewComponent = useCallback((node: ComponentNode) => {
    if (node.componentId === "chat") return <MockChatPreview />;
    if (node.componentId === "chat-input") return <MockChatInputPreview />;
    if (node.componentId === "basf-intro-screen") return <MockBasfIntroPreview />;
    return (
      <div className="rounded-sm border border-dashed border-border/70 bg-muted/10 px-3 py-2 text-xs text-muted-foreground">
        <div className="font-medium text-foreground/80">{node.label ?? node.componentId}</div>
        <div className="text-[11px] opacity-80">{node.componentId}</div>
      </div>
    );
  }, []);

  const updateNode = (id: string, updater: (node: UINode) => UINode) => {
    setSpec((prev) => {
      if (!prev) return prev;
      const current = prev.nodes[id];
      if (!current) return prev;
      const nextNode = updater(current);
      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [id]: { ...nextNode, id },
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
  };

  const addChildToNode = (targetId: string, child: UINode) => {
    setSpec((prev) => {
      if (!prev) return prev;
      const parent = prev.nodes[targetId];
      if (!parent || !isLayoutNode(parent)) return prev;
      const nextParent = appendChildToLayout(parent, child.id);
      if (!nextParent) return prev;

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [targetId]: nextParent,
          [child.id]: child,
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
    setSelectedId(child.id);
  };

  const addChildToSelected = (child: UINode) => {
    if (!selectedId) return;
    addChildToNode(selectedId, child);
  };

  const wrapNodeInLayout = (targetNodeId: string, action: PreviewWrapAction) => {
    let wrappedId: string | null = null;
    setSpec((prev) => {
      if (!prev || targetNodeId === prev.root) return prev;
      const parentRef = findParentRef(prev, targetNodeId);
      if (!parentRef || parentRef.slot !== "children" || parentRef.index === null) {
        return prev;
      }
      const parentNode = prev.nodes[parentRef.parentId];
      if (!parentNode || !isLayoutNode(parentNode)) return prev;
      if (parentNode.type === "divider" || parentNode.type === "text") return prev;

      const wrapperBase =
        action === "split-horizontal" || action === "split-vertical"
          ? createLayoutChild("split")
          : action === "stack-vertical"
            ? createLayoutChild("stack")
            : createLayoutChild("box");

      const wrapper: LayoutNode =
        wrapperBase.type === "split"
          ? {
              ...wrapperBase,
              direction:
                action === "split-horizontal"
                  ? ("horizontal" as const)
                  : ("vertical" as const),
              label:
                action === "split-horizontal"
                  ? "Horizontal Split"
                  : "Vertical Split",
            }
          : wrapperBase.type === "stack"
            ? {
                ...wrapperBase,
                direction: "vertical" as const,
                label: "Vertical Stack",
              }
            : wrapperBase;

      const nextChildren = [...parentNode.children];
      nextChildren[parentRef.index] = wrapper.id;
      wrappedId = wrapper.id;

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [parentRef.parentId]: {
            ...parentNode,
            children: nextChildren,
          },
          [wrapper.id]: {
            ...wrapper,
            children: [targetNodeId],
          },
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
    if (wrappedId) {
      setSelectedId(wrappedId);
    }
  };

  const deleteNodeById = (targetId: string) => {
    if (!spec || !targetId || targetId === spec.root) return;
    const subtree = collectSubtreeIds(spec, targetId);

    setSpec((prev) => {
      if (!prev) return prev;
      const nextNodes: Record<string, UINode> = {};

      for (const [id, node] of Object.entries(prev.nodes)) {
        if (subtree.has(id)) continue;
        if (node.kind === "layout") {
          nextNodes[id] = removeSubtreeRefs(node, subtree);
        } else {
          nextNodes[id] = node;
        }
      }

      return {
        ...prev,
        nodes: nextNodes,
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });

    if (selectedId === targetId) {
      setSelectedId(spec.root);
    }
  };

  const deleteSelectedNode = () => {
    if (!selectedId) return;
    deleteNodeById(selectedId);
  };

  const reorderNodeRelative = (
    sourceNodeId: string,
    targetNodeId: string,
    placement: "before" | "after"
  ) => {
    if (!sourceNodeId || !targetNodeId || sourceNodeId === targetNodeId) return;
    setSpec((prev) => {
      if (!prev) return prev;
      const sourceParentRef = findParentRef(prev, sourceNodeId);
      const targetParentRef = findParentRef(prev, targetNodeId);
      if (
        !sourceParentRef ||
        !targetParentRef ||
        sourceParentRef.slot !== "children" ||
        targetParentRef.slot !== "children"
      ) {
        return prev;
      }

      const sourceParentNode = prev.nodes[sourceParentRef.parentId];
      const targetParentNode = prev.nodes[targetParentRef.parentId];
      if (!sourceParentNode || !targetParentNode) return prev;
      if (!isLayoutNode(sourceParentNode) || !isLayoutNode(targetParentNode)) return prev;
      if (
        sourceParentNode.type === "divider" ||
        sourceParentNode.type === "text" ||
        targetParentNode.type === "divider" ||
        targetParentNode.type === "text"
      ) {
        return prev;
      }

      const sourceSubtree = collectSubtreeIds(prev, sourceNodeId);
      if (sourceSubtree.has(targetNodeId) || sourceSubtree.has(targetParentRef.parentId)) {
        return prev;
      }

      const sourceChildren = [...sourceParentNode.children];
      const sourceIndex = sourceChildren.indexOf(sourceNodeId);
      if (sourceIndex < 0) return prev;
      sourceChildren.splice(sourceIndex, 1);

      const targetChildren =
        sourceParentRef.parentId === targetParentRef.parentId
          ? sourceChildren
          : [...targetParentNode.children];
      const targetIndex = targetChildren.indexOf(targetNodeId);
      if (targetIndex < 0) return prev;

      const insertIndex = placement === "before" ? targetIndex : targetIndex + 1;
      targetChildren.splice(insertIndex, 0, sourceNodeId);

      if (sourceParentRef.parentId === targetParentRef.parentId) {
        return {
          ...prev,
          nodes: {
            ...prev.nodes,
            [sourceParentRef.parentId]: {
              ...sourceParentNode,
              children: targetChildren,
            },
          },
          meta: {
            ...(prev.meta ?? {}),
            updatedAt: Date.now(),
          },
        };
      }

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [sourceParentRef.parentId]: {
            ...sourceParentNode,
            children: sourceChildren,
          },
          [targetParentRef.parentId]: {
            ...targetParentNode,
            children: targetChildren,
          },
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
  };

  const moveNodeIntoLayout = (sourceNodeId: string, targetLayoutId: string) => {
    if (!sourceNodeId || !targetLayoutId || sourceNodeId === targetLayoutId) return;
    setSpec((prev) => {
      if (!prev) return prev;
      const sourceParentRef = findParentRef(prev, sourceNodeId);
      if (!sourceParentRef || sourceParentRef.slot !== "children") return prev;

      const sourceParentNode = prev.nodes[sourceParentRef.parentId];
      const targetNode = prev.nodes[targetLayoutId];
      if (!sourceParentNode || !targetNode) return prev;
      if (!isLayoutNode(sourceParentNode) || !isLayoutNode(targetNode)) return prev;
      if (
        sourceParentNode.type === "divider" ||
        sourceParentNode.type === "text" ||
        targetNode.type === "divider" ||
        targetNode.type === "text"
      ) {
        return prev;
      }

      const sourceSubtree = collectSubtreeIds(prev, sourceNodeId);
      if (sourceSubtree.has(targetLayoutId)) return prev;

      const sourceChildren = [...sourceParentNode.children];
      const sourceIndex = sourceChildren.indexOf(sourceNodeId);
      if (sourceIndex < 0) return prev;
      sourceChildren.splice(sourceIndex, 1);

      const targetChildren =
        sourceParentRef.parentId === targetLayoutId ? sourceChildren : [...targetNode.children];
      targetChildren.push(sourceNodeId);

      if (sourceParentRef.parentId === targetLayoutId) {
        return {
          ...prev,
          nodes: {
            ...prev.nodes,
            [targetLayoutId]: {
              ...targetNode,
              children: targetChildren,
            },
          },
          meta: {
            ...(prev.meta ?? {}),
            updatedAt: Date.now(),
          },
        };
      }

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [sourceParentRef.parentId]: {
            ...sourceParentNode,
            children: sourceChildren,
          },
          [targetLayoutId]: {
            ...targetNode,
            children: targetChildren,
          },
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
  };

  const insertSiblingRelative = (
    targetNodeId: string,
    placement: "before" | "after"
  ) => {
    let insertedId: string | null = null;
    setSpec((prev) => {
      if (!prev) return prev;
      const targetParentRef = findParentRef(prev, targetNodeId);
      if (
        !targetParentRef ||
        targetParentRef.slot !== "children" ||
        targetParentRef.index === null
      ) {
        return prev;
      }
      const parentNode = prev.nodes[targetParentRef.parentId];
      if (!parentNode || !isLayoutNode(parentNode)) return prev;
      if (parentNode.type === "divider" || parentNode.type === "text") return prev;

      const nextChild = createLayoutChild("box");
      insertedId = nextChild.id;
      const nextChildren = [...parentNode.children];
      const targetIndex = nextChildren.indexOf(targetNodeId);
      if (targetIndex < 0) return prev;
      const insertIndex = placement === "before" ? targetIndex : targetIndex + 1;
      nextChildren.splice(insertIndex, 0, nextChild.id);

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [targetParentRef.parentId]: {
            ...parentNode,
            children: nextChildren,
          },
          [nextChild.id]: nextChild,
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
    if (insertedId) {
      setSelectedId(insertedId);
    }
  };

  const moveSelectedInParent = (direction: -1 | 1) => {
    if (!selectedId) return;
    setSpec((prev) => {
      if (!prev) return prev;
      const parentRef = findParentRef(prev, selectedId);
      if (!parentRef || parentRef.slot !== "children" || parentRef.index === null) {
        return prev;
      }
      const parentNode = prev.nodes[parentRef.parentId];
      if (!parentNode || !isLayoutNode(parentNode)) return prev;
      if (parentNode.type === "divider" || parentNode.type === "text") return prev;
      const from = parentRef.index;
      const to = from + direction;
      if (to < 0 || to >= parentNode.children.length) return prev;

      const nextChildren = [...parentNode.children];
      const [moved] = nextChildren.splice(from, 1);
      nextChildren.splice(to, 0, moved);
      const nextParent = {
        ...parentNode,
        children: nextChildren,
      };

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          [parentRef.parentId]: nextParent,
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
  };

  const duplicateSelectedNode = () => {
    if (!selectedId) return;
    let duplicatedId: string | null = null;
    setSpec((prev) => {
      if (!prev) return prev;
      const parentRef = findParentRef(prev, selectedId);
      if (!parentRef || parentRef.slot !== "children" || parentRef.index === null) {
        return prev;
      }
      const parentNode = prev.nodes[parentRef.parentId];
      if (!parentNode || !isLayoutNode(parentNode)) return prev;
      if (parentNode.type === "divider" || parentNode.type === "text") return prev;

      const cloned = cloneSubtree(prev, selectedId);
      duplicatedId = cloned.rootId;
      const nextChildren = [...parentNode.children];
      nextChildren.splice(parentRef.index + 1, 0, cloned.rootId);

      return {
        ...prev,
        nodes: {
          ...prev.nodes,
          ...cloned.nodes,
          [parentRef.parentId]: {
            ...parentNode,
            children: nextChildren,
          },
        },
        meta: {
          ...(prev.meta ?? {}),
          updatedAt: Date.now(),
        },
      };
    });
    if (duplicatedId) {
      setSelectedId(duplicatedId);
      toast.success("Duplicated selected node subtree.");
    }
  };

  const saveInterface = () => {
    if (!toolchain || !spec || !userData?.auth) return;
    const parsed = validateToolchainUISpecV2(spec);
    if (!parsed.success) {
      toast.error("UI spec is invalid; fix validation errors first.");
      return;
    }

    setSaveFailed(false);
    setSaving(true);
    const nextToolchain: ToolChain = {
      ...toolchain,
      ui_spec_v2: {
        ...parsed.data,
        meta: {
          ...(parsed.data.meta ?? {}),
          updatedAt: Date.now(),
        },
      },
    };

    updateToolchainConfig({
      auth: userData.auth,
      toolchain_id: params.toolchainId,
      toolchain: nextToolchain as unknown as Record<string, unknown>,
      onFinish: (result: { toolchain_id: string } | false) => {
        setSaving(false);
        if (!result) {
          setSaveFailed(true);
          toast.error("Failed to save interface. Retry without losing draft.");
          return;
        }
        setSaveFailed(false);
        setToolchain(nextToolchain);
        setBaselineSpecSerialized(JSON.stringify(parsed.data));
        toast.success("Saved interface spec");
      },
    });
  };

  const setStyleValue = (key: StyleSelectKey, value: string) => {
    if (!selectedNode) return;
    updateNode(selectedNode.id, (node) => {
      const nextStyle: StyleSpec = { ...(node.style ?? {}) };
      if (value === UNSET_SELECT_VALUE) {
        delete nextStyle[key];
      } else {
        nextStyle[key] = value as never;
      }
      return { ...node, style: Object.keys(nextStyle).length ? nextStyle : undefined };
    });
  };

  const undoChanges = useCallback(() => {
    if (!spec || undoStack.length === 0) return;
    const previousSnapshot = undoStack[undoStack.length - 1];
    historyModeRef.current = "skip";
    setUndoStack((prev) => prev.slice(0, -1));
    setRedoStack((prev) => [...prev, cloneSpecSnapshot(spec)].slice(-SPEC_HISTORY_LIMIT));
    setSpec(cloneSpecSnapshot(previousSnapshot));
    toast.success("Undid latest interface edit.");
  }, [spec, undoStack]);

  const redoChanges = useCallback(() => {
    if (!spec || redoStack.length === 0) return;
    const nextSnapshot = redoStack[redoStack.length - 1];
    historyModeRef.current = "skip";
    setRedoStack((prev) => prev.slice(0, -1));
    setUndoStack((prev) => [...prev, cloneSpecSnapshot(spec)].slice(-SPEC_HISTORY_LIMIT));
    setSpec(cloneSpecSnapshot(nextSnapshot));
    toast.success("Redid interface edit.");
  }, [redoStack, spec]);

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
  if (!toolchain || !spec) {
    return <div className="ql-editor-state">Loading toolchain...</div>;
  }

  const canDeleteSelected = selectedId !== null && selectedId !== spec.root;
  const selectedPathLabels = selectedPath
    .map((id) => spec.nodes[id])
    .filter((node): node is UINode => Boolean(node))
    .map((node) => nodeDisplayName(node));
  const hasPreviewSelection = Boolean(selectedNode);
  const previewFocusLabel = selectedNode ? nodeDisplayName(selectedNode) : null;

  return (
    <div className="ql-editor-shell">
      <div className="ql-editor-hero">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-3">
            <div className="ql-editor-kicker">Visual interface design</div>
            <div className="space-y-1">
              <div className="text-xl font-semibold tracking-tight">Interface designer</div>
              <div className="max-w-3xl text-sm text-muted-foreground">
                Build the toolchain surface as a visual artifact first. Tree structure and component schema should support the preview, not dominate it.
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">Toolchain <span className="ml-1 font-mono">{toolchain.id}</span></Badge>
              <Badge variant="outline">Nodes {Object.keys(spec.nodes).length}</Badge>
              {hasPreviewSelection ? (
                <Badge variant="outline" className="border-cyan-400/50 bg-cyan-500/10 text-cyan-100">
                  Preview edit active
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
              {hasUnsavedChanges ? "Unsaved interface changes" : "All interface changes saved"}
            </div>
            <Button size="sm" variant="outline" onClick={undoChanges} disabled={undoStack.length === 0}>
              Undo
            </Button>
            <Button size="sm" variant="outline" onClick={redoChanges} disabled={redoStack.length === 0}>
              Redo
            </Button>
            <Button size="sm" variant="outline" onClick={saveInterface} disabled={!saveFailed || saving}>
              Retry save
            </Button>
            <Button size="sm" onClick={saveInterface} disabled={saving}>
              {saving ? "Saving..." : "Save interface"}
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={deleteSelectedNode}
              disabled={!canDeleteSelected}
            >
              Delete node
            </Button>
          </div>
        </div>
        <div className="mt-4 grid gap-2 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div className="rounded-[14px] border border-border/70 bg-background/35 px-3 py-2">
            <div className="text-xs font-medium text-foreground">Interaction model</div>
            <div className="mt-1 text-xs text-muted-foreground">
              Click directly on preview nodes to select them. Use the structure map for navigation and drag reordering support.
            </div>
          </div>
          <div className="rounded-[14px] border border-border/70 bg-background/35 px-3 py-2">
            <div className="text-xs font-medium text-foreground">Current focus</div>
            <div className="mt-1 text-xs text-muted-foreground">
              {selectedNode
                ? `${nodeDisplayName(selectedNode)} is active in the preview and inspector.`
                : "No node selected yet. The preview artifact should remain the dominant surface."}
            </div>
          </div>
        </div>
      </div>

      {saveFailed ? (
        <div className="ql-editor-alert-warning">
          Last interface save failed. Use <span className="font-semibold">Retry save</span> or keep editing.
        </div>
      ) : null}

      {selectedPathLabels.length ? (
        <div className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span className="ql-editor-kicker mr-2 tracking-[0.12em]">Selection path</span>
          {selectedPathLabels.map((name, index) => (
            <Badge key={`${name}-${index}`} variant="outline">
              {name}
            </Badge>
          ))}
        </div>
      ) : null}

      {validationErrors.length ? (
        <div className="ql-editor-alert-error border-destructive/30 p-3 text-sm">
          <div className="font-medium">Validation errors</div>
          <ul className="mt-2 list-disc space-y-1 pl-4">
            {validationErrors.slice(0, 6).map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
          {validationErrors.length > 6 ? (
            <div className="mt-2 text-xs opacity-80">
              (+{validationErrors.length - 6} more)
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[230px_minmax(0,1fr)_320px]">
        <div
          className={cn(
            "ql-editor-panel p-3 transition-all duration-200",
            hasPreviewSelection ? "opacity-60 saturate-[0.8] lg:scale-[0.99]" : undefined
          )}
        >
          <div className="space-y-1">
            <div className="text-sm font-semibold">Structure map</div>
            <div className="ql-editor-caption">Use this rail for hierarchy and reorder moves.</div>
          </div>
          <div className="mt-2">
            <ScrollArea className="h-[620px] pr-2">
              <div className="space-y-1">
                {treeItems.map((item) => {
                  const node = spec.nodes[item.id];
                  if (!node) return null;
                  const parentRef = findParentRef(spec, item.id);
                  const rowDraggable = Boolean(parentRef && parentRef.slot === "children");
                  const isSelected = item.id === selectedId;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      draggable={rowDraggable}
                      onDragStart={(event) => {
                        if (!rowDraggable) return;
                        event.dataTransfer.effectAllowed = "move";
                        event.dataTransfer.setData("text/plain", item.id);
                        setDraggingNodeId(item.id);
                      }}
                      onDragEnd={() => setDraggingNodeId(null)}
                      onDragOver={(event) => {
                        if (!rowDraggable || !draggingNodeId) return;
                        event.preventDefault();
                        event.dataTransfer.dropEffect = "move";
                      }}
                      onDrop={(event) => {
                        if (!rowDraggable) return;
                        event.preventDefault();
                        const sourceNodeId =
                          event.dataTransfer.getData("text/plain") || draggingNodeId;
                        if (!sourceNodeId) return;
                        const rect = event.currentTarget.getBoundingClientRect();
                        const relativeY = event.clientY - rect.top;
                        const relativeRatio = rect.height > 0 ? relativeY / rect.height : 0.5;
                        if (
                          node.kind === "layout" &&
                          node.type !== "divider" &&
                          node.type !== "text" &&
                          relativeRatio >= 0.34 &&
                          relativeRatio <= 0.66
                        ) {
                          moveNodeIntoLayout(sourceNodeId, item.id);
                        } else {
                          const placement: "before" | "after" =
                            relativeRatio < 0.5 ? "before" : "after";
                          reorderNodeRelative(sourceNodeId, item.id, placement);
                        }
                        setDraggingNodeId(null);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-sm px-2 py-1 text-left text-sm hover:bg-muted",
                        isSelected ? "bg-muted" : undefined,
                        draggingNodeId === item.id ? "opacity-60" : undefined
                      )}
                      style={{ paddingLeft: 8 + item.depth * 12 }}
                    >
                      <span className="text-xs text-muted-foreground">
                        {node.kind === "layout" ? "L" : "C"}
                      </span>
                      <span className="truncate">{nodeDisplayName(node)}</span>
                      <span className="ml-auto text-[10px] text-muted-foreground">
                        {item.id}
                      </span>
                    </button>
                  );
                })}
              </div>
            </ScrollArea>
          </div>
        </div>

        <div
          className={cn(
            "ql-editor-stage transition-all duration-200",
            hasPreviewSelection
              ? "border-cyan-400/45 shadow-[inset_0_1px_0_hsl(var(--foreground)/0.04),0_18px_42px_rgba(20,184,166,0.16)]"
              : undefined
          )}
        >
          <div className="flex flex-wrap items-center justify-between gap-2 px-1">
            <div>
              <div className="text-sm font-semibold">Live interface preview</div>
              <div className="ql-editor-caption">
                This should feel like the product surface, not a boxed schema sample.
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {hasPreviewSelection && previewFocusLabel ? (
                <div className="rounded-full border border-cyan-400/45 bg-cyan-500/10 px-2 py-1 text-[11px] text-cyan-100">
                  Editing {previewFocusLabel}
                </div>
              ) : null}
              <div className="rounded-full border border-border/70 bg-background/40 px-2 py-1 text-[11px] text-muted-foreground">
                Click preview nodes to select and edit
              </div>
            </div>
          </div>
          <div className="ql-editor-artifact-stage mt-2 h-[680px] overflow-auto">
            <div className="ql-editor-artifact-frame max-w-[1120px] p-4">
              {hasPreviewSelection && previewFocusLabel ? (
                <div className="mb-3 flex flex-wrap items-center gap-2 border-b border-border/60 pb-3">
                  <span className="rounded-full border border-cyan-400/45 bg-cyan-500/10 px-3 py-1 text-[11px] font-medium tracking-[0.08em] text-cyan-100">
                    Preview editing mode
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Selected artifact: <span className="font-medium text-foreground">{previewFocusLabel}</span>
                  </span>
                  {selectedPathLabels.length ? (
                    <div className="flex flex-wrap items-center gap-1">
                      {selectedPathLabels.map((name, index) => (
                        <Badge key={`preview-path-${name}-${index}`} variant="outline">
                          {name}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}
              {selectedComponentNode && selectedComponentManifest ? (
                <div className="mb-4 rounded-[16px] border border-cyan-400/35 bg-[radial-gradient(circle_at_top_left,hsl(var(--chart-2)/0.14),transparent_26%),linear-gradient(180deg,hsl(var(--background)/0.97),hsl(var(--card)/0.91))] p-4 shadow-[0_18px_36px_rgba(20,184,166,0.12)]">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div>
                        <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-cyan-200/80">
                          Active component
                        </div>
                        <div className="mt-1 text-sm font-semibold text-foreground">
                          {selectedComponentNode.label ?? selectedComponentManifest.title ?? selectedComponentNode.componentId}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 text-[11px]">
                        <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                          Component: <span className="font-mono">{selectedComponentNode.componentId}</span>
                        </span>
                        {selectedComponentNode.style?.className ? (
                          <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                            Tailwind: <span className="font-mono">{selectedComponentNode.style.className}</span>
                          </span>
                        ) : (
                          <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-muted-foreground">
                            No Tailwind overrides
                          </span>
                        )}
                        <span className="rounded-full border border-border/70 bg-background/45 px-2.5 py-1 text-foreground">
                          Hooks: <span className="font-mono">{selectedComponentNode.hooks?.length ?? 0}</span>
                        </span>
                      </div>
                      {selectedComponentManifest.description ? (
                        <div className="max-w-[72ch] text-xs text-muted-foreground">
                          {selectedComponentManifest.description}
                        </div>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => setComponentDrawerRequestNonce((value) => value + 1)}
                      >
                        Advanced drawer
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={duplicateSelectedNode}
                        disabled={!canDuplicateSelected}
                      >
                        Duplicate
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => moveSelectedInParent(-1)}
                        disabled={!canMoveSelectedUp}
                      >
                        Move up
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => moveSelectedInParent(1)}
                        disabled={!canMoveSelectedDown}
                      >
                        Move down
                      </Button>
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
                    <div className="space-y-3 rounded-[14px] border border-border/70 bg-background/35 p-3">
                      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                        Quick component controls
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs">Component</Label>
                        <Select
                          value={selectedComponentNode.componentId}
                          onValueChange={(componentId) => {
                            const nextManifest = getToolchainComponentManifest(componentId);
                            updateNode(selectedComponentNode.id, (node) =>
                              node.kind === "component"
                                ? {
                                    ...node,
                                    componentId,
                                    label: node.label ?? nextManifest?.title ?? componentId,
                                    config: buildDefaultConfig(nextManifest),
                                  }
                                : node
                            );
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {registry.map((entry) => (
                              <SelectItem key={entry.manifest.id} value={entry.manifest.id}>
                                {entry.manifest.title}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-xs">Tailwind Classes</Label>
                        <Input
                          value={selectedComponentNode.style?.className ?? ""}
                          placeholder="w-[85vw] md:w-[70vw] lg:w-[60vw]"
                          onChange={(event) =>
                            updateNode(selectedComponentNode.id, (node) => {
                              if (node.kind !== "component") return node;
                              const nextStyle: StyleSpec = { ...(node.style ?? {}) };
                              if (event.target.value.trim()) {
                                nextStyle.className = event.target.value;
                              } else {
                                delete nextStyle.className;
                              }
                              return {
                                ...node,
                                style: Object.keys(nextStyle).length ? nextStyle : undefined,
                              };
                            })
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="text-xs font-semibold text-muted-foreground">Available hooks</div>
                        {Object.keys(selectedComponentManifest.hooks ?? {}).length ? (
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(selectedComponentManifest.hooks ?? {}).map(([hookKey, hook]) => (
                              <Badge key={hookKey} variant="outline">
                                {hook.label ?? hookKey}
                              </Badge>
                            ))}
                          </div>
                        ) : (
                          <div className="rounded-sm border border-dashed border-border/60 p-2 text-xs text-muted-foreground">
                            No manifest hooks. Use the advanced drawer for raw JSON if needed.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-3 rounded-[14px] border border-border/70 bg-background/35 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                          Quick config fields
                        </div>
                        {Object.keys(selectedComponentManifest.config ?? {}).length > selectedComponentQuickFields.length ? (
                          <div className="text-[11px] text-muted-foreground">
                            Showing {selectedComponentQuickFields.length} of {Object.keys(selectedComponentManifest.config ?? {}).length}
                          </div>
                        ) : null}
                      </div>
                      {selectedComponentQuickFields.length ? (
                        <div className="grid gap-3 md:grid-cols-2">
                          {selectedComponentQuickFields.map(([key, field]) => (
                            <ConfigFieldEditor
                              key={`${selectedComponentNode.id}-${key}`}
                              fieldKey={key}
                              field={field}
                              value={selectedComponentNode.config?.[key] as JSONValue | undefined}
                              jsonDraft={componentQuickJsonDrafts[key]}
                              onJsonDraftChange={(draft) =>
                                setComponentQuickJsonDrafts((prev) => ({ ...prev, [key]: draft }))
                              }
                              onValueChange={(value) =>
                                updateNode(selectedComponentNode.id, (node) => {
                                  if (node.kind !== "component") return node;
                                  const nextConfig = { ...(node.config ?? {}) };
                                  if (value === undefined) {
                                    delete nextConfig[key];
                                  } else {
                                    nextConfig[key] = value;
                                  }
                                  return {
                                    ...node,
                                    config: Object.keys(nextConfig).length ? nextConfig : {},
                                  };
                                })
                              }
                            />
                          ))}
                        </div>
                      ) : (
                        <div className="rounded-sm border border-dashed border-border/60 p-3 text-xs text-muted-foreground">
                          No quick config fields on this manifest. Use the advanced drawer if you need raw JSON or hook mapping controls.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}
              <ToolchainUISpecRendererV2
                spec={spec}
                renderComponent={renderPreviewComponent}
                selectedNodeId={selectedId ?? undefined}
                onSelectNode={setSelectedId}
                showNodeFrames
                showInlineControls
                enableNodeReorderDnD
                draggingNodeId={draggingNodeId}
                onNodeDragStart={setDraggingNodeId}
                onNodeDragEnd={() => setDraggingNodeId(null)}
                onNodeDropRelative={(sourceNodeId, targetNodeId, placement) => {
                  reorderNodeRelative(sourceNodeId, targetNodeId, placement);
                }}
                onNodeDropInside={(sourceNodeId, targetNodeId) => {
                  moveNodeIntoLayout(sourceNodeId, targetNodeId);
                }}
                onInsertRelative={(targetNodeId, placement) =>
                  insertSiblingRelative(targetNodeId, placement)
                }
                onWrapNode={wrapNodeInLayout}
                onAddLayoutChild={(targetNodeId, kind) =>
                  addChildToNode(targetNodeId, createLayoutChild(kind))
                }
                onDeleteNode={(nodeId) => deleteNodeById(nodeId)}
              />
            </div>
          </div>
        </div>

        <div
          className={cn(
            "ql-editor-panel p-3 transition-all duration-200",
            hasPreviewSelection ? "opacity-65 saturate-[0.82] lg:scale-[0.995]" : undefined
          )}
        >
          <div className="space-y-1">
            <div className="text-sm font-semibold">Selection inspector</div>
            <div className="ql-editor-caption">
              Fine-tune structure, style, and component config after selecting in the preview.
            </div>
          </div>
          {selectedNode ? (
            <div className="mt-3 space-y-4">
              <div className="space-y-2">
                <Label className="text-xs">Node id</Label>
                <Input value={selectedNode.id} disabled />
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Label</Label>
                <Input
                  value={selectedNode.label ?? ""}
                  onChange={(event) =>
                    updateNode(selectedNode.id, (node) => ({
                      ...node,
                      label: event.target.value || undefined,
                    }))
                  }
                  placeholder="Optional label"
                />
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Structure</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => moveSelectedInParent(-1)}
                    disabled={!canMoveSelectedUp}
                  >
                    Move up
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => moveSelectedInParent(1)}
                    disabled={!canMoveSelectedDown}
                  >
                    Move down
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="col-span-2"
                    onClick={duplicateSelectedNode}
                    disabled={!canDuplicateSelected}
                  >
                    Duplicate subtree
                  </Button>
                </div>
              </div>

              {isLayoutNode(selectedNode) && selectedNode.type === "text" ? (
                <div className="space-y-2">
                  <Label className="text-xs">Text</Label>
                  <Textarea
                    value={selectedNode.text}
                    onChange={(event) =>
                      updateNode(selectedNode.id, (node) =>
                        isLayoutNode(node) && node.type === "text"
                          ? { ...node, text: event.target.value }
                          : node
                      )
                    }
                    rows={4}
                  />
                </div>
              ) : null}

              {isLayoutNode(selectedNode) &&
              (selectedNode.type === "stack" || selectedNode.type === "split") ? (
                <div className="space-y-2">
                  <Label className="text-xs">Direction</Label>
                  <Select
                    value={selectedNode.direction}
                    onValueChange={(value) =>
                      updateNode(selectedNode.id, (node) => {
                        if (!isLayoutNode(node)) return node;
                        if (node.type === "stack" || node.type === "split") {
                          return {
                            ...node,
                            direction: value as "horizontal" | "vertical",
                          };
                        }
                        return node;
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="horizontal">horizontal</SelectItem>
                      <SelectItem value="vertical">vertical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              ) : null}

              <Separator />

              <div className="space-y-2">
                <div className="text-xs font-semibold text-muted-foreground">Style</div>
                {STYLE_SELECT_KEYS.map((key) => (
                  <div key={key} className="space-y-1">
                    <Label className="text-xs">{key}</Label>
                    <Select
                      value={
                        selectedNode.style?.[key] !== undefined
                          ? String(selectedNode.style[key])
                          : UNSET_SELECT_VALUE
                      }
                      onValueChange={(value) => setStyleValue(key, value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="(unset)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={UNSET_SELECT_VALUE}>(unset)</SelectItem>
                        {STYLE_OPTIONS[key].map((value) => (
                          <SelectItem key={value} value={value}>
                            {value}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ))}
                <div className="space-y-1">
                  <Label className="text-xs">className</Label>
                  <Input
                    value={selectedNode.style?.className ?? ""}
                    onChange={(event) =>
                      updateNode(selectedNode.id, (node) => {
                        const nextStyle: StyleSpec = { ...(node.style ?? {}) };
                        if (event.target.value) {
                          nextStyle.className = event.target.value;
                        } else {
                          delete nextStyle.className;
                        }
                        return {
                          ...node,
                          style: Object.keys(nextStyle).length ? nextStyle : undefined,
                        };
                      })
                    }
                    placeholder="Advanced (optional)"
                  />
                </div>
              </div>

              {isLayoutNode(selectedNode) ? (
                <>
                  <Separator />
                  <div className="space-y-3">
                    <div className="text-xs font-semibold text-muted-foreground">
                      Add child
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {(["stack", "box", "split", "scroll", "text", "divider"] as const).map(
                        (kind) => (
                          <Button
                            key={kind}
                            type="button"
                            variant="outline"
                            onClick={() => addChildToSelected(createLayoutChild(kind))}
                            disabled={
                              selectedNode.type === "divider" ||
                              selectedNode.type === "text"
                            }
                          >
                            {kind[0].toUpperCase() + kind.slice(1)}
                          </Button>
                        )
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label className="text-xs">Component</Label>
                      <Select
                        onValueChange={(componentId) => {
                          const manifest = getToolchainComponentManifest(componentId);
                          const id = makeId("cmp");
                          addChildToSelected({
                            id,
                            kind: "component",
                            componentId,
                            label: manifest?.title ?? componentId,
                            config: buildDefaultConfig(manifest),
                          });
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Add component..." />
                        </SelectTrigger>
                        <SelectContent>
                          {registry.map((entry) => (
                            <SelectItem key={entry.manifest.id} value={entry.manifest.id}>
                              {entry.manifest.title}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </>
              ) : null}

              {isComponentNode(selectedNode) ? (
                <>
                  <Separator />
                  <ComponentInspector
                    node={selectedNode}
                    registry={registry}
                    drawerOpenRequestNonce={componentDrawerRequestNonce}
                    onUpdate={(updater) =>
                      updateNode(selectedNode.id, (node) =>
                        isComponentNode(node) ? updater(node) : node
                      )
                    }
                  />
                </>
              ) : null}
            </div>
          ) : (
            <div className="mt-3 text-sm text-muted-foreground">
              Select a node in the tree or preview to edit it.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ComponentInspector({
  node,
  onUpdate,
  registry,
  drawerOpenRequestNonce,
}: {
  node: ComponentNode;
  onUpdate: (updater: (prev: ComponentNode) => ComponentNode) => void;
  registry: ToolchainComponentRegistryEntry[];
  drawerOpenRequestNonce?: number;
}) {
  const manifest = getToolchainComponentManifest(node.componentId);
  const configSchema = manifest?.config ?? {};
  const [jsonDrafts, setJsonDrafts] = useState<Record<string, string>>({});
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [tailwindDraft, setTailwindDraft] = useState("");
  const [hookDrafts, setHookDrafts] = useState<ComponentHookDraft[]>([]);
  const [rawDraft, setRawDraft] = useState("");

  useEffect(() => {
    setJsonDrafts({});
    setTailwindDraft(node.style?.className ?? "");
    setHookDrafts((node.hooks ?? []).map((hook, index) => hookBindingToDraft(hook, makeId(`hook_${index + 1}`))));
    setRawDraft(
      JSON.stringify(
        {
          config: node.config ?? {},
          hooks: node.hooks ?? [],
          style: node.style ?? {},
        },
        null,
        2
      )
    );
    // Reset drafts when selection changes; preserve local edits while configuring one node.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node.id]);

  useEffect(() => {
    if (!drawerOpenRequestNonce) return;
    setDrawerOpen(true);
  }, [drawerOpenRequestNonce]);

  const setConfigValue = (key: string, value: JSONValue | undefined) => {
    onUpdate((prev) => {
      const nextConfig = { ...(prev.config ?? {}) };
      if (value === undefined) {
        delete nextConfig[key];
      } else {
        nextConfig[key] = value;
      }
      return { ...prev, config: nextConfig };
    });
  };

  const componentOptions = registry.map((entry) => entry.manifest);
  const availableHookNames = Array.from(
    new Set([
      ...Object.keys(manifest?.hooks ?? {}),
      ...(node.hooks ?? []).map((hook) => hook.hook),
      ...(node.componentId === "chat-input"
        ? ["on_submit", "selected_collections", "on_upload"]
        : []),
    ])
  );

  const addHookDraft = (hookName?: string) => {
    setHookDrafts((prev) => [
      ...prev,
      {
        id: makeId("hook"),
        hook: hookName ?? availableHookNames[0] ?? "submit",
        fireIndex: 1,
        targetEvent: "",
        targetRoute: "value",
        payloadPath: "/",
        store: false,
      },
    ]);
  };

  const updateHookDraft = (
    draftId: string,
    updater: (prev: ComponentHookDraft) => ComponentHookDraft
  ) => {
    setHookDrafts((prev) =>
      prev.map((draft) => (draft.id === draftId ? updater(draft) : draft))
    );
  };

  const removeHookDraft = (draftId: string) => {
    setHookDrafts((prev) => prev.filter((draft) => draft.id !== draftId));
  };

  const saveDrawerChanges = () => {
    const nextHooks = hookDrafts
      .map((draft) => hookDraftToBinding(draft))
      .filter((hook): hook is HookBindingSpec => hook !== null);

    onUpdate((prev) => {
      const nextStyle: StyleSpec = { ...(prev.style ?? {}) };
      if (tailwindDraft.trim()) {
        nextStyle.className = tailwindDraft.trim();
      } else {
        delete nextStyle.className;
      }

      return {
        ...prev,
        style: Object.keys(nextStyle).length ? nextStyle : undefined,
        hooks: nextHooks.length ? nextHooks : undefined,
      };
    });
    setDrawerOpen(false);
    toast.success("Updated component configuration.");
  };

  const applyRawJson = () => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(rawDraft);
    } catch {
      toast.error("Raw JSON is invalid.");
      return;
    }
    if (!isObjectRecord(parsed)) {
      toast.error("Raw JSON must be an object.");
      return;
    }
    const parsedRecord = parsed as Record<string, unknown>;

    onUpdate((prev) => {
      const next: ComponentNode = { ...prev };

      if ("config" in parsedRecord) {
        next.config = isObjectRecord(parsedRecord.config)
          ? (parsedRecord.config as Record<string, JSONValue>)
          : undefined;
      }
      if ("style" in parsedRecord) {
        next.style = isObjectRecord(parsedRecord.style)
          ? (parsedRecord.style as StyleSpec)
          : undefined;
      }
      if ("hooks" in parsedRecord) {
        next.hooks = Array.isArray(parsedRecord.hooks)
          ? (parsedRecord.hooks as HookBindingSpec[])
          : undefined;
      }

      return next;
    });

    if (isObjectRecord(parsedRecord.style)) {
      setTailwindDraft(
        typeof parsedRecord.style.className === "string" ? parsedRecord.style.className : ""
      );
    }
    if (Array.isArray(parsedRecord.hooks)) {
      setHookDrafts(
        (parsedRecord.hooks as HookBindingSpec[]).map((hook, index) =>
          hookBindingToDraft(hook, makeId(`hook_${index + 1}`))
        )
      );
    }

    toast.success("Applied raw JSON to component.");
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label className="text-xs">Component</Label>
        <Select
          value={node.componentId}
          onValueChange={(componentId) => {
            const nextManifest = getToolchainComponentManifest(componentId);
            onUpdate((prev) => ({
              ...prev,
              componentId,
              label: prev.label ?? nextManifest?.title ?? componentId,
              config: buildDefaultConfig(nextManifest),
            }));
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {componentOptions.map((option) => (
              <SelectItem key={option.id} value={option.id}>
                {option.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {manifest?.description ? (
        <div className="text-xs text-muted-foreground">{manifest.description}</div>
      ) : null}

      <div className="flex items-center justify-between rounded-sm border border-border/70 bg-muted/10 p-2">
        <div className="text-xs text-muted-foreground">
          Configure event hooks and raw JSON in drawer mode.
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => setDrawerOpen(true)}>
          Configure component
        </Button>
      </div>

      <div className="space-y-2">
        <div className="text-xs font-semibold text-muted-foreground">Config</div>
        {Object.entries(configSchema).length === 0 ? (
          <div className="rounded-sm border border-dashed border-border p-2 text-xs text-muted-foreground">
            No manifest config fields.
          </div>
        ) : (
          Object.entries(configSchema).map(([key, field]) => (
            <ConfigFieldEditor
              key={key}
              fieldKey={key}
              field={field}
              value={node.config?.[key] as JSONValue | undefined}
              jsonDraft={jsonDrafts[key]}
              onJsonDraftChange={(draft) =>
                setJsonDrafts((prev) => ({ ...prev, [key]: draft }))
              }
              onValueChange={(value) => setConfigValue(key, value)}
            />
          ))
        )}
      </div>

      <div className="space-y-2">
        <div className="text-xs font-semibold text-muted-foreground">Bindings</div>
        {Object.keys(manifest?.bindings ?? {}).length ? (
          <div className="flex flex-wrap gap-1">
            {Object.entries(manifest?.bindings ?? {}).map(([bindingKey, binding]) => (
              <Badge key={bindingKey} variant="outline">
                {binding.label} ({binding.kind})
              </Badge>
            ))}
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">No manifest bindings.</div>
        )}
      </div>

      <div className="space-y-2">
        <div className="text-xs font-semibold text-muted-foreground">Hooks</div>
        {Object.keys(manifest?.hooks ?? {}).length ? (
          <div className="flex flex-wrap gap-1">
            {Object.entries(manifest?.hooks ?? {}).map(([hookKey, hook]) => (
              <Badge key={hookKey} variant="outline">
                {hook.label ?? hookKey}
              </Badge>
            ))}
          </div>
        ) : (
          <div className="text-xs text-muted-foreground">No manifest hooks.</div>
        )}
      </div>

      <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
        <SheetContent side="right" className="w-[720px] max-w-[calc(100vw-2rem)] p-0 sm:max-w-[720px]">
          <div className="flex h-full flex-col">
            <SheetHeader className="border-b border-border/70 px-6 py-4 pr-14">
              <SheetTitle>Configure &quot;{node.componentId}&quot; Component</SheetTitle>
              <SheetDescription>
                Configure component styling, event hooks, and raw JSON configuration.
              </SheetDescription>
            </SheetHeader>

            <ScrollArea className="flex-1">
              <div className="space-y-5 px-6 py-5">
                <div className="space-y-2 rounded-sm border border-border/70 p-3">
                  <div className="text-sm font-semibold">Component Styling</div>
                  <Label className="text-xs">Tailwind Classes</Label>
                  <Input
                    value={tailwindDraft}
                    onChange={(event) => setTailwindDraft(event.target.value)}
                    placeholder="w-[85vw] md:w-[70vw] lg:w-[60vw]"
                  />
                </div>

                <div className="space-y-3 rounded-sm border border-border/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold">Event Hooks</div>
                    <Button type="button" size="sm" variant="outline" onClick={() => addHookDraft()}>
                      Add hook
                    </Button>
                  </div>

                  {availableHookNames.length ? (
                    <div className="flex flex-wrap gap-1">
                      {availableHookNames.map((hookName) => (
                        <Button
                          key={hookName}
                          type="button"
                          variant="outline"
                          size="sm"
                          className="h-6 px-2 text-[11px]"
                          onClick={() => addHookDraft(hookName)}
                        >
                          {hookName}
                        </Button>
                      ))}
                    </div>
                  ) : null}

                  {hookDrafts.length ? (
                    <div className="space-y-3">
                      {hookDrafts.map((draft) => (
                        <div key={draft.id} className="space-y-2 rounded-sm border border-border/60 bg-muted/10 p-2">
                          <div className="flex items-center justify-between gap-2">
                            <div className="text-xs font-semibold">
                              {draft.hook || "New hook"}
                            </div>
                            <Button
                              type="button"
                              variant="outline"
                              size="sm"
                              className="h-7 px-2"
                              onClick={() => removeHookDraft(draft.id)}
                            >
                              Remove
                            </Button>
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-1">
                              <Label className="text-[11px]">Hook key</Label>
                              <Input
                                value={draft.hook}
                                onChange={(event) =>
                                  updateHookDraft(draft.id, (prev) => ({
                                    ...prev,
                                    hook: event.target.value,
                                  }))
                                }
                                placeholder="on_submit"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-[11px]">Fire index</Label>
                              <Input
                                type="number"
                                min={1}
                                value={String(draft.fireIndex)}
                                onChange={(event) =>
                                  updateHookDraft(draft.id, (prev) => ({
                                    ...prev,
                                    fireIndex: Math.max(1, Number(event.target.value) || 1),
                                  }))
                                }
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-[11px]">Target event</Label>
                              <Input
                                value={draft.targetEvent}
                                onChange={(event) =>
                                  updateHookDraft(draft.id, (prev) => ({
                                    ...prev,
                                    targetEvent: event.target.value,
                                  }))
                                }
                                placeholder="user_question_event"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-[11px]">Target route</Label>
                              <Input
                                value={draft.targetRoute}
                                onChange={(event) =>
                                  updateHookDraft(draft.id, (prev) => ({
                                    ...prev,
                                    targetRoute: event.target.value,
                                  }))
                                }
                                placeholder="question"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-[11px]">Payload path</Label>
                              <Input
                                value={draft.payloadPath}
                                onChange={(event) =>
                                  updateHookDraft(draft.id, (prev) => ({
                                    ...prev,
                                    payloadPath: event.target.value,
                                  }))
                                }
                                placeholder="/"
                              />
                            </div>
                            <div className="space-y-1">
                              <Label className="text-[11px]">Store</Label>
                              <div className="flex min-h-8 items-center rounded-sm border border-border/60 px-2 py-1.5">
                                <Checkbox
                                  checked={draft.store}
                                  onCheckedChange={(checked) =>
                                    updateHookDraft(draft.id, (prev) => ({
                                      ...prev,
                                      store: checked === true,
                                    }))
                                  }
                                />
                                <span className="ml-2 text-xs text-muted-foreground">
                                  Persist/await action
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-sm border border-dashed border-border/60 p-3 text-xs text-muted-foreground">
                      No hook mappings configured yet.
                    </div>
                  )}
                </div>

                <div className="space-y-2 rounded-sm border border-border/70 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-sm font-semibold">Raw JSON Preview</div>
                    <Button type="button" variant="outline" size="sm" onClick={applyRawJson}>
                      Apply JSON
                    </Button>
                  </div>
                  <Textarea
                    rows={12}
                    value={rawDraft}
                    onChange={(event) => setRawDraft(event.target.value)}
                    className="font-mono text-xs"
                  />
                </div>
              </div>
            </ScrollArea>

            <div className="border-t border-border/70 px-4 py-3">
              <Button type="button" className="w-full" onClick={saveDrawerChanges}>
                Save Changes
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}

function ConfigFieldEditor({
  fieldKey,
  field,
  value,
  onValueChange,
  jsonDraft,
  onJsonDraftChange,
}: {
  fieldKey: string;
  field: FieldSchema;
  value: JSONValue | undefined;
  onValueChange: (value: JSONValue | undefined) => void;
  jsonDraft?: string;
  onJsonDraftChange: (value: string) => void;
}) {
  const currentValue = value ?? (field.default as JSONValue | undefined);

  return (
    <div className="space-y-1">
      <Label className="text-xs">{fieldKey}</Label>
      {field.type === "string" ? (
        field.multiline ? (
          <Textarea
            rows={3}
            value={typeof currentValue === "string" ? currentValue : ""}
            placeholder={field.placeholder}
            onChange={(event) => onValueChange(event.target.value)}
          />
        ) : (
          <Input
            value={typeof currentValue === "string" ? currentValue : ""}
            placeholder={field.placeholder}
            onChange={(event) => onValueChange(event.target.value)}
          />
        )
      ) : null}

      {field.type === "number" ? (
        <Input
          type="number"
          value={typeof currentValue === "number" ? String(currentValue) : ""}
          min={field.min}
          max={field.max}
          step={field.step}
          onChange={(event) => {
            if (!event.target.value) {
              onValueChange(undefined);
              return;
            }
            const parsed = Number(event.target.value);
            if (Number.isFinite(parsed)) {
              onValueChange(parsed);
            }
          }}
        />
      ) : null}

      {field.type === "boolean" ? (
        <Select
          value={
            typeof currentValue === "boolean"
              ? String(currentValue)
              : UNSET_SELECT_VALUE
          }
          onValueChange={(selected) => {
            if (selected === UNSET_SELECT_VALUE) {
              onValueChange(undefined);
              return;
            }
            onValueChange(selected === "true");
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={UNSET_SELECT_VALUE}>(unset)</SelectItem>
            <SelectItem value="true">true</SelectItem>
            <SelectItem value="false">false</SelectItem>
          </SelectContent>
        </Select>
      ) : null}

      {field.type === "enum" ? (
        <Select
          value={
            typeof currentValue === "string" ? currentValue : UNSET_SELECT_VALUE
          }
          onValueChange={(selected) => {
            if (selected === UNSET_SELECT_VALUE) {
              onValueChange(undefined);
              return;
            }
            onValueChange(selected);
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={UNSET_SELECT_VALUE}>(unset)</SelectItem>
            {field.options.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : null}

      {field.type === "json" ? (
        <Textarea
          rows={5}
          value={
            jsonDraft ??
            JSON.stringify(currentValue ?? field.default ?? {}, null, 2)
          }
          onChange={(event) => onJsonDraftChange(event.target.value)}
          onBlur={(event) => {
            try {
              const parsed = JSON.parse(event.target.value) as JSONValue;
              onValueChange(parsed);
            } catch {
              toast.error(`Invalid JSON for "${fieldKey}"`);
            }
          }}
        />
      ) : null}
    </div>
  );
}
