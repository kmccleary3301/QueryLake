"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useContextAction } from "@/app/context-provider";
import { QueryLakeApiKey } from "@/types/globalTypes";
import { createApiKey, deleteApiKey, fetchApiKeys } from "@/hooks/querylakeAPI";

export default function Page() {
  const { userData, authReviewed, loginValid } = useContextAction();
  const [keys, setKeys] = useState<QueryLakeApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmingKey, setConfirmingKey] = useState<QueryLakeApiKey | null>(
    null
  );

  const refreshKeys = useCallback(() => {
    if (!userData?.auth) return;
    setLoading(true);
    fetchApiKeys({
      auth: userData.auth,
      onFinish: (result) => {
        if (result && Array.isArray(result)) {
          setKeys(result);
        } else {
          setKeys([]);
        }
        setLoading(false);
      },
    });
  }, [userData?.auth]);

  useEffect(() => {
    if (!authReviewed || !loginValid || !userData?.auth) {
      setLoading(false);
      return;
    }
    refreshKeys();
  }, [authReviewed, loginValid, userData?.auth, refreshKeys]);

  if (!authReviewed) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-border p-5 space-y-3">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-56" />
          <Skeleton className="h-4 w-44" />
        </div>
      </div>
    );
  }

  if (!loginValid || !userData) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">API keys</h1>
        <p className="text-sm text-muted-foreground">
          Sign in to manage API keys.
        </p>
      </div>
    );
  }

  const createKey = () => {
    if (!userData?.auth) return;
    setCreating(true);
    setStatus(null);
    createApiKey({
      auth: userData.auth,
      name: newKeyName.trim() || undefined,
      onFinish: (result) => {
        setCreating(false);
        if (!result) {
          setStatus("Failed to create API key.");
          return;
        }
        setCreatedKey(result.api_key);
        setNewKeyName("");
        setStatus("API key created. Copy it now; it will not be shown again.");
        refreshKeys();
      },
    });
  };

  const removeKey = (id: string) => {
    if (!userData?.auth) return;
    setDeletingId(id);
    deleteApiKey({
      auth: userData.auth,
      api_key_id: id,
      onFinish: (success) => {
        setDeletingId(null);
        if (!success) {
          setStatus("Failed to delete API key.");
          return;
        }
        refreshKeys();
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Breadcrumb>
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbPage>Platform</BreadcrumbPage>
              </BreadcrumbItem>
              <BreadcrumbItem>
                <BreadcrumbPage>API keys</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <h1 className="text-2xl font-semibold">API keys</h1>
          <p className="text-sm text-muted-foreground">
            Create and manage workspace-scoped API keys.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            placeholder="Key name (optional)"
            className="w-[220px]"
            value={newKeyName}
            onChange={(event) => setNewKeyName(event.target.value)}
          />
          <Button onClick={createKey} disabled={creating}>
            {creating ? "Creating..." : "Create key"}
          </Button>
        </div>
      </div>

      {createdKey && (
        <div className="rounded-lg border border-border bg-card/40 p-4 text-sm">
          <div className="font-medium">New API key</div>
          <div className="mt-2 break-all rounded-md border border-border bg-background p-3 font-mono text-xs">
            {createdKey}
          </div>
          <div className="mt-2 flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                navigator.clipboard.writeText(createdKey);
                setStatus("API key copied to clipboard.");
              }}
            >
              Copy
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setCreatedKey(null)}>
              Dismiss
            </Button>
          </div>
        </div>
      )}

      {status && (
        <div className="rounded-lg border border-border p-3 text-xs text-muted-foreground">
          {status}
        </div>
      )}

      <div className="rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Key preview</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Last used</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={5} className="py-6 text-center text-sm text-muted-foreground">
                  Loading API keys...
                </TableCell>
              </TableRow>
            ) : keys.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="py-6 text-center text-sm text-muted-foreground">
                  No API keys found. Create one above to get started.
                </TableCell>
              </TableRow>
            ) : (
              keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell className="font-medium">{key.title}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {key.key_preview}
                  </TableCell>
                  <TableCell>
                    {key.created_string ??
                      new Date(key.created * 1000).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {key.last_used_string ??
                      (key.last_used
                        ? new Date(key.last_used * 1000).toLocaleDateString()
                        : "Never")}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          navigator.clipboard.writeText(key.key_preview);
                          setStatus("Key preview copied to clipboard.");
                        }}
                      >
                        Copy preview
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={deletingId === key.id}
                        onClick={() => setConfirmingKey(key)}
                      >
                        {deletingId === key.id ? "Deleting..." : "Delete"}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <AlertDialog
        open={Boolean(confirmingKey)}
        onOpenChange={(open) => {
          if (!open) setConfirmingKey(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API key</AlertDialogTitle>
            <AlertDialogDescription>
              This will revoke the API key
              {confirmingKey?.title ? ` “${confirmingKey.title}”` : ""}. Any
              clients using it will fail authentication.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="rounded-md border border-border bg-background p-3 text-xs text-muted-foreground">
            Preview: <span className="font-mono">{confirmingKey?.key_preview}</span>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (!confirmingKey) return;
                removeKey(confirmingKey.id);
                setConfirmingKey(null);
              }}
            >
              Delete key
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
