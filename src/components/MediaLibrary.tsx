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
}

interface MediaLibraryProps {
  tracks: Track[];
  onTrackSelect: (track: Track) => void;
  selectedTrack?: Track;
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
    <div className={cn("p-5", className)}>
      <div className="flex flex-col gap-2.5">
        {tracks.map((track) => (
          <div
            key={track.id}
            className={`flex justify-between items-center px-4 py-3 rounded-lg cursor-pointer transition-all duration-300 border-2 border-palette-coral hover:translate-x-1 gap-4 ${
              selectedTrack?.id === track.id
                ? "bg-white/25 border-palette-coral scale-[1.075] my-1"
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
              {selectedTrack?.id === track.id && (
                <div
                  className={cn(
                    "flex items-center text-palette-coral",
                    isPlaying && "animate-pulse"
                  )}
                >
                  <AudioLines fill="currentColor" size={16} />
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MediaLibrary;
