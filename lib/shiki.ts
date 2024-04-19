import type { BundledLanguage, BundledTheme } from 'shiki'
import { codeToHtml } from 'shiki'

export async function highlight(code: string, theme: BundledTheme, lang: string) {

	const html = await codeToHtml(code, {
		lang: lang as BundledLanguage,
		theme: theme,
		colorReplacements: {
			"#1a1b26": "#00000000"
		},

	})
  return html.replace(/^<pre[^>]*>/i, '<pre>');
}