import type { BundledLanguage, Highlighter} from 'shiki'
import { codeToTokens, codeToHtml } from 'shiki'

let highlighter: Highlighter
export async function highlight(code: string, theme: string, lang: string) {
  
	// console.log('highlighting code with', lang);
	// if (!highlighter) {
  //   highlighter = await getHighlighter({
  //     langs: [lang],
  //     themes: []
  //   })
  // }

  // const tokens = highlighter.codeToTokensBase(code, {
  //   includeExplanation: true,
	// 	lang: lang as BundledLanguage
  // })
	
  // // const html = renderToHtml(tokens, { bg: 'transparent' })

  // // return html
	// return tokens

	const html = await codeToHtml(code, {
		lang: lang as BundledLanguage,
		// includeExplanation: true,
		themes: {
			light: 'tokyo-night',
			dark: 'vitesse-black',
		},
	})

	// return tokens

	// const html = renderToHtml(tokens, { bg: 'transparent' })

  return html
}