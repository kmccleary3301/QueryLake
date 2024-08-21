"use client";
import { retrieveValueFromObj, toolchainStateType } from "@/hooks/toolchain-session";
import { componentMetaDataType, displayMapping } from "@/types/toolchain-interface";
import MarkdownRenderer from "@/components/markdown/markdown-renderer";
import { useToolchainContextAction } from "@/app/app/context-provider";
import { useContextAction } from "@/app/context-provider";
import { useEffect, useState } from "react";
import MARKDOWN_SAMPLE_TEXT from "@/components/markdown/demo-text";

export const METADATA : componentMetaDataType = {
	label: "Markdown",
	category: "Text Display",
	description: "Displays text as markdown.",
};

export default function Markdown({
	configuration,
  demo = false,
}:{
	configuration: displayMapping,
  demo?: boolean,
}) {

  const { toolchainState, toolchainWebsocket } = useToolchainContextAction();
  const { userData } = useContextAction();

	const [currentValue, setCurrentValue] = useState<string>(
    demo ?
    MARKDOWN_SAMPLE_TEXT :
    retrieveValueFromObj(toolchainState, configuration.display_route) as string || ""
	);

  useEffect(() => {
		if (toolchainWebsocket?.current === undefined || demo) return;
    const newValue = retrieveValueFromObj(toolchainState, configuration.display_route) as string || "";
    // console.log("Chat newValue", JSON.parse(JSON.stringify(newValue)));
		setCurrentValue(newValue);
	}, [toolchainState]);

  return (
    <div className="max-w-full p-0 -mt-1.5">
      <MarkdownRenderer
        // disableRender={(value.role === "user")}
        input={currentValue} 
        finished={false}
      />
	  </div>
  );
}