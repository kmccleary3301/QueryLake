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

const REGISTRY_THEMES = new Map<string, object>();

for (const theme of themes) {
  REGISTRY_THEMES.set(theme.name, theme.cssVars);
}

type themeType = {
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

const DEFAULT_THEME = REGISTRY_THEMES.get('default') as {light: themeType, dark: themeType};

const Context = createContext<{
	background: string;
	setBackground: Dispatch<SetStateAction<string>>;
  foreground: string;
	setForeground: Dispatch<SetStateAction<string>>;
  card: string;
  setCard: Dispatch<SetStateAction<string>>;
  cardForeground: string;
  setCardForeground: Dispatch<SetStateAction<string>>;
  popover: string;
  setPopover: Dispatch<SetStateAction<string>>;
  popoverForeground: string;
  setPopoverForeground: Dispatch<SetStateAction<string>>;
  primary: string;
  setPrimary: Dispatch<SetStateAction<string>>;
  primaryForeground: string;
  setPrimaryForeground: Dispatch<SetStateAction<string>>;
  secondary: string;
  setSecondary: Dispatch<SetStateAction<string>>;
  secondaryForeground: string;
  setSecondaryForeground: Dispatch<SetStateAction<string>>;
  muted: string;
  setMuted: Dispatch<SetStateAction<string>>;
  mutedForeground: string;
  setMutedForeground: Dispatch<SetStateAction<string>>;
  accent: string;
  setAccent: Dispatch<SetStateAction<string>>;
  accentForeground: string;
  setAccentForeground: Dispatch<SetStateAction<string>>;
  destructive: string;
  setDestructive: Dispatch<SetStateAction<string>>;
  destructiveForeground: string;
  setDestructiveForeground: Dispatch<SetStateAction<string>>;
  border: string;
  setBorder: Dispatch<SetStateAction<string>>;
  input: string;
  setInput: Dispatch<SetStateAction<string>>;
}>({
	background: DEFAULT_THEME.dark.background,
  setBackground: () => DEFAULT_THEME.dark.background,
  foreground: DEFAULT_THEME.dark.foreground,
  setForeground: () => DEFAULT_THEME.dark.foreground,
  card: DEFAULT_THEME.dark.card,
  setCard: () => DEFAULT_THEME.dark.card,
  cardForeground: DEFAULT_THEME.dark.cardForeground,
  setCardForeground: () => DEFAULT_THEME.dark.cardForeground,
  popover: DEFAULT_THEME.dark.popover,
  setPopover: () => DEFAULT_THEME.dark.popover,
  popoverForeground: DEFAULT_THEME.dark.popoverForeground,
  setPopoverForeground: () => DEFAULT_THEME.dark.popoverForeground,
  primary: DEFAULT_THEME.dark.primary,
  setPrimary: () => DEFAULT_THEME.dark.primary,
  primaryForeground: DEFAULT_THEME.dark.primaryForeground,
  setPrimaryForeground: () => DEFAULT_THEME.dark.primaryForeground,
  secondary: DEFAULT_THEME.dark.secondary,
  setSecondary: () => DEFAULT_THEME.dark.secondary,
  secondaryForeground: DEFAULT_THEME.dark.secondaryForeground,
  setSecondaryForeground: () => DEFAULT_THEME.dark.secondaryForeground,
  muted: DEFAULT_THEME.dark.muted,
  setMuted: () => DEFAULT_THEME.dark.muted,
  mutedForeground: DEFAULT_THEME.dark.mutedForeground,
  setMutedForeground: () => DEFAULT_THEME.dark.mutedForeground,
  accent: DEFAULT_THEME.dark.accent,
  setAccent: () => DEFAULT_THEME.dark.accent,
  accentForeground: DEFAULT_THEME.dark.accentForeground,
  setAccentForeground: () => DEFAULT_THEME.dark.accentForeground,
  destructive: DEFAULT_THEME.dark.destructive,
  setDestructive: () => DEFAULT_THEME.dark.destructive,
  destructiveForeground: DEFAULT_THEME.dark.destructiveForeground,
  setDestructiveForeground: () => DEFAULT_THEME.dark.destructiveForeground,
  border: DEFAULT_THEME.dark.border,
  setBorder: () => DEFAULT_THEME.dark.border,
  input: DEFAULT_THEME.dark.input,
  setInput: () => DEFAULT_THEME.dark.input,
});

export const ThemeProvider = ({children}: PropsWithChildren<{}>) => {
	const [background_i, set_background_i] = useState(DEFAULT_THEME.dark.background);
  const [foreground_i, set_foreground_i] = useState(DEFAULT_THEME.dark.foreground);
  const [card_i, set_card_i] = useState(DEFAULT_THEME.dark.card);
  const [card_foreground_i, set_card_foreground_i] = useState(DEFAULT_THEME.dark.cardForeground);
  const [popover_i, set_popover_i] = useState(DEFAULT_THEME.dark.popover);
  const [popover_foreground_i, set_popover_foreground_i] = useState(DEFAULT_THEME.dark.popoverForeground);
  const [primary_i, set_primary_i] = useState(DEFAULT_THEME.dark.primary);
  const [primary_foreground_i, set_primary_foreground_i] = useState(DEFAULT_THEME.dark.primaryForeground);
  const [secondary_i, set_secondary_i] = useState(DEFAULT_THEME.dark.secondary);
  const [secondary_foreground_i, set_secondary_foreground_i] = useState(DEFAULT_THEME.dark.secondaryForeground);
  const [muted_i, set_muted_i] = useState(DEFAULT_THEME.dark.muted);
  const [muted_foreground_i, set_muted_foreground_i] = useState(DEFAULT_THEME.dark.mutedForeground);
  const [accent_i, set_accent_i] = useState(DEFAULT_THEME.dark.accent);
  const [accent_foreground_i, set_accent_foreground_i] = useState(DEFAULT_THEME.dark.accentForeground);
  const [destructive_i, set_destructive_i] = useState(DEFAULT_THEME.dark.destructive);
  const [destructive_foreground_i, set_destructive_foreground_i] = useState(DEFAULT_THEME.dark.destructiveForeground);
  const [border_i, set_border_i] = useState(DEFAULT_THEME.dark.border);
  const [input_i, set_input_i] = useState(DEFAULT_THEME.dark.input);

  useEffect(() => {
    const theme = REGISTRY_THEMES.get('default') as {light: themeType, dark: themeType};
    set_background_i(theme.dark.background);
    set_foreground_i(theme.dark.foreground);
    set_card_i(theme.dark.card);
    set_card_foreground_i(theme.dark.cardForeground);
    set_popover_i(theme.dark.popover);
    set_popover_foreground_i(theme.dark.popoverForeground);
    // set_primary_i(theme.dark.primary);
    set_primary_i(theme.dark.primary);
    set_primary_foreground_i(theme.dark.primaryForeground);
    set_secondary_i(theme.dark.secondary);
    set_secondary_foreground_i(theme.dark.secondaryForeground);
    set_muted_i(theme.dark.muted);
    set_muted_foreground_i(theme.dark.mutedForeground);
    set_accent_i(theme.dark.accent);
    set_accent_foreground_i(theme.dark.accentForeground);
    set_destructive_i(theme.dark.destructive);
    set_destructive_foreground_i(theme.dark.destructiveForeground);
    set_border_i(theme.dark.border);
    set_input_i(theme.dark.input);
  })

	return (
		<Context.Provider value={{ 
			background: background_i,
      setBackground: set_background_i,
      foreground: foreground_i,
      setForeground: set_foreground_i,
      card: card_i,
      setCard: set_card_i,
      cardForeground: card_foreground_i,
      setCardForeground: set_card_foreground_i,
      popover: popover_i,
      setPopover: set_popover_i,
      popoverForeground: popover_foreground_i,
      setPopoverForeground: set_popover_foreground_i,
      primary: primary_i,
      setPrimary: set_primary_i,
      primaryForeground: primary_foreground_i,
      setPrimaryForeground: set_primary_foreground_i,
      secondary: secondary_i,
      setSecondary: set_secondary_i,
      secondaryForeground: secondary_foreground_i,
      setSecondaryForeground: set_secondary_foreground_i,
      muted: muted_i,
      setMuted: set_muted_i,
      mutedForeground: muted_foreground_i,
      setMutedForeground: set_muted_foreground_i,
      accent: accent_i,
      setAccent: set_accent_i,
      accentForeground: accent_foreground_i,
      setAccentForeground: set_accent_foreground_i,
      destructive: destructive_i,
      setDestructive: set_destructive_i,
      destructiveForeground: destructive_foreground_i,
      setDestructiveForeground: set_destructive_foreground_i,
      border: border_i,
      setBorder: set_border_i,
      input: input_i,
      setInput: set_input_i,
		}}>
      <div style={{
        '--background': background_i,
        '--foreground': foreground_i,
        '--card': card_i,
        '--card-foreground': card_foreground_i,
        '--popover': popover_i,
        '--popover-foreground': popover_foreground_i,
        '--primary': primary_i,
        '--primary-foreground': primary_foreground_i,
        '--secondary': secondary_i,
        '--secondary-foreground': secondary_foreground_i,
        '--muted': muted_i,
        '--muted-foreground': muted_foreground_i,
        '--accent': accent_i,
        '--accent-foreground': accent_foreground_i,
        '--destructive': destructive_i,
        '--destructive-foreground': destructive_foreground_i,
        '--border': border_i,
        '--input': input_i,
      } as React.CSSProperties}>
			  {children}
      </div>
		</Context.Provider>
	);
};

export const useThemeContextAction = () => {
	return useContext(Context);
};


// export function ThemeWrapper({children}:{children: React.ReactNode}) {
//   const {
//     background,
//     foreground,
//     card,
//     cardForeground,
//     popover,
//     popoverForeground,
//     primary,
//     primaryForeground,
//     secondary,
//     secondaryForeground,
//     muted,
//     mutedForeground,
//     accent,
//     accentForeground,
//     destructive,
//     destructiveForeground,
//     border,
//     input,
//   } = useThemeContextAction();

//   return (
//     <ThemeProvider>
//       <div style={{
//         '--background': background,
//         '--foreground': foreground,
//         '--card': card,
//         '--card-foreground': cardForeground,
//         '--popover': popover,
//         '--popover-foreground': popoverForeground,
//         '--primary': primary,
//         '--primary-foreground': primaryForeground,
//         '--secondary': secondary,
//         '--secondary-foreground': secondaryForeground,
//         '--muted': muted,
//         '--muted-foreground': mutedForeground,
//         '--accent': accent,
//         '--accent-foreground': accentForeground,
//         '--destructive': destructive,
//         '--destructive-foreground': destructiveForeground,
//         '--border': border,
//         '--input': input,
//       } as React.CSSProperties}>
//         {children}
//       </div>
//     </ThemeProvider>
//   );
// }