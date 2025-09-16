import React from "react";
import cn from "classnames";
import { AudioLines } from "lucide-react";

export interface Track {
  id: string;
  src: string;
  title: string;
  artist: string;
  duration: string;
  cover: string;
  isSecret: boolean;
}

interface MediaLibraryProps {
  tracks: Track[];
  onTrackSelect: (track: Track) => void;
  selectedTrack?: Track | null;
  className?: string;
  isPlaying?: boolean;
  onPlayPause?: () => void;
}

const MediaLibrary: React.FC<MediaLibraryProps> = ({
  tracks,
  onTrackSelect,
  selectedTrack,
  className = "",
  isPlaying = false,
  onPlayPause,
}) => {
  return (
    <div className={cn("flex flex-col gap-2.5 p-5 px-8 min-h-0", className)}>
      {tracks.map((track) =>
        track.isSecret ? null : (
          <div
            key={track.id}
            className={`flex justify-between items-center px-4 py-3 rounded-lg cursor-pointer transition-all duration-300 border-2 border-[var(--theme-primary)] hover:scale-[1.075] hover:border-[var(--theme-secondary)] gap-4 ${
              selectedTrack?.id === track.id
                ? "bg-[var(--theme-tertiary)] border-[var(--theme-secondary)] scale-[1.075] my-1"
                : ""
            }`}
            onClick={() => {
              if (selectedTrack?.id === track.id && onPlayPause) {
                onPlayPause();
              } else {
                onTrackSelect(track);
              }
            }}
          >
            <div className="min-w-0">
              <div className="font-semibold text-sm mb-1 whitespace-nowrap overflow-hidden text-ellipsis">
                {track.title}
              </div>
              {track.artist && (
                <div className="text-xs opacity-80 mb-0.5">{track.artist}</div>
              )}
              {track.duration && (
                <div className="text-xs opacity-70">{track.duration}</div>
              )}
            </div>
            <div className="flex items-center">
              {selectedTrack?.id === track.id && isPlaying && (
                <div
                  className={cn(
                    "flex items-center text-[var(--theme-secondary)]",
                    isPlaying && "animate-pulse"
                  )}
                >
                  <AudioLines fill="currentColor" size={16} />
                </div>
              )}
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default MediaLibrary;
