

export type displayComponents = "chat" | "markdown" | "text" | "graph" | "running_event_display";
export type inputComponents = "file_upload" | "chat_input";

export const DISPLAY_COMPONENTS : displayComponents[] = ["chat", "markdown", "text", "graph", "running_event_display"];
export const INPUT_COMPONENTS : inputComponents[] = ["file_upload", "chat_input"];

export type configEntryFieldType = {
  name: string,
  type: "boolean",
  default: boolean
} | {
  name: string,
  type: "string",
  default: string
} | {
  name: string,
  type: "number",
  default: number
} | {
  name: string,
  type: "long_string",
  default: string
}

export type inputComponentConfig = {
	hooks: string[],
	config?: configEntryFieldType[],
	tailwind?: string,
}


/*  This is for the toolchain interface designer.
 *  The fields config immediately below is for each input component.
 *  Note that the hook `selected_collections` is a special hook 
 *  that is used to send the selected collections to a toolchain event.
 */

export const INPUT_COMPONENT_FIELDS : {[key in inputComponents]: inputComponentConfig} = {
	"file_upload": {
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
		],
	},
	"chat_input": {
		"hooks": [
      "on_upload", 
      "on_submit",
      "selected_collections",
    ],
    "config": [
			{
				"name": "test_1_boolean",
				"type": "boolean",
        "default": false
			},
      {
				"name": "test_2_boolean",
				"type": "boolean",
        "default": true
			},
      {
				"name": "test_3_number",
				"type": "number",
        "default": 3
			},
      {
				"name": "test_4_number",
				"type": "number",
        "default": 4
			},
      {
				"name": "test_5_string",
				"type": "string",
        "default": ""
			},
      {
				"name": "test_6_string",
				"type": "string",
        "default": "6ix"
			},
      {
				"name": "test_7_long_string",
				"type": "long_string",
        "default": "6ix"
			}
		],
	},
}

export type displayMapping = {
  display_route: (string | number)[],
  display_as: displayComponents;
}

export type inputEvent = {
  hook: string,
  target_event: string,
  fire_index: number,
  // target_route: (string | number)[],
  store: boolean,
  target_route: string,
}

export type configEntry = {
  name: string,
  value: string | number | boolean
}

// export type inputMappingProto = {
//   hooks: inputEvent[],
//   config: configEntry[],
//   tailwind: string,
// }

// export type fileUploadMapping = inputMappingProto & {
//   display_as: "file_upload"
// }

// export type chatInputMapping = inputMappingProto & {
//   display_as: "chat_input"
// }



// export type inputMapping = fileUploadMapping | chatInputMapping;

export type inputMapping = {
  display_as: string,
  hooks: inputEvent[],
  config: configEntry[],
  tailwind: string,
}

export type contentMapping = displayMapping | inputMapping;

export type alignType = "left" | "center" | "right" | "justify";

export type contentDiv = {
  type: "div",
  align: alignType,
  tailwind: string,
  mappings: (contentMapping | contentDiv)[]
}

export type contentSection = {
  split: "none",
  size: number,
  align: alignType,
  tailwind: string,
  mappings: (contentMapping | contentDiv)[],
  header?: headerSection,
  footer?: headerSection
}

export type divisionSection = {
  split: "horizontal" | "vertical",
  size: number,
  sections: displaySection[],
  header?: headerSection,
  footer?: headerSection
}


export type headerSection = {
  align: alignType,
  tailwind: string,
  mappings: contentMapping[]
}

export type displaySection = contentSection | divisionSection
