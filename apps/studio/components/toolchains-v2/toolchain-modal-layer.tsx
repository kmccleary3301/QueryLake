"use client";

import { useCallback, useEffect, useState } from "react";

import { useContextAction } from "@/app/context-provider";
import SidebarCollectionSelect from "@/components/sidebar/sidebar-collections";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

const COLLECTION_MODAL_ID = "collectionPicker";
const MODEL_MODAL_ID = "modelPicker";

export default function ToolchainModalLayer() {
  const {
    userData,
    collectionGroups,
    setCollectionGroups,
    refreshCollectionGroups,
    selectedCollections,
    setSelectedCollections,
    toolchainUI,
    setToolchainUI,
  } = useContextAction();

  const activeModal = toolchainUI?.modal?.active;
  const showCollectionPicker = activeModal === COLLECTION_MODAL_ID;
  const showModelPicker = activeModal === MODEL_MODAL_ID;

  const closeModal = useCallback(() => {
    setToolchainUI((prev) => ({
      ...prev,
      modal: { ...prev.modal, active: undefined },
    }));
  }, [setToolchainUI]);

  useEffect(() => {
    if (!showCollectionPicker) return;
    if (!userData?.auth) return;
    if (collectionGroups.length === 0) {
      refreshCollectionGroups();
    }
  }, [collectionGroups.length, refreshCollectionGroups, showCollectionPicker, userData?.auth]);

  const setCollectionSelected = useCallback(
    (collectionHashId: string, value: boolean) => {
      setSelectedCollections((prev) => {
        const next = new Map(prev);
        next.set(collectionHashId, value);
        return next;
      });
    },
    [setSelectedCollections]
  );

  const [modelDraft, setModelDraft] = useState("");

  useEffect(() => {
    if (showModelPicker) {
      setModelDraft(toolchainUI?.model?.selectedModelId ?? "");
    }
  }, [showModelPicker, toolchainUI?.model?.selectedModelId]);

  const applyModel = useCallback(() => {
    setToolchainUI((prev) => ({
      ...prev,
      model: {
        ...prev.model,
        selectedModelId: modelDraft || undefined,
      },
      modal: { ...prev.modal, active: undefined },
    }));
  }, [modelDraft, setToolchainUI]);

  return (
    <>
      <Sheet
        open={showCollectionPicker}
        onOpenChange={(open) => {
          if (!open) closeModal();
        }}
      >
        <SheetContent side="left" className="w-[360px] sm:max-w-[360px]">
          <SheetHeader>
            <SheetTitle>Collections</SheetTitle>
          </SheetHeader>
          <div className="mt-4 h-[calc(100vh-120px)]">
            {userData ? (
              <SidebarCollectionSelect
                scrollClassName="h-full overflow-auto scrollbar-hide"
                userData={userData}
                collectionGroups={collectionGroups}
                setCollectionGroups={setCollectionGroups}
                setCollectionSelected={setCollectionSelected}
                selectedCollections={selectedCollections}
              />
            ) : (
              <div className="text-sm text-muted-foreground">
                Sign in to select collections.
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>

      <Dialog
        open={showModelPicker}
        onOpenChange={(open) => {
          if (!open) closeModal();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Model selection</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Store a default model identifier to use in toolchain prompts.
            </p>
            <Input
              value={modelDraft}
              placeholder="e.g. openai/gpt-4o"
              onChange={(event) => setModelDraft(event.target.value)}
            />
          </div>
          <DialogFooter className="mt-4">
            <Button variant="ghost" onClick={closeModal}>
              Cancel
            </Button>
            <Button onClick={applyModel}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
