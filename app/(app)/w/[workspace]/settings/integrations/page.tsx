"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { useContextAction } from "@/app/context-provider";
import { modifyUserExternalProviders } from "@/hooks/querylakeAPI";

const isPersonalWorkspace = (workspace: string) =>
  workspace === "personal" || workspace === "me";

export default function Page() {
  const params = useParams<{ workspace: string }>()!;
  const { userData, setUserData, authReviewed, loginValid } =
    useContextAction();
  const [currentProvider, setCurrentProvider] = useState("");
  const [currentKeyInput, setCurrentKeyInput] = useState("");
  const [keyAvailable, setKeyAvailable] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const providerOptions = useMemo(() => {
    return (userData?.providers ?? []).map((provider) => provider.toLowerCase());
  }, [userData?.providers]);

  useEffect(() => {
    if (!currentProvider) return;
    const hasKey = userData?.user_set_providers.includes(currentProvider) ?? false;
    setKeyAvailable(hasKey);
    setCurrentKeyInput("");
    setStatus(null);
  }, [currentProvider, userData?.user_set_providers]);

  const saveKey = () => {
    if (!userData?.auth) return;
    if (!currentProvider) {
      setStatus("Select a provider first.");
      return;
    }
    if (!currentKeyInput.trim()) {
      setStatus("Enter an API key to save.");
      return;
    }
    modifyUserExternalProviders({
      auth: userData.auth,
      update: { [currentProvider]: currentKeyInput },
      onFinish: (success) => {
        setStatus(success ? "Key saved." : "Failed to save key.");
        if (success && userData) {
          setUserData({
            ...userData,
            user_set_providers: Array.from(
              new Set([...userData.user_set_providers, currentProvider])
            ),
          });
          setKeyAvailable(true);
          setCurrentKeyInput("");
        }
      },
    });
  };

  const deleteKey = () => {
    if (!userData?.auth || !currentProvider) return;
    modifyUserExternalProviders({
      auth: userData.auth,
      delete: [currentProvider],
      onFinish: (success) => {
        setStatus(success ? "Key deleted." : "Failed to delete key.");
        if (success && userData) {
          setUserData({
            ...userData,
            user_set_providers: userData.user_set_providers.filter(
              (provider) => provider !== currentProvider
            ),
          });
          setKeyAvailable(false);
          setCurrentKeyInput("");
        }
      },
    });
  };

  if (!authReviewed) {
    return (
      <div className="max-w-4xl space-y-6">
        <div className="h-6 w-48 rounded bg-muted" />
        <div className="h-4 w-72 rounded bg-muted" />
      </div>
    );
  }

  if (!loginValid || !userData) {
    return (
      <div className="max-w-4xl space-y-4">
        <h1 className="text-2xl font-semibold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          Sign in to manage provider keys.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href={`/w/${params.workspace}`}>Workspace</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <BreadcrumbLink href={`/w/${params.workspace}/settings`}>Settings</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbItem>
              <BreadcrumbPage>Integrations</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
        <h1 className="text-2xl font-semibold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          Configure external providers, OAuth, and webhooks.
        </p>
      </div>

      {!isPersonalWorkspace(params.workspace) && (
        <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
          Provider keys are currently user-scoped. Workspace-level keys will be
          added once the backend supports org-scoped provider settings.
        </div>
      )}

      <div className="rounded-lg border border-border p-5 space-y-4">
        <div className="text-sm font-semibold">Provider keys</div>
        <div className="flex flex-wrap gap-3">
          <Select
            value={currentProvider}
            onValueChange={(value) => setCurrentProvider(value)}
          >
            <SelectTrigger className="w-[240px]">
              <SelectValue placeholder="Select provider" />
            </SelectTrigger>
            <SelectContent>
              {providerOptions.map((provider) => (
                <SelectItem key={provider} value={provider}>
                  {provider}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            className="min-w-[280px]"
            type="password"
            placeholder={
              keyAvailable
                ? "Key is stored. Paste a new key to rotate."
                : "Enter API key"
            }
            value={currentKeyInput}
            onChange={(event) => setCurrentKeyInput(event.target.value)}
          />
          <Button onClick={saveKey} disabled={!currentProvider || !currentKeyInput.trim()}>
            Save
          </Button>
          <Button
            variant="outline"
            onClick={deleteKey}
            disabled={!currentProvider || !keyAvailable}
          >
            Delete
          </Button>
        </div>
        {status ? <p className="text-xs text-muted-foreground">{status}</p> : null}
      </div>
    </div>
  );
}
