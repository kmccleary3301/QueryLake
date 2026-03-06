import ToolchainGraphEditorClient from "@/components/toolchains-v2/graph-editor";

export default async function ToolchainGraphEditorPage({
  params,
}: {
  params: Promise<{ workspace: string; toolchainId: string }>;
}) {
  const resolved = await params;
  return <ToolchainGraphEditorClient params={resolved} />;
}

