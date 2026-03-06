import ToolchainInterfaceEditorV2 from "@/components/toolchains-v2/interface-editor";

export default async function ToolchainInterfaceEditorPage({
  params,
}: {
  params: Promise<{ workspace: string; toolchainId: string }>;
}) {
  const resolved = await params;
  return <ToolchainInterfaceEditorV2 params={resolved} />;
}
