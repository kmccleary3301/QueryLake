export type ToolchainUIState = {
  collections: {
    selectedIds: string[];
  };
  model?: {
    selectedModelId?: string;
    parameters?: Record<string, unknown>;
  };
  modal?: {
    active?: string;
  };
};
