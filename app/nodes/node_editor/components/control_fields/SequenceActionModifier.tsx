import { HoverTextDiv } from "@/registry/default/ui/hover-text-div";
import { createAction, sequenceAction, sequenceActionNonStatic } from "@/types/toolchains";

export default function sequenceActionModifier({
  data,
  className = "",
}:{
  data : sequenceAction,
  className?: string,
}) {

  return(
    <>
      {((typeof data === "object") && 
      ((data as createAction).type === "createAction")) && (
          <div className="flex flex-row">
            <HoverTextDiv hint="Create Action">
              <p className="">C</p>
            </HoverTextDiv>
            {((data as createAction).initialValue !== undefined) && (
              <div/>
            )}
          </div>
      )}
    </>
  );
}