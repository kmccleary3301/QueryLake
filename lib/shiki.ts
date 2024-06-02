import type { BundledLanguage, BundledTheme } from 'shiki'
import { codeToHtml } from 'shiki'

const languages = [
  ["ABAP", "abap"],
  ["ActionScript", "actionscript-3"],
  ["Ada", "ada"],
  ["Angular HTML", "angular-html"],
  ["Angular TypeScript", "angular-ts"],
  ["Apache Conf", "apache"],
  ["Apex", "apex"],
  ["APL", "apl"],
  ["AppleScript", "applescript"],
  ["Ara", "ara"],
  ["Assembly", "asm", "nasm"],
  ["Astro", "astro"],
  ["AWK", "awk"],
  ["Ballerina", "ballerina"],
  ["Batch File", "bat", "batch"],
  ["Beancount", "beancount"],
  ["Berry", "berry", "be"],
  ["BibTeX", "bibtex"],
  ["Bicep", "bicep"],
  ["Blade", "blade"],
  ["C", "c"],
  ["Cadence", "cadence", "cdc"],
  ["Clarity", "clarity"],
  ["Clojure", "clojure", "clj"],
  ["CMake", "cmake"],
  ["COBOL", "cobol"],
  ["CodeQL", "codeql", "ql"],
  ["CoffeeScript", "coffee", "coffeescript"],
  ["C++", "cpp", "c++"],
  ["Crystal", "crystal"],
  ["C#", "csharp", "c#cs"],
  ["CSS", "css"],
  ["CSV", "csv"],
  ["CUE", "cue"],
  ["Cypher", "cypher", "cql"],
  ["D", "d"],
  ["Dart", "dart"],
  ["DAX", "dax"],
  ["Diff", "diff"],
  ["Dockerfile", "docker", "dockerfile"],
  ["Dream Maker", "dream-maker"],
  ["Elixir", "elixir"],
  ["Elm", "elm"],
  ["ERB", "erb"],
  ["Erlang", "erlang", "erl"],
  ["Fish", "fish"],
  ["Fortran (Fixed Form)", "fortran-fixed-form", "fforf77"],
  ["Fortran (Free Form)", "fortran-free-form", "f90f95f03f08f18"],
  ["F#", "fsharp", "f#fs"],
  ["GDResource", "gdresource"],
  ["GDScript", "gdscript"],
  ["GDShader", "gdshader"],
  ["Gherkin", "gherkin"],
  ["Git Commit Message", "git-commit"],
  ["Git Rebase Message", "git-rebase"],
  ["Gleam", "gleam"],
  ["Glimmer JS", "glimmer-js", "gjs"],
  ["Glimmer TS", "glimmer-ts", "gts"],
  ["GLSL", "glsl"],
  ["Gnuplot", "gnuplot"],
  ["Go", "go"],
  ["GraphQL", "graphql", "gql"],
  ["Groovy", "groovy"],
  ["Hack", "hack"],
  ["Ruby Haml", "haml"],
  ["Handlebars", "handlebars", "hbs"],
  ["Haskell", "haskell", "hs"],
  ["HashiCorp HCL", "hcl"],
  ["Hjson", "hjson"],
  ["HLSL", "hlsl"],
  ["HTML", "html"],
  ["HTML (Derivative)", "html-derivative"],
  ["HTTP", "http"],
  ["Imba", "imba"],
  ["INI", "ini", "properties"],
  ["Java", "java"],
  ["JavaScript", "javascript", "js"],
  ["Jinja", "jinja"],
  ["Jison", "jison"],
  ["JSON", "json"],
  ["JSON5", "json5"],
  ["JSON with Comments", "jsonc"],
  ["JSON Lines", "jsonl"],
  ["Jsonnet", "jsonnet"],
  ["JSSM", "jssm", "fsl"],
  ["JSX", "jsx"],
  ["Julia", "julia", "jl"],
  ["Kotlin", "kotlin", "kt", "kts"],
  ["Kusto", "kusto", "kql"],
  ["LaTeX", "latex"],
  ["Less", "less"],
  ["Liquid", "liquid"],
  ["Lisp", "lisp"],
  ["Logo", "logo"],
  ["Lua", "lua"],
  ["Makefile", "make", "makefile"],
  ["Markdown", "markdown", "md"],
  ["Marko", "marko"],
  ["MATLAB", "matlab"],
  ["MDC", "mdc"],
  ["MDX", "mdx"],
  ["Mermaid", "mermaid"],
  ["Mojo", "mojo"],
  ["Move", "move"],
  ["Narrat Language", "narrat", "nar"],
  ["Nextflow", "nextflow", "nf"],
  ["Nginx", "nginx"],
  ["Nim", "nim"],
  ["Nix", "nix"],
  ["Nushell", "nushell", "nu"],
  ["Objective-C", "objective-c", "objc"],
  ["Objective-C++", "objective-cpp"],
  ["OCaml", "ocaml"],
  ["Pascal", "pascal"],
  ["Perl", "perl"],
  ["PHP", "php"],
  ["PL/SQL", "plsql"],
  ["PostCSS", "postcss"],
  ["PowerQuery", "powerquery"],
  ["PowerShell", "powershell", "ps", "ps1"],
  ["Prisma", "prisma"],
  ["Prolog", "prolog"],
  ["Protocol Buffer 3", "proto"],
  ["Pug", "pug", "jade"],
  ["Puppet", "puppet"],
  ["PureScript", "purescript"],
  ["Python", "python", "py"],
  ["R", "r"],
  ["Raku", "raku", "perl6"],
  ["ASP.NET Razor", "razor"],
  ["Windows Registry Script", "reg"],
  ["Rel", "rel"],
  ["RISC-V", "riscv"],
  ["reStructuredText", "rst"],
  ["Ruby", "ruby", "rb"],
  ["Rust", "rust", "rs"],
  ["SAS", "sas"],
  ["Sass", "sass"],
  ["Scala", "scala"],
  ["Scheme", "scheme"],
  ["SCSS", "scss"],
  ["ShaderLab", "shaderlab", "shader"],
  ["Shell", "shellscript", "bash", "sh", "zsh"],
  ["Shell Session", "shellsession", "console"],
  ["Smalltalk", "smalltalk"],
  ["Solidity", "solidity"],
  ["SPARQL", "sparql"],
  ["Splunk Query Language", "splunk", "spl"],
  ["SQL", "sql"],
  ["SSH Config", "ssh-config"],
  ["Stata", "stata"],
  ["Stylus", "stylus", "st"],
  ["Svelte", "svelte"],
  ["Swift", "swift"],
  ["SystemVerilog", "system-verilog"],
  ["Tasl", "tasl"],
  ["Tcl", "tcl"],
  ["Terraform", "terraform", "tft", "tfvars"],
  ["TeX", "tex"],
  ["TOML", "toml"],
  ["TSV", "tsv"],
  ["TSX", "tsx"],
  ["Turtle", "turtle"],
  ["Twig", "twig"],
  ["TypeScript", "typescript", "ts"],
  ["Typst", "typst", "typ"],
  ["V", "v"],
  ["Visual Basic", "vb", "cmd"],
  ["Verilog", "verilog"],
  ["VHDL", "vhdl"],
  ["Vim Script", "viml", "vim", "vimscript"],
  ["Vue", "vue"],
  ["Vue HTML", "vue-html"],
  ["Vyper", "vyper", "vy"],
  ["WebAssembly", "wasm"],
  ["Wenyan", "wenyan"],
  ["WGSL", "wgsl"],
  ["Wolfram", "wolfram", "wl"],
  ["XML", "xml"],
  ["XSL", "xsl"],
  ["YAML", "yaml", "yml"],
  ["ZenScript", "zenscript"],
  ["Zig", "zig"]
];

