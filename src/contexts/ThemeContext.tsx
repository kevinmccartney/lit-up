import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { themes as themesConstants } from "../constants";

export type ThemeKey = "coral" | "magenta" | "pink" | "teal" | "cyan";
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
    name: "coral",
  },
  magenta: {
    primary: themesConstants.magenta.primary,
    secondary: themesConstants.magenta.secondary,
    tertiary: themesConstants.magenta.tertiary,
    name: "magenta",
  },
  pink: {
    primary: themesConstants.pink.primary,
    secondary: themesConstants.pink.secondary,
    tertiary: themesConstants.pink.tertiary,
    name: "pink",
  },
  teal: {
    primary: themesConstants.teal.primary,
    secondary: themesConstants.teal.secondary,
    tertiary: themesConstants.teal.tertiary,
    name: "teal",
  },
  cyan: {
    primary: themesConstants.cyan.primary,
    secondary: themesConstants.cyan.secondary,
    tertiary: themesConstants.cyan.tertiary,
    name: "cyan",
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

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(themes.coral);
  const [primaryColor, setPrimaryColor] = useState<string>(
    themes.coral.primary
  );
  const [secondaryColor, setSecondaryColor] = useState<string>(
    themes.coral.secondary
  );
  const [tertiaryColor, setTertiaryColor] = useState<string>(
    themes.coral.tertiary
  );
  const [isLoaded, setIsLoaded] = useState(false);

  // Load theme from localStorage on mount
  useEffect(() => {
    const storedTheme = localStorage.getItem("app-theme");
    const savedTheme: Theme =
      (storedTheme && JSON.parse(storedTheme)) || themes.coral;
    setTheme(savedTheme);
    setPrimaryColor(savedTheme.primary);
    setSecondaryColor(savedTheme.secondary);
    setTertiaryColor(savedTheme.tertiary);
    document.documentElement.setAttribute("data-theme", savedTheme.name);
    setIsLoaded(true);
  }, []);

  // Update theme and persist to localStorage
  const updateTheme = (themeKey: ThemeKey) => {
    const newTheme = themes[themeKey];
    setTheme(newTheme);
    setPrimaryColor(newTheme.primary);
    setSecondaryColor(newTheme.secondary);
    setTertiaryColor(newTheme.tertiary);
    localStorage.setItem("app-theme", JSON.stringify(newTheme));
    document.documentElement.setAttribute("data-theme", newTheme.name);
  };

  const value: ThemeContextType = {
    theme,
    updateTheme,
    isLoaded,
    primaryColor,
    secondaryColor,
    tertiaryColor,
    themes,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
