import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { themes as themesConstants } from '../constants';

export type ThemeKey = 'coral' | 'magenta' | 'pink' | 'teal' | 'cyan';
export type Theme = {
  primary: string;
  secondary: string;
  tertiary: string;
  name: ThemeKey;
};

const themes: Record<ThemeKey, Theme> = {
  coral: {
    primary: themesConstants.coral.primary,
    secondary: themesConstants.coral.secondary,
    tertiary: themesConstants.coral.tertiary,
    name: 'coral',
  },
  magenta: {
    primary: themesConstants.magenta.primary,
    secondary: themesConstants.magenta.secondary,
    tertiary: themesConstants.magenta.tertiary,
    name: 'magenta',
  },
  pink: {
    primary: themesConstants.pink.primary,
    secondary: themesConstants.pink.secondary,
    tertiary: themesConstants.pink.tertiary,
    name: 'pink',
  },
  teal: {
    primary: themesConstants.teal.primary,
    secondary: themesConstants.teal.secondary,
    tertiary: themesConstants.teal.tertiary,
    name: 'teal',
  },
  cyan: {
    primary: themesConstants.cyan.primary,
    secondary: themesConstants.cyan.secondary,
    tertiary: themesConstants.cyan.tertiary,
    name: 'cyan',
  },
};

interface ThemeContextType {
  theme: Theme;
  updateTheme: (newTheme: ThemeKey) => void;
  isLoaded: boolean;
  primaryColor: string;
  secondaryColor: string;
  tertiaryColor: string;
  themes: Record<ThemeKey, Theme>;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function isThemeKey(value: unknown): value is ThemeKey {
  return (
    value === 'coral' ||
    value === 'magenta' ||
    value === 'pink' ||
    value === 'teal' ||
    value === 'cyan'
  );
}

function parseStoredThemeKey(stored: string | null): ThemeKey | null {
  if (!stored) return null;

  // New format: just store the key, e.g. "coral"
  if (isThemeKey(stored)) return stored;

  // Backward compatibility: old format was JSON stringified Theme object
  try {
    const parsed = JSON.parse(stored) as unknown;
    if (parsed && typeof parsed === 'object' && 'name' in parsed) {
      const maybeName = (parsed as { name?: unknown }).name;
      if (isThemeKey(maybeName)) return maybeName;
    }
  } catch {
    // ignore malformed storage values
  }

  return null;
}

export function ThemeProvider({ children }: { children: ReactNode }): JSX.Element {
  const [themeKey, setThemeKey] = useState<ThemeKey>('coral');
  const [isLoaded, setIsLoaded] = useState(false);

  const theme = useMemo(() => themes[themeKey], [themeKey]);
  const primaryColor = theme.primary;
  const secondaryColor = theme.secondary;
  const tertiaryColor = theme.tertiary;

  // Load theme from localStorage on mount
  useEffect(() => {
    const storedTheme = localStorage.getItem('app-theme');
    const savedThemeKey = parseStoredThemeKey(storedTheme) ?? 'coral';
    setThemeKey(savedThemeKey);
    document.documentElement.setAttribute('data-theme', savedThemeKey);
    setIsLoaded(true);
  }, []);

  // Update theme and persist to localStorage
  const updateTheme = useCallback((themeKey: ThemeKey) => {
    setThemeKey(themeKey);
    localStorage.setItem('app-theme', themeKey);
    document.documentElement.setAttribute('data-theme', themeKey);
  }, []);

  const value = useMemo<ThemeContextType>(() => {
    return {
      theme,
      updateTheme,
      isLoaded,
      primaryColor,
      secondaryColor,
      tertiaryColor,
      themes,
    };
  }, [isLoaded, primaryColor, secondaryColor, tertiaryColor, theme, updateTheme]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
