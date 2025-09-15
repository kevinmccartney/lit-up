import { Hourglass, Play, SkipBack, SkipForward } from "lucide-react";
import React, { useState, useRef, useEffect } from "react";
import cn from "classnames";

interface MediaPlayerProps {
  src: string;
  title?: string;
  cover?: string;
  autoPlay?: boolean;
  onPrevious?: () => void;
  onNext?: () => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
  className?: string;
  isPlaying?: boolean;
  onPlayPause?: () => void;
}

const MediaPlayer: React.FC<MediaPlayerProps> = ({
  src,
  title = "Audio Player",
  cover,
  autoPlay = false,
  onPrevious,
  onNext,
  hasPrevious = false,
  hasNext = false,
  className = "",
  isPlaying: externalIsPlaying,
  onPlayPause,
}) => {
  const [internalIsPlaying, setInternalIsPlaying] = useState(externalIsPlaying);

  // Use external isPlaying state if provided, otherwise use internal state
  const isPlaying =
    externalIsPlaying !== undefined ? externalIsPlaying : internalIsPlaying;
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
      setIsLoading(false);

      // Auto-play if requested
      if (autoPlay) {
        audio.play();
        if (externalIsPlaying === undefined) {
          setInternalIsPlaying(true);
        }
      }
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      if (externalIsPlaying === undefined) {
        setInternalIsPlaying(false);
      }
      setCurrentTime(0);
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [autoPlay]);

  // Reset player state when src changes
  useEffect(() => {
    if (externalIsPlaying === undefined) {
      setInternalIsPlaying(false);
    }
    setCurrentTime(0);
    setDuration(0);
    setIsLoading(true);
  }, [src]);

  // Sync external play state with audio element
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.play();
    } else {
      audio.pause();
    }
  }, [isPlaying]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
      if (externalIsPlaying === undefined) {
        setInternalIsPlaying(false);
      }
    } else {
      audio.play();
      if (externalIsPlaying === undefined) {
        setInternalIsPlaying(true);
      }
    }

    // Call external handler if provided
    if (onPlayPause) {
      onPlayPause();
    }
  };

  const formatTime = (time: number): string => {
    if (isNaN(time)) return "0:00";

    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0;

  const handleProgressBarClick = (event: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;

    const progressBar = event.currentTarget;
    const rect = progressBar.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;

    // Update the audio time
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  return (
    <div
      className={cn(
        "border-palette-coral border-2 rounded-2xl p-8 flex-1 self-start flex md:flex-col gap-6 bg-white/25",
        className
      )}
    >
      <audio ref={audioRef} src={src} preload="metadata" />

      {cover && (
        <div className="flex md:justify-center">
          <img
            src={`/${cover}`}
            alt={`${title} cover`}
            className="md:w-72 md:h-72 w-48 h-48 rounded-xl object-cover"
            onError={(e) => {
              // Hide image if it fails to load
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        </div>
      )}

      <div className="flex flex-col justify-center items-center flex-1">
        <div className="flex flex-col justify-center items-center">
          <h3 className="m-0 text-2xl font-semibold">{title}</h3>
          <div className="flex flex-row justify-center items-center gap-5">
            <button
              className="bg-white/15 border-0 rounded-full w-12 h-12 text-2xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-white/25 hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed text-palette-coral"
              onClick={onPrevious}
              disabled={!hasPrevious || isLoading}
              title="Previous track"
            >
              <SkipBack fill="currentColor" />
            </button>

            <button
              className="bg-white/20 border-0 rounded-full w-18 h-18 text-4xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 hover:scale-105 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed text-palette-coral"
              onClick={togglePlayPause}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="animate-spin">
                  <Hourglass />
                </span>
              ) : isPlaying ? (
                <Play />
              ) : (
                <Play fill="currentColor" />
              )}
            </button>

            <button
              className="bg-white/15 border-0 rounded-full w-12 h-12 text-2xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-white/25 hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed text-palette-coral"
              onClick={onNext}
              disabled={!hasNext || isLoading}
              title="Next track"
            >
              <SkipForward fill="currentColor" />
            </button>
          </div>
        </div>

        <div className="mt-5 w-full">
          <div
            className="bg-palette-coral/20 h-2 rounded-sm overflow-hidden mb-2 backdrop-blur-sm cursor-pointer transition-all duration-300 relative hover:bg-palette-coral/30 hover:h-2.5 hover:-translate-y-0.5 active:translate-y-0"
            onClick={handleProgressBarClick}
            title="Click to seek"
          >
            <div
              className="bg-palette-coral/90 h-full transition-all duration-100 rounded-sm relative hover:bg-palette-coral hover:shadow-lg hover:shadow-palette-coral/50"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
          <div className="flex justify-between text-sm font-medium opacity-90">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MediaPlayer;
