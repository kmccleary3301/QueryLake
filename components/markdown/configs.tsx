export type segment_types = "regular" | "bold" | 
                            "italic" | "bolditalic" | 
                            "double_dollar" | "single_dollar" | 
                            "escaped_square_brackets" | "escaped_parentheses" |
                            "codespan" | "anchor" | 
                            "strikethrough"

export type rendering_types = "regular" | "bold" | 
                              "italic" | "bolditalic" | 
                              "inline_math" | "newline_math" |
                              "codespan" | "anchor" | 
                              "strikethrough"


// export type markdownRenderingConfig = {[key in segment_types]: rendering_types}

export type markdownRenderingConfig = Partial<{[key in segment_types]: rendering_types}>

const normal_config : markdownRenderingConfig = {
  regular: "regular",
  bold: "bold",
  italic: "italic",
  bolditalic: "bolditalic",
  codespan: "codespan",
  anchor: "anchor",
  strikethrough: "strikethrough"
}

export const OBSIDIAN_MARKDOWN_RENDERING_CONFIG : markdownRenderingConfig = {
  ...normal_config,
  single_dollar: "inline_math",
  double_dollar: "newline_math",
}


export const CHAT_RENDERING_STYLE : markdownRenderingConfig = {
  ...normal_config,
  double_dollar: "newline_math",
  single_dollar: "inline_math",   // Ideally this is disabled
  "escaped_parentheses": "inline_math",
  "escaped_square_brackets": "newline_math"
}



