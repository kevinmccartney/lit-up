import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

interface ThemePickerProps {
  className?: string;
}

const ThemePicker: React.FC<ThemePickerProps> = ({ className = '' }) => {
  const { theme, updateTheme, isLoaded, themes } = useTheme();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const next = e.target.value as keyof typeof themes;
    updateTheme(next);
  };

  // Don't render until theme is loaded to prevent hydration mismatch
  if (!isLoaded) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <label htmlFor="theme-picker" className="text-sm opacity-80">
          Theme
        </label>
        <select
          id="theme-picker"
          disabled
          className="text-sm bg-[var(--theme-tertiary)] border-2 border-[var(--theme-secondary)] rounded px-2 py-1 outline-none cursor-pointer opacity-50"
        >
          <option>Loading...</option>
        </select>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <label htmlFor="theme-picker" className="text-sm opacity-80">
        Theme
      </label>
      <select
        id="theme-picker"
        value={theme.name}
        onChange={handleChange}
        className={`text-sm bg-[var(--theme-tertiary)] border-2 border-[var(--theme-secondary)] rounded px-2 py-1 outline-none cursor-pointer`}
      >
        {Object.entries(themes).map(([key, theme]) => (
          <option key={key} value={key}>
            {theme.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ThemePicker;
