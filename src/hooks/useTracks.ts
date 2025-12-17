import { Track } from "../components/MediaLibrary";

export type TrackTiming = {
  id: string;
  title: string;
  artist: string;
  startTime: number;
  endTime: number;
  duration: number;
};

export type ConcatenatedPlaylist = {
  enabled: boolean;
  file: string;
  tracks: TrackTiming[];
  totalDuration: number;
};

export type AppConfig = {
  tracks: Track[];
  headerMessage?: string;
  buildDatetime?: string;
  buildHash?: string;
  concatenatedPlaylist?: ConcatenatedPlaylist;
};

const BASE_URL = import.meta.env.BASE_URL || "/";

function withBase(path: string): string {
  // If config contains absolute-root paths like "/songs/..", rewrite to "/v2/songs/.."
  // BASE_URL always ends with "/" in Vite.
  if (!path) return path;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const trimmed = path.replace(/^\//, "");
  return `${BASE_URL}${trimmed}`;
}

// Load tracks from the generated appConfig.json
// This file is generated from lit_up_config.yaml during the build process
export const useTracks = async (): Promise<Track[]> => {
  try {
    const response = await fetch(withBase("appConfig.json"));
    if (!response.ok) {
      throw new Error(`Failed to load app config: ${response.statusText}`);
    }
    const config: AppConfig = await response.json();
    return (config.tracks || []).map((t) => ({
      ...t,
      src: withBase(t.src),
      cover: withBase(t.cover),
    }));
  } catch (error) {
    console.error("Error loading tracks from appConfig.json:", error);
    // Fallback to empty array if config loading fails
    return [];
  }
};

export function getAppConfigUrl(): string {
  return withBase("appConfig.json");
}

export function withAppBase(path: string): string {
  return withBase(path);
}
