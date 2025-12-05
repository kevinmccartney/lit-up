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
  buildDatetime?: string;
  buildHash?: string;
  concatenatedPlaylist?: ConcatenatedPlaylist;
};

// Load tracks from the generated appConfig.json
// This file is generated from song_list.yaml during the build process
export const useTracks = async (): Promise<Track[]> => {
  try {
    const response = await fetch("/appConfig.json");
    if (!response.ok) {
      throw new Error(`Failed to load app config: ${response.statusText}`);
    }
    const config: AppConfig = await response.json();
    return config.tracks || [];
  } catch (error) {
    console.error("Error loading tracks from appConfig.json:", error);
    // Fallback to empty array if config loading fails
    return [];
  }
};
