

export type displayComponents = "chat" | "markdown" | "text" | "graph";
export type inputComponents = "file_upload" | "chat_input";

export const DISPLAY_COMPONENTS : displayComponents[] = ["chat", "markdown", "text", "graph"];
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
}

export type inputComponentConfig = {
	hooks: string[],
	config?: configEntryFieldType[],
	tailwind?: string,
}

export const INPUT_COMPONENT_FIELDS : {[key in inputComponents]: inputComponentConfig} = {
	"file_upload": {
		"hooks": ["on_upload"],
		"config": [
			{
				"name": "multiple",
				"type": "boolean",
        "default": false
			}
		],
	},
	"chat_input": {
		"hooks": ["on_upload", "on_submit"],
	},
}

export type displayMapping = {
  display_route: (string | number)[],
  display_as: displayComponents;
}

export type inputEvent = {
  hook: string,
  target_event: string,
  // target_route: (string | number)[],
  store: boolean,
  target_route: string,
}

export type configEntry = {
  name: string,
  value: string | number | boolean
}

export type inputMappingProto = {
  hooks: inputEvent[],
  config: configEntry[],
  tailwind: string,
}

export type fileUploadMapping = inputMappingProto & {
  display_as: "file_upload"
}

export type chatInputMapping = inputMappingProto & {
  display_as: "chat_input"
}

export type inputMapping = fileUploadMapping | chatInputMapping;
export type contentMapping = displayMapping | inputMapping;

export type contentSection = {
  split: "none",
  align: alignType,
  tailwind: string,
  mappings: contentMapping[],
  header?: headerSection,
  footer?: headerSection
}

export type divisionSection = {
  split: "horizontal" | "vertical",
  sections: displaySection[],
  header?: headerSection,
  footer?: headerSection
}

export type alignType = "left" | "center" | "right" | "justify";

export type headerSection = {
  align: alignType,
  tailwind: string,
  mappings: contentMapping[]
}

export type displaySection = contentSection | divisionSection