const SHIKI_BUNDLED_THEMES : {value: BundledTheme, backgroundColor: string}[] = [
  { "value": "andromeeda", "backgroundColor": "#23262E" },
  { "value": "aurora-x", "backgroundColor": "#07090F" },
  { "value": "ayu-dark", "backgroundColor": "#0b0e14" },
  { "value": "catppuccin-frappe", "backgroundColor": "#303446" },
  { "value": "catppuccin-latte", "backgroundColor": "#eff1f5" },
  { "value": "catppuccin-macchiato", "backgroundColor": "#24273a" },
  { "value": "catppuccin-mocha", "backgroundColor": "#1e1e2e" },
  { "value": "dark-plus", "backgroundColor": "#1E1E1E" },
  { "value": "dracula", "backgroundColor": "#282A36" },
  { "value": "dracula-soft", "backgroundColor": "#282A36" },
  { "value": "github-dark", "backgroundColor": "#24292e" },
  { "value": "github-dark-default", "backgroundColor": "#0d1117" },
  { "value": "github-dark-dimmed", "backgroundColor": "#22272e" },
  { "value": "github-light", "backgroundColor": "#fff" },
  { "value": "github-light-default", "backgroundColor": "#ffffff" },
  { "value": "houston", "backgroundColor": "#17191e" },
  { "value": "light-plus", "backgroundColor": "#FFFFFF" },
  { "value": "material-theme", "backgroundColor": "#263238" },
  { "value": "material-theme-darker", "backgroundColor": "#212121" },
  { "value": "material-theme-lighter", "backgroundColor": "#FAFAFA" },
  { "value": "material-theme-ocean", "backgroundColor": "#0F111A" },
  { "value": "material-theme-palenight", "backgroundColor": "#292D3E" },
  { "value": "min-dark", "backgroundColor": "#1f1f1f" },
  { "value": "min-light", "backgroundColor": "#ffffff" },
  { "value": "monokai", "backgroundColor": "#272822" },
  { "value": "night-owl", "backgroundColor": "#011627" },
  { "value": "nord", "backgroundColor": "#2e3440ff" },
  { "value": "one-dark-pro", "backgroundColor": "#282c34" },
  { "value": "poimandres", "backgroundColor": "#1b1e28" },
  { "value": "red", "backgroundColor": "#390000" },
  { "value": "rose-pine", "backgroundColor": "#191724" },
  { "value": "rose-pine-dawn", "backgroundColor": "#faf4ed" },
  { "value": "rose-pine-moon", "backgroundColor": "#232136" },
  { "value": "slack-dark", "backgroundColor": "#222222" },
  { "value": "slack-ochin", "backgroundColor": "#FFF" },
  { "value": "solarized-dark", "backgroundColor": "#002B36" },
  { "value": "solarized-light", "backgroundColor": "#FDF6E3" },
  { "value": "synthwave-84", "backgroundColor": "#262335" },
  { "value": "tokyo-night", "backgroundColor": "#1a1b26" },
  { "value": "vesper", "backgroundColor": "#101010" },
  { "value": "vitesse-black", "backgroundColor": "#000" },
  { "value": "vitesse-dark", "backgroundColor": "#121212" },
  { "value": "vitesse-light", "backgroundColor": "#ffffff" }
];

