import { z } from "zod";

import type {
  BindingSpec,
  JSONValue,
  ToolchainUISpecV2,
  UINode,
} from "@/types/toolchain-ui-spec-v2";

const zJsonPrimitive = z.union([z.string(), z.number(), z.boolean(), z.null()]);
const zJsonValue: z.ZodType<JSONValue> = z.lazy(
  () =>
    z.union([
      zJsonPrimitive,
      z.array(zJsonValue),
      z.record(zJsonValue),
    ]) as z.ZodType<JSONValue>
);

export const zStyleSpec = z
  .object({
    padding: z.enum(["none", "xs", "sm", "md", "lg"]).optional(),
    gap: z.enum(["none", "xs", "sm", "md", "lg"]).optional(),
    alignX: z.enum(["start", "center", "end", "stretch", "between"]).optional(),
    alignY: z.enum(["start", "center", "end", "stretch"]).optional(),
    width: z.enum(["auto", "full", "sm", "md", "lg", "xl"]).optional(),
    height: z.enum(["auto", "full"]).optional(),
    overflow: z.enum(["visible", "hidden", "auto"]).optional(),
    surface: z.enum(["none", "panel", "muted", "inset"]).optional(),
    border: z.enum(["none", "hairline"]).optional(),
    radius: z.enum(["none", "sm", "md"]).optional(),
    className: z.string().optional(),
  })
  .strict();

const zBindingSpec: z.ZodType<BindingSpec> = z.lazy(() =>
  z.discriminatedUnion("kind", [
    z
      .object({
        kind: z.literal("state"),
        path: z.string(),
        fallback: zJsonValue.optional(),
      })
      .strict(),
    z
      .object({
        kind: z.literal("session"),
        key: z.enum(["id", "rev", "toolchainId", "title"]),
      })
      .strict(),
    z
      .object({
        kind: z.literal("ui"),
        path: z.string(),
        fallback: zJsonValue.optional(),
      })
      .strict(),
    z
      .object({
        kind: z.literal("pref"),
        key: z.string(),
        fallback: zJsonValue.optional(),
      })
      .strict(),
    z
      .object({
        kind: z.literal("literal"),
        value: zJsonValue,
      })
      .strict(),
    z
      .object({
        kind: z.literal("payload"),
        path: z.string(),
      })
      .strict(),
    z
      .object({
        kind: z.literal("computed"),
        op: z.enum(["length", "toString", "join"]),
        args: z.array(zBindingSpec),
      })
      .strict(),
  ])
);

const zActionSpec = z.discriminatedUnion("type", [
  z
    .object({
      type: z.literal("emitEvent"),
      nodeId: z.string(),
      inputs: z.record(zBindingSpec),
      await: z.boolean().optional(),
      idempotencyKey: z.string().optional(),
    })
    .strict(),
  z
    .object({
      type: z.literal("toast"),
      variant: z.enum(["success", "error", "info"]).optional(),
      message: z.string(),
    })
    .strict(),
  z
    .object({
      type: z.literal("navigate"),
      to: z.string(),
      newTab: z.boolean().optional(),
    })
    .strict(),
  z
    .object({
      type: z.literal("openModal"),
      modalId: z.string(),
    })
    .strict(),
  z
    .object({
      type: z.literal("setUI"),
      path: z.string(),
      value: zBindingSpec,
    })
    .strict(),
  z
    .object({
      type: z.literal("setPref"),
      key: z.string(),
      value: zBindingSpec,
    })
    .strict(),
]);

const zHookBindingSpec = z
  .object({
    hook: z.string(),
    fires: z.array(
      z
        .object({
          index: z.number().int().positive(),
          actions: z.array(zActionSpec),
        })
        .strict()
    ),
  })
  .strict();

const zSplitNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("split"),
    direction: z.enum(["horizontal", "vertical"]),
    children: z.array(z.string()),
    sizes: z.array(z.number()).optional(),
    resizable: z.boolean().optional(),
    header: z.string().optional(),
    footer: z.string().optional(),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zStackNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("stack"),
    direction: z.enum(["horizontal", "vertical"]),
    children: z.array(z.string()),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zBoxNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("box"),
    children: z.array(z.string()),
    header: z.string().optional(),
    footer: z.string().optional(),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zScrollNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("scroll"),
    children: z.array(z.string()),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zDividerNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("divider"),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zTextNode = z
  .object({
    id: z.string(),
    kind: z.literal("layout"),
    type: z.literal("text"),
    text: z.string(),
    style: zStyleSpec.optional(),
    label: z.string().optional(),
  })
  .strict();

const zLayoutNode = z.union([
  zSplitNode,
  zStackNode,
  zBoxNode,
  zScrollNode,
  zDividerNode,
  zTextNode,
]);

const zComponentNode = z
  .object({
    id: z.string(),
    kind: z.literal("component"),
    componentId: z.string(),
    label: z.string().optional(),
    config: z.record(zJsonValue).optional(),
    bindings: z.record(zBindingSpec).optional(),
    hooks: z.array(zHookBindingSpec).optional(),
    style: zStyleSpec.optional(),
    permissions: z
      .object({
        view: z.array(z.string()).optional(),
        edit: z.array(z.string()).optional(),
      })
      .strict()
      .optional(),
  })
  .strict();

const zUINode: z.ZodType<UINode> = z.union([zLayoutNode, zComponentNode]);

export const zToolchainUISpecV2: z.ZodType<ToolchainUISpecV2> = z
  .object({
    version: z.literal(2),
    root: z.string(),
    nodes: z.record(zUINode),
    meta: z
      .object({
        name: z.string().optional(),
        updatedAt: z.number().int().optional(),
        updatedBy: z.string().optional(),
        editor: z
          .object({
            viewport: z
              .object({
                x: z.number(),
                y: z.number(),
                zoom: z.number(),
              })
              .strict()
              .optional(),
            selectedNodeId: z.string().optional(),
          })
          .strict()
          .optional(),
      })
      .strict()
      .optional(),
  })
  .strict()
  .superRefine((spec, ctx) => {
    const nodeIds = new Set(Object.keys(spec.nodes));

    if (!nodeIds.has(spec.root)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: `root '${spec.root}' is not present in nodes`,
        path: ["root"],
      });
    }

    for (const [key, node] of Object.entries(spec.nodes)) {
      if (node.id !== key) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: `node.id '${node.id}' does not match nodes['${key}'] key`,
          path: ["nodes", key, "id"],
        });
      }

      if (node.kind === "layout") {
        const references: Array<{ field: string; id: string }> = [];
        switch (node.type) {
          case "split":
          case "box":
            references.push(...node.children.map((id) => ({ field: "children", id })));
            if (node.header) references.push({ field: "header", id: node.header });
            if (node.footer) references.push({ field: "footer", id: node.footer });
            break;
          case "stack":
          case "scroll":
            references.push(...node.children.map((id) => ({ field: "children", id })));
            break;
          case "divider":
          case "text":
            break;
          default: {
            const exhaustive: never = node;
            void exhaustive;
          }
        }

        for (const ref of references) {
          if (!nodeIds.has(ref.id)) {
            ctx.addIssue({
              code: z.ZodIssueCode.custom,
              message: `unknown node reference '${ref.id}'`,
              path: ["nodes", key, ref.field],
            });
          }
        }
      }
    }
  });

export function validateToolchainUISpecV2(input: unknown) {
  return zToolchainUISpecV2.safeParse(input);
}
