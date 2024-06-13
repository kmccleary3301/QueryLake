import { inputComponentConfig } from "@/types/toolchain-interface";

export type displayComponents = "chat" | "current-event-display" | "markdown" | "text";
export type inputComponents = "chat-input" | "file-upload" | "switch";
export const DISPLAY_COMPONENTS : displayComponents[] = ["chat","current-event-display","markdown","text"];
export const INPUT_COMPONENTS : inputComponents[] = ["chat-input","file-upload","switch"];
export const INPUT_COMPONENT_FIELDS : {[key in inputComponents]: inputComponentConfig} = {
  "chat-input": {
    "hooks": [
      "on_upload",
      "on_submit",
      "selected_collections"
    ],
    "config": [
      {
        "name": "test_7_long_string",
        "type": "long_string",
        "default": "6ix"
      }
    ]
  },
  "file-upload": {
    "hooks": [
      "on_upload",
      "selected_collections"
    ],
    "config": [
      {
        "name": "multiple",
        "type": "boolean",
        "default": false
      }
    ]
  },
  "switch": {
    "hooks": [
      "value_map"
    ],
    "config": [
      {
        "name": "Label",
        "type": "string",
        "default": ""
      }
    ]
  }
};