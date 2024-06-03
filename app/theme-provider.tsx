// ThemeProvider.tsx
'use client';
import {
	Dispatch,
	PropsWithChildren,
	SetStateAction,
	createContext,
	useContext,
	useEffect,
	useState,
} from 'react';
import { themes } from '@/registry/themes';
import exp from 'constants';

const REGISTRY_THEMES_PRE = new Map<string, object>();

for (const theme of themes) {
  REGISTRY_THEMES_PRE.set(theme.name, theme.cssVars);
}

export const REGISTRY_THEMES_MAP = REGISTRY_THEMES_PRE;
export const COMBOBOX_THEMES : {label : string, value: string}[] = themes.map((theme) => ({
  label: theme.label, 
  value: theme.name
}));
// expport const REGISTRY




export type themeType = {
  "theme-one": string,
  background: string;
  "background-sidebar": string;
  foreground: string;
  card: string;
  cardForeground: string;
  popover: string;
  popoverForeground: string;
  primary: string;
  primaryForeground: string;
  secondary: string;
  secondaryForeground: string;
  muted: string;
  mutedForeground: string;
  accent: string;
  accentForeground: string;
  destructive: string;
  destructiveForeground: string;
  border: string;
  input: string;
};

export type registryThemeEntry = {label: string, mode: "light" | "dark", value: string, stylesheet:themeType}

export const REGISTRY_THEMES : registryThemeEntry[] = Array(themes.length*2).fill(0).map((_, i) => {
  const themes_i = themes[Math.floor(i / 2)];
  let result = {...(i % 2 == 0)?themes_i.cssVars.light:themes_i.cssVars.dark, radius: 2}
  if (result.radius) delete (result as {radius: unknown})?.radius;
  return {
    label: `${themes_i.label} (${(i % 2 == 0)?"Light":"Dark"})`,
    mode: (i % 2 == 0)?"light":"dark",
    value: themes_i.name,
    stylesheet: result
  };
}) as unknown as registryThemeEntry[];

// [...themes.map((theme) => {
//   let result = {...theme.cssVars.light, radius: 2}
//   if (result.radius) delete (result as {radius: unknown})?.radius;
//   return {
//     label: `${theme.label} (Light)`,
//     mode: "light",
//     value: theme.name,
//     stylesheet: result
//   };
// }), ...themes.map((theme) => {
//   let result = {...theme.cssVars.light, radius: 2}
//   if (result.radius) delete (result as {radius: unknown})?.radius;
//   return {
//     label: `${theme.label} (Dark)`,
//     mode: "dark",
//     value: theme.name,
//     stylesheet: result
//   };
// })] as unknown as registryThemeEntry[];

// export const REGISTRY_THEMES : registryThemeEntry[] = Array(REGISTRY_THEMES_PRE_2.length).fill(0).map((_, i) => {
//   const index = Math.floor(i / 2) + ((i % 2 === 0) ? themes.length : 0);
//   return REGISTRY_THEMES_PRE_2[index];
// });

const DEFAULT_THEME_ID = "openai";
const DEFAULT_THEME = REGISTRY_THEMES_MAP.get(DEFAULT_THEME_ID) as {light: themeType, dark: themeType};

const Context = createContext<{
	theme: themeType;
  setTheme: Dispatch<SetStateAction<themeType>>;
}>({
	theme: DEFAULT_THEME.dark,
  setTheme: () => {},
});

export const StateThemeProvider = ({children}: PropsWithChildren<{}>) => {
	const [theme_i, set_theme_i] = useState(DEFAULT_THEME.dark);

  useEffect(() => {
    const theme = REGISTRY_THEMES_MAP.get(DEFAULT_THEME_ID) as {light: themeType, dark: themeType};
    set_theme_i(theme.dark);
  }, []);

	return (
		<Context.Provider value={{ 
			theme: theme_i,
      setTheme: set_theme_i,
		}}>
      <div style={{
      } as React.CSSProperties}>
			  {children}
      </div>
		</Context.Provider>
	);
};

export const useThemeContextAction = () => {
	return useContext(Context);
};

export function ThemeProviderWrapper({children}:{children: React.ReactNode}) {
  const {
    theme
  } = useThemeContextAction();

  return (
    // <ThemeProvider>
      <div style={{
        '--theme-one': theme["theme-one"],
        '--background': theme.background,
        '--background-sidebar': theme["background-sidebar"],
        '--foreground': theme.foreground,
        '--card': theme.card,
        '--card-foreground': theme.cardForeground,
        '--popover': theme.popover,
        '--popover-foreground': theme.popoverForeground,
        '--primary': theme.primary,
        '--primary-foreground': theme.primaryForeground,
        '--secondary': theme.secondary,
        '--secondary-foreground': theme.secondaryForeground,
        '--muted': theme.muted,
        '--muted-foreground': theme.mutedForeground,
        '--accent': theme.accent,
        '--accent-foreground': theme.accentForeground,
        '--destructive': theme.destructive,
        '--destructive-foreground': theme.destructiveForeground,
        '--border': theme.border,
        '--input': theme.input,
      } as React.CSSProperties}>
        {children}
      </div>
    // </ThemeProvider>
  );
}