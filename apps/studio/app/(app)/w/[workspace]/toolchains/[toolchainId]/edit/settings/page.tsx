"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { toast } from "sonner";

import { useContextAction } from "@/app/context-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { fetchToolchainConfig, updateToolchainConfig } from "@/hooks/querylakeAPI";
import { cn } from "@/lib/utils";
import type { ToolChain } from "@/types/toolchains";

function splitCommaList(raw: string): string[] {
  return raw
    .split(",")
    .map((token) => token.trim())
    .filter(Boolean);
}

function joinCommaList(values?: string[]): string {
  return values?.join(", ") ?? "";
}

function normalizeRoleList(raw: string): string[] {
  const dedupe = new Set<string>();
  for (const token of splitCommaList(raw)) {
    const normalized = token.toLowerCase();
    if (normalized) dedupe.add(normalized);
  }
  return Array.from(dedupe);
}

type SettingsDraft = {
  name: string;
  category: string;
  firstEvent: string;
  description: string;
  tagsText: string;
  visibility: "private" | "workspace" | "public";
  viewRolesText: string;
  editRolesText: string;
  draft: boolean;
};

function draftFromToolchain(toolchain: ToolChain): SettingsDraft {
  return {
    name: toolchain.name ?? "",
    category: toolchain.category ?? "",
    firstEvent: toolchain.first_event_follow_up ?? "",
    description: toolchain.editor_meta?.settings?.description ?? "",
    tagsText: joinCommaList(toolchain.editor_meta?.settings?.tags),
    visibility: toolchain.editor_meta?.settings?.visibility ?? "workspace",
    viewRolesText: joinCommaList(toolchain.editor_meta?.settings?.permissions?.view),
    editRolesText: joinCommaList(toolchain.editor_meta?.settings?.permissions?.edit),
    draft: Boolean(toolchain.editor_meta?.settings?.draft),
  };
}

function serializeDraft(draft: SettingsDraft): string {
  return JSON.stringify(draft);
}

