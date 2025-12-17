import React, { useState, useEffect } from "react";

interface VersionPickerProps {
  className?: string;
}

const VersionPicker: React.FC<VersionPickerProps> = ({ className = "" }) => {
  const availableVersions = ["v1", "v2"];

  // Extract version from current URL path
  const getCurrentVersion = (): string => {
    const pathname = window.location.pathname;
    // Path will be like /v1/ or /v2/, extract the version
    const match = pathname.match(/^\/(v\d+)\//);
    if (match && match[1]) {
      return match[1];
    }
    // Fallback: try to get from BASE_URL
    const baseUrl = import.meta.env.BASE_URL || "/";
    const baseMatch = baseUrl.match(/\/(v\d+)\//);
    if (baseMatch && baseMatch[1]) {
      return baseMatch[1];
    }
    // Default fallback
    return "v1";
  };

  const [version, setVersion] = useState<string>(getCurrentVersion());

  // Update version if pathname changes (e.g., browser back/forward)
  useEffect(() => {
    const handleLocationChange = () => {
      setVersion(getCurrentVersion());
    };

    // Listen for popstate (back/forward navigation)
    window.addEventListener("popstate", handleLocationChange);

    return () => {
      window.removeEventListener("popstate", handleLocationChange);
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const next = e.target.value;
    window.location.href = `/${next}/`;
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <label htmlFor="version-picker" className="text-sm opacity-80">
        Version
      </label>
      <select
        id="version-picker"
        value={version}
        onChange={handleChange}
        className={`text-sm bg-[var(--theme-tertiary)] border-2 border-[var(--theme-secondary)] rounded px-2 py-1 outline-none cursor-pointer`}
      >
        {availableVersions.map((version) => (
          <option key={version} value={version}>
            {version}
          </option>
        ))}
      </select>
    </div>
  );
};

export default VersionPicker;
