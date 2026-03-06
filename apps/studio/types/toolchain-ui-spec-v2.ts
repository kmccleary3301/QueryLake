export type JSONPrimitive = string | number | boolean | null;
export type JSONValue =
  | JSONPrimitive
  | { [key: string]: JSONValue }
  | Array<JSONValue>;

export type NodeId = string;
export type ComponentId = string;

// Canonical selector format (recommended): JSON Pointer (RFC 6901).
// We keep it as string for ergonomics; validate separately.
export type JSONPointer = string;

export type ToolchainUISpecV2 = {
  version: 2;
  root: NodeId;
  nodes: Record<NodeId, UINode>;
  meta?: {
    name?: string;
    updatedAt?: number;
    updatedBy?: string;
    editor?: {
      viewport?: { x: number; y: number; zoom: number };
      selectedNodeId?: NodeId;
    };
  };
};

export type UINode = LayoutNode | ComponentNode;

export type LayoutNode =
  | SplitNode
  | StackNode
  | BoxNode
  | ScrollNode
  | DividerNode
  | TextNode;

export type ComponentNode = {
  id: NodeId;
  kind: "component";
  componentId: ComponentId;
  label?: string;
  config?: Record<string, JSONValue>;
  bindings?: Record<string, BindingSpec>;
  hooks?: HookBindingSpec[];
  style?: StyleSpec;
  permissions?: {
    view?: string[];
    edit?: string[];
  };
};

export type SplitNode = {
  id: NodeId;
  kind: "layout";
  type: "split";
  direction: "horizontal" | "vertical";
  children: NodeId[];
  sizes?: number[];
  resizable?: boolean;
  header?: NodeId;
  footer?: NodeId;
  style?: StyleSpec;
  label?: string;
};

export type StackNode = {
  id: NodeId;
  kind: "layout";
  type: "stack";
  direction: "horizontal" | "vertical";
  children: NodeId[];
  style?: StyleSpec;
  label?: string;
};

export type BoxNode = {
  id: NodeId;
  kind: "layout";
  type: "box";
  children: NodeId[];
  header?: NodeId;
  footer?: NodeId;
  style?: StyleSpec;
  label?: string;
};

export type ScrollNode = {
  id: NodeId;
  kind: "layout";
  type: "scroll";
  children: NodeId[];
  style?: StyleSpec;
  label?: string;
};

export type DividerNode = {
  id: NodeId;
  kind: "layout";
  type: "divider";
  style?: StyleSpec;
  label?: string;
};

export type TextNode = {
  id: NodeId;
  kind: "layout";
  type: "text";
  text: string;
  style?: StyleSpec;
  label?: string;
};

export type BindingSpec =
  | { kind: "state"; path: JSONPointer; fallback?: JSONValue }
  | { kind: "session"; key: "id" | "rev" | "toolchainId" | "title" }
  | { kind: "ui"; path: JSONPointer; fallback?: JSONValue }
  | { kind: "pref"; key: string; fallback?: JSONValue }
  | { kind: "literal"; value: JSONValue }
  | { kind: "payload"; path: JSONPointer }
  | {
      kind: "computed";
      op: "length" | "toString" | "join";
      args: BindingSpec[];
    };

export type HookBindingSpec = {
  hook: string;
  fires: HookFireSpec[];
};

export type HookFireSpec = {
  index: number;
  actions: ActionSpec[];
};

export type ActionSpec =
  | {
      type: "emitEvent";
      nodeId: string;
      inputs: Record<string, BindingSpec>;
      await?: boolean;
      idempotencyKey?: string;
    }
  | {
      type: "toast";
      variant?: "success" | "error" | "info";
      message: string;
    }
  | {
      type: "navigate";
      to: string;
      newTab?: boolean;
    }
  | {
      type: "openModal";
      modalId: string;
    }
  | {
      type: "setUI";
      path: JSONPointer;
      value: BindingSpec;
    }
  | {
      type: "setPref";
      key: string;
      value: BindingSpec;
    };

export type StyleSpec = {
  padding?: "none" | "xs" | "sm" | "md" | "lg";
  gap?: "none" | "xs" | "sm" | "md" | "lg";
  alignX?: "start" | "center" | "end" | "stretch" | "between";
  alignY?: "start" | "center" | "end" | "stretch";
  width?: "auto" | "full" | "sm" | "md" | "lg" | "xl";
  height?: "auto" | "full";
  overflow?: "visible" | "hidden" | "auto";
  surface?: "none" | "panel" | "muted" | "inset";
  border?: "none" | "hairline";
  radius?: "none" | "sm" | "md";
  className?: string;
};
