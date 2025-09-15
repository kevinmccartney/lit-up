import React, { useEffect, useState } from "react";

type ThemeKey = "default" | "coral" | "pink" | "cyan";

const themeLabels: Record<ThemeKey, string> = {
  default: "Default",
  coral: "Coral",
  pink: "Pink",
  cyan: "Cyan",
};

interface ThemePickerProps {
  className?: string;
}

const ThemePicker: React.FC<ThemePickerProps> = ({ className = "" }) => {
  const [theme, setTheme] = useState<ThemeKey>("default");

  useEffect(() => {
    const saved = (localStorage.getItem("app-theme") as ThemeKey) || "default";
    setTheme(saved);
    document.documentElement.setAttribute("data-theme", saved);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const next = e.target.value as ThemeKey;
    setTheme(next);
    localStorage.setItem("app-theme", next);
    document.documentElement.setAttribute("data-theme", next);
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <label htmlFor="theme-picker" className="text-sm opacity-80">
        Theme
      </label>
      <select
        id="theme-picker"
        value={theme}
        onChange={handleChange}
        className="text-sm bg-white/30 border border-palette-coral rounded px-2 py-1 outline-none cursor-pointer"
      >
        {Object.entries(themeLabels).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ThemePicker;
