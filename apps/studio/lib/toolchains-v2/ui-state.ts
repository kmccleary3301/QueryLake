import type { selectedCollectionsType } from "@/types/globalTypes";
import type { ToolchainUIState } from "@/types/toolchain-ui-state";

export function selectedCollectionIds(
  selectedCollections: selectedCollectionsType
): string[] {
  return Array.from(selectedCollections.entries())
    .filter(([, selected]) => selected)
    .map(([id]) => id);
}

export function buildToolchainUIState(
  selectedCollections: selectedCollectionsType,
  prev?: ToolchainUIState
): ToolchainUIState {
  return {
    collections: {
      selectedIds: selectedCollectionIds(selectedCollections),
    },
    model: prev?.model,
    modal: prev?.modal,
  };
}
