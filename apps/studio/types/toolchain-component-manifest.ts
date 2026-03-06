export type ComponentId = string;

export type FieldSchema =
  | {
      type: "string";
      default?: string;
      multiline?: boolean;
      placeholder?: string;
    }
  | {
      type: "number";
      default?: number;
      min?: number;
      max?: number;
      step?: number;
    }
  | {
      type: "boolean";
      default?: boolean;
    }
  | {
      type: "enum";
      options: Array<{ label: string; value: string }>;
      default?: string;
    }
  | {
      type: "json";
      default?: unknown;
    };

export type ToolchainComponentManifest = {
  id: ComponentId;
  kind: "display" | "input";
  title: string;
  category: string;
  description?: string;
  icon?: string;
  config?: Record<string, FieldSchema>;
  bindings?: Record<
    string,
    {
      label: string;
      kind: "state" | "session";
      schema?: unknown;
      required?: boolean;
    }
  >;
  hooks?: Record<
    string,
    {
      label?: string;
      payloadSchema?: unknown;
    }
  >;
  preview?: {
    demoState?: unknown;
    minWidth?: number;
    minHeight?: number;
  };
  version?: string;
};