export const SHIKI_THEMES : {value: BundledTheme, label: string}[] = SHIKI_BUNDLED_THEMES.map(theme => ({
  value: theme.value as BundledTheme,
  label: theme.value.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}));

let SHIKI_THEMES_BACKGROUND_COLORS_PRE = new Map<BundledTheme, string>();
for (const theme of SHIKI_BUNDLED_THEMES) {
  SHIKI_THEMES_BACKGROUND_COLORS_PRE.set(theme.value as BundledTheme, theme.backgroundColor);
}
export const SHIKI_THEMES_BACKGROUND_COLORS = SHIKI_THEMES_BACKGROUND_COLORS_PRE;

let LANGUAGES_MAP_PRE = new Map<string, {value: BundledLanguage, preview: string}>();

// Loop through each language pair
for (let value_set of languages) {
  // Strip non-alphanumeric characters and force to lowercase
	for (let value of value_set) {
		const cleanKey = value.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
		// Add the cleaned key-value pair to the map

		for (let i = 1; i < cleanKey.length-1; i++) {
			if (LANGUAGES_MAP_PRE.has(cleanKey.slice(0, i))) {
				continue;
			}
			LANGUAGES_MAP_PRE.set(cleanKey.slice(0, i), {value: value_set[1] as BundledLanguage, preview: value_set[0]});
		}
		LANGUAGES_MAP_PRE.set(cleanKey, {value: value_set[1] as BundledLanguage, preview: value_set[0]});
	}
}

const LANGUAGES_MAP = LANGUAGES_MAP_PRE;

export function getLanguage(lang: string) : {value: BundledLanguage | "text", preview: string} {
	const langSimple = (lang || "").replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
	// console.log(LANGUAGES_MAP);
	// console.log("Searching for", langSimple, "got:", LANGUAGES_MAP.get(langSimple));
	return LANGUAGES_MAP.get(langSimple) || {value: "text", preview: "Text"};
}

export async function highlight(code: string, theme: BundledTheme, lang: string) {
	const html = await codeToHtml(code, {
		lang: lang as BundledLanguage,
		theme: theme,
		// colorReplacements: {
		// 	"#1a1b26": "#00000000"
		// },
	});
  return html.replace(/^<pre[^>]*>/i, '<pre>');
}

const test_code = `
print("Hello, World!")
`

export async function get_all_language_backgrounds() {
  const backgrounds = new Map<string, string>();
  let background_entries = new Array<{value: BundledTheme, backgroundColor: string}>();
  
  for (const e of SHIKI_BUNDLED_THEMES) {
    const html = await codeToHtml("test", {
      lang: "python",
      theme: e.value,
      // colorReplacements: {
      //   "#1a1b26": "#00000000"
      // },
    })
    const background = html.match(/^<pre[^>]*>/i);
    const backgroundColor = background?background[0].match(/background\-color\:\#[a-fA-F0-9]+/i):undefined;
    if (backgroundColor) {
      const color_entry = backgroundColor[0].split(":")[1];
      console.log(color_entry);
      // backgrounds.set(e.value, background[1]);
      background_entries.push({value: e.value, backgroundColor: color_entry});
    }
  }
  // const languageBackgrounds = Object.fromEntries(backgrounds) as { [key: BundledLanguage]: string };
  // return languageBackgrounds;
  console.log("Shiki background values:", background_entries);

  return backgrounds;
}