export default function ToolchainEditorSettingsPlaceholder() {
  const { userData, authReviewed, loginValid } = useContextAction();
  const params = useParams<{ toolchainId: string }>();
  const toolchainId = params?.toolchainId;
  const [toolchain, setToolchain] = useState<ToolChain | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveFailed, setSaveFailed] = useState(false);
  const [baselineDraftSerialized, setBaselineDraftSerialized] = useState<string>("");
  const [lastSavePayload, setLastSavePayload] = useState<ToolChain | null>(null);

  const [name, setName] = useState("");
  const [category, setCategory] = useState("");
  const [firstEvent, setFirstEvent] = useState("");
  const [description, setDescription] = useState("");
  const [tagsText, setTagsText] = useState("");
  const [visibility, setVisibility] = useState<"private" | "workspace" | "public">("workspace");
  const [viewRolesText, setViewRolesText] = useState("");
  const [editRolesText, setEditRolesText] = useState("");
  const [draft, setDraft] = useState(false);

  const applyDraft = useCallback((nextDraft: SettingsDraft) => {
    setName(nextDraft.name);
    setCategory(nextDraft.category);
    setFirstEvent(nextDraft.firstEvent);
    setDescription(nextDraft.description);
    setTagsText(nextDraft.tagsText);
    setVisibility(nextDraft.visibility);
    setViewRolesText(nextDraft.viewRolesText);
    setEditRolesText(nextDraft.editRolesText);
    setDraft(nextDraft.draft);
  }, []);

  const loadToolchain = useCallback(() => {
    if (!authReviewed || !loginValid || !userData?.auth || !toolchainId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchToolchainConfig({
      auth: userData.auth,
      toolchain_id: toolchainId,
      onFinish: (result: ToolChain) => {
        setToolchain(result);
        const loadedDraft = draftFromToolchain(result);
        applyDraft(loadedDraft);
        setBaselineDraftSerialized(serializeDraft(loadedDraft));
        setSaveFailed(false);
        setLastSavePayload(null);
        setLoading(false);
      },
    });
  }, [applyDraft, authReviewed, loginValid, toolchainId, userData?.auth]);

  useEffect(() => {
    if (!authReviewed) return;
    if (!loginValid || !userData?.auth) {
      setLoading(false);
      return;
    }
    if (!toolchainId) {
      setLoading(false);
      return;
    }
    loadToolchain();
  }, [authReviewed, loadToolchain, loginValid, toolchainId, userData?.auth]);

  const currentDraft = useMemo<SettingsDraft>(
    () => ({
      name,
      category,
      firstEvent,
      description,
      tagsText,
      visibility,
      viewRolesText,
      editRolesText,
      draft,
    }),
    [category, description, draft, editRolesText, firstEvent, name, tagsText, viewRolesText, visibility]
  );

  const hasUnsavedChanges = useMemo(() => {
    if (!baselineDraftSerialized) return false;
    return serializeDraft(currentDraft) !== baselineDraftSerialized;
  }, [baselineDraftSerialized, currentDraft]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (!hasUnsavedChanges) return;
      event.preventDefault();
      event.returnValue = "";
    };

    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [hasUnsavedChanges]);

  const nodeIds = useMemo(() => new Set((toolchain?.nodes ?? []).map((node) => node.id)), [toolchain]);
  const normalizedViewRoles = useMemo(() => normalizeRoleList(viewRolesText), [viewRolesText]);
  const normalizedEditRoles = useMemo(() => normalizeRoleList(editRolesText), [editRolesText]);

  const validationErrors = useMemo(() => {
    const issues: string[] = [];
    if (!name.trim()) {
      issues.push("Name is required.");
    }
    const nextFirstEvent = firstEvent.trim();
    if (nextFirstEvent && !nodeIds.has(nextFirstEvent)) {
      issues.push(`First event follow-up must match an existing node id (${nextFirstEvent}).`);
    }
    const rawRoles = [...splitCommaList(viewRolesText), ...splitCommaList(editRolesText)];
    const invalidRoles = Array.from(
      new Set(rawRoles.filter((token) => !/^[a-zA-Z0-9:_-]+$/.test(token)))
    );
    if (invalidRoles.length) {
      issues.push(
        `Role tokens may only include letters, numbers, ':', '_' or '-': ${invalidRoles.join(", ")}.`
      );
    }
    const missingEditViewCoverage = normalizedEditRoles.filter(
      (role) => !normalizedViewRoles.includes(role)
    );
    if (missingEditViewCoverage.length) {
      issues.push(
        `Edit roles should also be present in view roles: ${missingEditViewCoverage.join(", ")}.`
      );
    }
    return issues;
  }, [editRolesText, firstEvent, name, nodeIds, normalizedEditRoles, normalizedViewRoles, viewRolesText]);

  const buildNextToolchain = useCallback((): ToolChain | null => {
    if (!toolchain) return null;
    const nextFirstEvent = firstEvent.trim();
    const nextToolchain: ToolChain = {
      ...toolchain,
      name: name.trim(),
      category: category.trim() || "General",
      editor_meta: {
        ...(toolchain.editor_meta ?? {}),
        settings: {
          ...(toolchain.editor_meta?.settings ?? {}),
          description: description.trim(),
          tags: splitCommaList(tagsText),
          visibility,
          permissions: {
            view: normalizedViewRoles,
            edit: normalizedEditRoles,
          },
          draft,
        },
      },
    };
    if (nextFirstEvent) {
      nextToolchain.first_event_follow_up = nextFirstEvent;
    } else {
      delete nextToolchain.first_event_follow_up;
    }
    return nextToolchain;
  }, [
    category,
    description,
    draft,
    firstEvent,
    name,
    normalizedEditRoles,
    normalizedViewRoles,
    tagsText,
    toolchain,
    visibility,
  ]);

  const persistSettings = useCallback(
    (nextToolchain: ToolChain) => {
      if (!userData?.auth) return;
      if (!toolchainId) return;
      setSaving(true);
      setSaveFailed(false);
      setLastSavePayload(nextToolchain);
      updateToolchainConfig({
        auth: userData.auth,
        toolchain_id: toolchainId,
        toolchain: nextToolchain as unknown as Record<string, unknown>,
        onFinish: (result: { toolchain_id: string } | false) => {
          setSaving(false);
          if (!result) {
            setSaveFailed(true);
            toast.error("Failed to save settings. You can retry without losing your draft.");
            return;
          }
          setToolchain(nextToolchain);
          const savedDraft = draftFromToolchain(nextToolchain);
          applyDraft(savedDraft);
          setBaselineDraftSerialized(serializeDraft(savedDraft));
          setSaveFailed(false);
          setLastSavePayload(null);
          toast.success("Saved toolchain settings");
        },
      });
    },
    [applyDraft, toolchainId, userData?.auth]
  );

  const saveSettings = () => {
    if (validationErrors.length) {
      toast.error("Fix validation issues before saving.");
      return;
    }
    const nextToolchain = buildNextToolchain();
    if (!nextToolchain) return;
    persistSettings(nextToolchain);
  };

  const resetToBaseline = () => {
    if (!toolchain) return;
    const baselineDraft = draftFromToolchain(toolchain);
    applyDraft(baselineDraft);
    setSaveFailed(false);
    toast.success("Reset unsaved changes.");
  };

  const retryLastSave = () => {
    if (!lastSavePayload) return;
    persistSettings(lastSavePayload);
  };

  const canSave = hasUnsavedChanges && validationErrors.length === 0 && !saving;

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
  if (loading || !toolchain) {
    return <div className="ql-editor-state">Loading toolchain settings...</div>;
  }

  return (
    <div className="ql-editor-shell">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold">Toolchain editor settings</div>
          <div className="text-xs text-muted-foreground">
            Persisted metadata and editor permissions for this toolchain.
          </div>
          <div
            className={cn(
              "ql-editor-status",
              hasUnsavedChanges ? "ql-editor-status-unsaved" : "ql-editor-status-saved"
            )}
          >
            {hasUnsavedChanges ? "Unsaved changes" : "All changes saved"}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button size="sm" variant="outline" onClick={loadToolchain} disabled={loading || saving}>
            Reload
          </Button>
          <Button size="sm" variant="outline" onClick={resetToBaseline} disabled={!hasUnsavedChanges || saving}>
            Reset
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={retryLastSave}
            disabled={!saveFailed || !lastSavePayload || saving}
          >
            Retry save
          </Button>
          <Button size="sm" onClick={saveSettings} disabled={!canSave}>
            {saving ? "Saving..." : "Save settings"}
          </Button>
        </div>
      </div>

      {validationErrors.length ? (
        <div className="ql-editor-alert-error">
          <div className="font-semibold">Validation issues</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {validationErrors.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {saveFailed ? (
        <div className="ql-editor-alert-warning">
          Last save failed. Use <span className="font-semibold">Retry save</span> or keep editing.
        </div>
      ) : null}

      <div className="grid gap-3 lg:grid-cols-2">
        <section className="ql-editor-inset p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Metadata</div>
          <div className="mt-3 grid gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Name</Label>
              <Input value={name} onChange={(event) => setName(event.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Category</Label>
              <Input value={category} onChange={(event) => setCategory(event.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">First event follow-up</Label>
              <Input
                value={firstEvent}
                onChange={(event) => setFirstEvent(event.target.value)}
                placeholder="Optional node id"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Description</Label>
              <Textarea
                rows={4}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Short internal description"
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Tags (comma-separated)</Label>
              <Input
                value={tagsText}
                onChange={(event) => setTagsText(event.target.value)}
                placeholder="rag, basf, demo"
              />
            </div>
          </div>
        </section>

        <section className="ql-editor-inset p-3">
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Permissions</div>
          <div className="mt-3 grid gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Visibility</Label>
              <select
                className="h-7 w-full rounded-sm border border-border bg-background px-2 text-xs"
                value={visibility}
                onChange={(event) =>
                  setVisibility(event.target.value as "private" | "workspace" | "public")
                }
              >
                <option value="private">private</option>
                <option value="workspace">workspace</option>
                <option value="public">public</option>
              </select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">View roles (comma-separated)</Label>
              <Input
                value={viewRolesText}
                onChange={(event) => setViewRolesText(event.target.value)}
                placeholder="owner, member"
              />
              <div className="text-[11px] text-muted-foreground">
                Normalized: {normalizedViewRoles.join(", ") || "(none)"}
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Edit roles (comma-separated)</Label>
              <Input
                value={editRolesText}
                onChange={(event) => setEditRolesText(event.target.value)}
                placeholder="owner"
              />
              <div className="text-[11px] text-muted-foreground">
                Normalized: {normalizedEditRoles.join(", ") || "(none)"}
              </div>
            </div>
            <label className="flex items-center gap-2 text-xs text-muted-foreground">
              <input
                type="checkbox"
                checked={draft}
                onChange={(event) => setDraft(event.target.checked)}
              />
              Mark as draft
            </label>
          </div>
        </section>

        <section className="ql-editor-inset p-3 lg:col-span-2">
          <div className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Notes
          </div>
          <p className="mt-2 text-sm text-muted-foreground">
            These settings are persisted into toolchain JSON (`name`, `category`,
            `first_event_follow_up`, and `editor_meta.settings.*`) and can be
            expanded as lifecycle tooling lands.
          </p>
        </section>
      </div>
    </div>
  );
}
