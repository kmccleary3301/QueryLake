import type {
  ActionSpec,
  BindingSpec,
  HookBindingSpec,
} from "@/types/toolchain-ui-spec-v2";

export type ToolchainUIRuntimeContext = {
  state: unknown;
  session: {
    id?: string;
    rev?: string;
    toolchainId?: string;
    title?: string;
  };
  ui: unknown;
  prefs: Record<string, unknown>;
  actions: {
    emitEvent: (
      nodeId: string,
      inputs: Record<string, unknown>,
      opts?: { await?: boolean; idempotencyKey?: string }
    ) => Promise<unknown>;
    toast?: (message: string, variant?: "success" | "error" | "info") => void;
    navigate?: (to: string, newTab?: boolean) => void;
    openModal?: (modalId: string) => Promise<unknown> | void;
    setUI?: (path: string, value: unknown) => void;
    setPref?: (key: string, value: unknown) => void;
  };
};

export function resolveJsonPointer(root: unknown, pointer: string): unknown {
  if (pointer === "" || pointer === "/") return root;
  if (!pointer.startsWith("/")) return undefined;
  const parts = pointer
    .slice(1)
    .split("/")
    .map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));

  let current: unknown = root;
  for (const part of parts) {
    if (current === null || current === undefined) return undefined;
    if (Array.isArray(current)) {
      const index = Number(part);
      if (!Number.isInteger(index) || index < 0 || index >= current.length) {
        return undefined;
      }
      current = current[index];
      continue;
    }
    if (typeof current === "object") {
      current = (current as Record<string, unknown>)[part];
      continue;
    }
    return undefined;
  }
  return current;
}

export function resolveBinding(
  binding: BindingSpec,
  ctx: ToolchainUIRuntimeContext,
  payload?: unknown
): unknown {
  switch (binding.kind) {
    case "state": {
      const value = resolveJsonPointer(ctx.state, binding.path);
      return value === undefined ? binding.fallback : value;
    }
    case "session":
      return ctx.session[binding.key];
    case "ui": {
      const value = resolveJsonPointer(ctx.ui, binding.path);
      return value === undefined ? binding.fallback : value;
    }
    case "pref": {
      const value = ctx.prefs[binding.key];
      return value === undefined ? binding.fallback : value;
    }
    case "literal":
      return binding.value;
    case "payload":
      return resolveJsonPointer(payload, binding.path);
    case "computed": {
      const resolved = binding.args.map((arg) => resolveBinding(arg, ctx, payload));
      switch (binding.op) {
        case "length": {
          const value = resolved[0];
          if (typeof value === "string" || Array.isArray(value)) {
            return value.length;
          }
          return 0;
        }
        case "toString":
          return resolved[0] === undefined || resolved[0] === null
            ? ""
            : String(resolved[0]);
        case "join":
          return Array.isArray(resolved[0]) ? (resolved[0] as unknown[]).join("") : "";
        default: {
          const exhaustive: never = binding.op;
          return exhaustive;
        }
      }
    }
    default: {
      const exhaustive: never = binding;
      return exhaustive;
    }
  }
}

export function resolveBindingRecord(
  record: Record<string, BindingSpec>,
  ctx: ToolchainUIRuntimeContext,
  payload?: unknown
): Record<string, unknown> {
  const resolved: Record<string, unknown> = {};
  for (const [key, binding] of Object.entries(record)) {
    resolved[key] = resolveBinding(binding, ctx, payload);
  }
  return resolved;
}

export async function runAction(
  action: ActionSpec,
  ctx: ToolchainUIRuntimeContext,
  payload?: unknown
): Promise<void> {
  switch (action.type) {
    case "emitEvent": {
      const inputs = resolveBindingRecord(action.inputs, ctx, payload);
      await ctx.actions.emitEvent(action.nodeId, inputs, {
        await: action.await,
        idempotencyKey: action.idempotencyKey,
      });
      return;
    }
    case "toast":
      ctx.actions.toast?.(action.message, action.variant);
      return;
    case "navigate":
      ctx.actions.navigate?.(action.to, action.newTab);
      return;
    case "openModal":
      await ctx.actions.openModal?.(action.modalId);
      return;
    case "setUI": {
      const value = resolveBinding(action.value, ctx, payload);
      ctx.actions.setUI?.(action.path, value);
      return;
    }
    case "setPref": {
      const value = resolveBinding(action.value, ctx, payload);
      ctx.actions.setPref?.(action.key, value);
      return;
    }
    default: {
      const exhaustive: never = action;
      void exhaustive;
    }
  }
}

export async function runActions(
  actions: ActionSpec[],
  ctx: ToolchainUIRuntimeContext,
  payload?: unknown
): Promise<void> {
  for (const action of actions) {
    await runAction(action, ctx, payload);
  }
}

export async function runHook(
  hooks: HookBindingSpec[] | undefined,
  hookName: string,
  ctx: ToolchainUIRuntimeContext,
  payload?: unknown
): Promise<void> {
  if (!hooks?.length) return;
  const matching = hooks.filter((hook) => hook.hook === hookName);
  if (!matching.length) return;
  const fires = matching
    .flatMap((hook) => hook.fires)
    .sort((a, b) => a.index - b.index);
  for (const fire of fires) {
    await runActions(fire.actions, ctx, payload);
  }
}
