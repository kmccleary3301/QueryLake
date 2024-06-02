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

const REGISTRY_THEMES_PRE = new Map<string, object>();

for (const theme of themes) {
  REGISTRY_THEMES_PRE.set(theme.name, theme.cssVars);
}

export const REGISTRY_THEMES = REGISTRY_THEMES_PRE;
export const COMBOBOX_THEMES : {label : string, value: string}[] = themes.map((theme) => ({
  label: theme.label, 
  value: theme.name
}));


export type themeType = {
  "theme-one": string,
  background: string;
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

const DEFAULT_THEME_ID = "openai";
const DEFAULT_THEME = REGISTRY_THEMES.get(DEFAULT_THEME_ID) as {light: themeType, dark: themeType};

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
    const theme = REGISTRY_THEMES.get(DEFAULT_THEME_ID) as {light: themeType, dark: themeType};
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