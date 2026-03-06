"use client";

import type { ComponentType } from "react";

import { INPUT_COMPONENT_FIELDS } from "@/types/toolchain-interface";
import type { configEntryFieldType, inputComponents } from "@/types/toolchain-interface";
import {
  TOOLCHAIN_V2_LOADERS,
  TOOLCHAIN_V2_MANIFESTS,
} from "@/__generated__/toolchains/toolchain-v2-registry";
import type {
  FieldSchema,
  ToolchainComponentManifest,
} from "@/types/toolchain-component-manifest";

export type ToolchainComponentRegistryEntry = {
  manifest: ToolchainComponentManifest;
  load: () => Promise<{ default: ComponentType<any> }>;
};

function legacyFieldToSchema(field: configEntryFieldType): FieldSchema {
  switch (field.type) {
    case "boolean":
      return { type: "boolean", default: field.default };
    case "number":
      return { type: "number", default: field.default };
    case "string":
      return { type: "string", default: field.default };
    case "long_string":
      return { type: "string", default: field.default, multiline: true };
    default: {
      const exhaustive: never = field;
      return exhaustive;
    }
  }
}

function buildLegacyInputConfig(componentId: string) {
  const legacy = INPUT_COMPONENT_FIELDS[componentId as inputComponents];
  if (!legacy) return undefined;

  const config: Record<string, FieldSchema> = {};
  for (const field of legacy.config ?? []) {
    config[field.name] = legacyFieldToSchema(field);
  }

  const hooks: Record<string, { label?: string }> = {};
  for (const hookName of legacy.hooks ?? []) {
    hooks[hookName] = { label: hookName };
  }

  return { config, hooks };
}

export const TOOLCHAIN_COMPONENT_REGISTRY: Record<
  string,
  ToolchainComponentRegistryEntry
> = Object.fromEntries(
  TOOLCHAIN_V2_MANIFESTS.map((base) => {
    const legacyInput = base.kind === "input" ? buildLegacyInputConfig(base.id) : undefined;
    const manifest: ToolchainComponentManifest = {
      ...base,
      ...(legacyInput?.config && !base.config ? { config: legacyInput.config } : {}),
      ...(legacyInput?.hooks && !base.hooks ? { hooks: legacyInput.hooks } : {}),
    };
    return [
      base.id,
      {
        manifest,
        load: TOOLCHAIN_V2_LOADERS[base.id],
      } as ToolchainComponentRegistryEntry,
    ];
  })
);

export function listToolchainComponents(): ToolchainComponentRegistryEntry[] {
  return Object.values(TOOLCHAIN_COMPONENT_REGISTRY);
}

export function getToolchainComponentManifest(
  componentId: string
): ToolchainComponentManifest | undefined {
  return TOOLCHAIN_COMPONENT_REGISTRY[componentId]?.manifest;
}
