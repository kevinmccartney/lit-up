import { Hourglass, Pause, Play, SkipBack, SkipForward } from "lucide-react";
import React, {
  useState,
  useRef,
  useEffect,
  forwardRef,
  useImperativeHandle,
} from "react";
import cn from "classnames";
import { useTheme } from "../contexts/ThemeContext";

interface MediaPlayerProps {
  src: string;
  title?: string;
  cover?: string;
  autoPlay?: boolean;
  onPrevious?: () => void;
  onNext?: () => void;
  onEnded?: () => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
  className?: string;
  isPlaying?: boolean;
  onPlayPause?: () => void;
  // Concatenated playlist support
  playlistMode?: boolean;
  trackStartTime?: number;
  trackEndTime?: number;
  onTrackEnd?: () => void;
}

export interface MediaPlayerRef {
  pause: () => void;
  play: () => void;
  getCurrentTime: () => number;
  setCurrentTime: (time: number) => void;
}

const MediaPlayer = forwardRef<MediaPlayerRef, MediaPlayerProps>(
  (
    {
      src,
      title = "Audio Player",
      cover,
      autoPlay = false,
      onPrevious,
      onNext,
      onEnded,
      hasPrevious = false,
      hasNext = false,
      className = "",
      isPlaying: externalIsPlaying,
      onPlayPause,
      // Concatenated playlist support
      playlistMode = false,
      trackStartTime = 0,
      trackEndTime,
      onTrackEnd,
    },
    ref
  ) => {
    const [internalIsPlaying, setInternalIsPlaying] =
      useState(externalIsPlaying);

    // Use external isPlaying state if provided, otherwise use internal state
    const isPlaying =
      externalIsPlaying !== undefined ? externalIsPlaying : internalIsPlaying;
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const audioRef = useRef<HTMLAudioElement>(null);
    const trackEndCheckIntervalRef = useRef<number | null>(null);
    const lastTrackEndCheckRef = useRef<number>(0);
    useTheme(); // For theme context

    // Calculate effective duration for playlist mode
    const effectiveDuration =
      playlistMode && trackEndTime ? trackEndTime - trackStartTime : duration;

    // Expose audio control methods to parent component
    useImperativeHandle(ref, () => ({
      pause: () => {
        const audio = audioRef.current;
        if (audio) {
          audio.pause();
        }
      },
      play: () => {
        const audio = audioRef.current;
        if (audio) {
          audio.play();
        }
      },
      getCurrentTime: () => {
        const audio = audioRef.current;
        return audio ? audio.currentTime : 0;
      },
      setCurrentTime: (time: number) => {
        const audio = audioRef.current;
        if (audio) {
          audio.currentTime = time;
        }
      },
    }));

    useEffect(() => {
      const audio = audioRef.current;
      if (!audio) return;

      const handleLoadedMetadata = () => {
        setDuration(audio.duration);
        setIsLoading(false);

        // Auto-play if requested
        if (autoPlay) {
          // For PWA, attempt to resume AudioContext if available (non-standard)
          // @ts-ignore: context is not standard on HTMLAudioElement
          if (
            (audio as any).context &&
            (audio as any).context.state === "suspended"
          ) {
            // @ts-ignore
            (audio as any).context.resume();
          }
          audio.play();
          if (externalIsPlaying === undefined) {
            setInternalIsPlaying(true);
          }
        }
      };

      const handleTimeUpdate = () => {
        if (playlistMode) {
          // In playlist mode, show relative time within the track
          const absoluteTime = audio.currentTime;
          const relativeTime = Math.max(0, absoluteTime - trackStartTime);
          setCurrentTime(relativeTime);

          // Check if we've reached the end of this track
          // Only trigger when we're very close to the end (within 0.05s) to avoid early transitions
          if (trackEndTime && absoluteTime >= trackEndTime - 0.05) {
            if (onTrackEnd) {
              onTrackEnd();
            }
          }
        } else {
          setCurrentTime(audio.currentTime);
        }
      };

      const handleEnded = () => {
        if (externalIsPlaying === undefined) {
          setInternalIsPlaying(false);
        }
        setCurrentTime(0);
        if (onEnded) {
          onEnded();
        }
      };

      // More reliable track end detection for iOS
      const handleProgress = () => {
        if (playlistMode && trackEndTime) {
          const absoluteTime = audio.currentTime;
          // Check if we've reached the end of this track
          if (absoluteTime >= trackEndTime - 0.05) {
            if (onTrackEnd) {
              onTrackEnd();
            }
          }
        }
      };

      audio.addEventListener("loadedmetadata", handleLoadedMetadata);
      audio.addEventListener("timeupdate", handleTimeUpdate);
      audio.addEventListener("ended", handleEnded);
      audio.addEventListener("progress", handleProgress);

      // Set up reliable track end detection for locked/backgrounded devices
      // This uses polling which works even when timeupdate is throttled
      if (playlistMode && trackEndTime && onTrackEnd) {
        const checkTrackEnd = () => {
          const absoluteTime = audio.currentTime;
          // Only check if we're close to the end and haven't already triggered
          // This prevents multiple rapid triggers
          if (
            absoluteTime >= trackEndTime - 0.1 &&
            absoluteTime < trackEndTime + 0.5 &&
            Date.now() - lastTrackEndCheckRef.current > 500
          ) {
            lastTrackEndCheckRef.current = Date.now();
            onTrackEnd();
          }
        };

        // Poll every 100ms for reliable detection even when backgrounded
        trackEndCheckIntervalRef.current = window.setInterval(
          checkTrackEnd,
          100
        );
      }

      // Also check when page becomes visible again (user unlocks phone)
      const handleVisibilityChange = () => {
        if (!document.hidden && playlistMode && trackEndTime && onTrackEnd) {
          const absoluteTime = audio.currentTime;
          if (absoluteTime >= trackEndTime - 0.1) {
            onTrackEnd();
          }
        }
      };

      document.addEventListener("visibilitychange", handleVisibilityChange);

      return () => {
        audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
        audio.removeEventListener("timeupdate", handleTimeUpdate);
        audio.removeEventListener("ended", handleEnded);
        audio.removeEventListener("progress", handleProgress);
        document.removeEventListener("visibilitychange", handleVisibilityChange);
        if (trackEndCheckIntervalRef.current !== null) {
          clearInterval(trackEndCheckIntervalRef.current);
          trackEndCheckIntervalRef.current = null;
        }
      };
    }, [autoPlay, playlistMode, trackEndTime, onTrackEnd, trackStartTime]);

    // Reset player state when src changes
    useEffect(() => {
      // Clear any existing track end check interval
      if (trackEndCheckIntervalRef.current !== null) {
        clearInterval(trackEndCheckIntervalRef.current);
        trackEndCheckIntervalRef.current = null;
      }
      lastTrackEndCheckRef.current = 0;

      if (externalIsPlaying === undefined) {
        setInternalIsPlaying(false);
      }
      setCurrentTime(0);
      setDuration(0);
      setIsLoading(true);
    }, [src]);

    // Set initial position for playlist mode
    useEffect(() => {
      if (playlistMode && trackStartTime > 0) {
        const audio = audioRef.current;
        if (audio) {
          audio.currentTime = trackStartTime;
        }
      }
    }, [playlistMode, trackStartTime]);

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

    const progressPercentage =
      effectiveDuration > 0 ? (currentTime / effectiveDuration) * 100 : 0;

    const handleProgressBarClick = (
      event: React.MouseEvent<HTMLDivElement>
    ) => {
      const audio = audioRef.current;
      if (!audio || !effectiveDuration) return;

      const progressBar = event.currentTarget;
      const rect = progressBar.getBoundingClientRect();
      const clickX = event.clientX - rect.left;
      const percentage = clickX / rect.width;
      const newRelativeTime = percentage * effectiveDuration;

      if (playlistMode) {
        // In playlist mode, convert relative time to absolute time
        const newAbsoluteTime = trackStartTime + newRelativeTime;
        audio.currentTime = newAbsoluteTime;
        setCurrentTime(newRelativeTime);
      } else {
        // Normal mode
        audio.currentTime = newRelativeTime;
        setCurrentTime(newRelativeTime);
      }
    };

    return (
      <div
        className={cn(
          `border-2 border-[var(--theme-secondary)] rounded-2xl p-4 md:p-8 flex flex-col sm:flex-row lg:flex-col gap-4 md:gap-6 bg-[var(--theme-tertiary)] min-h-0`,
          className
        )}
      >
        <audio
          ref={audioRef}
          src={src}
          preload="metadata"
          playsInline
          webkit-playsinline="true"
          crossOrigin="anonymous"
          controls={false}
          loop={false}
          muted={false}
        />

        {cover && (
          <div className="flex justify-center">
            <img
              src={`${cover}`}
              alt={`${title} cover`}
              className="w-32 h-32 lg:w-72 lg:h-72 rounded-xl object-cover"
              onError={(e) => {
                // Hide image if it fails to load
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        )}

        <div className="flex flex-col justify-center items-center flex-1 w-full">
          <div className="flex flex-col justify-center items-center w-full">
            <h3 className="m-0 text-lg md:text-2xl font-semibold text-center">
              {title}
            </h3>
            <div
              className={`flex flex-row justify-center items-center gap-5 text-[var(--theme-secondary)]`}
            >
              <button
                className={`border-0 rounded-full w-12 h-12 text-2xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-[var(--theme-tertiary)] hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed`}
                onClick={onPrevious}
                disabled={!hasPrevious || isLoading}
                title="Previous track"
              >
                <SkipBack fill="currentColor" />
              </button>

              <button
                className={`border-0 rounded-full w-18 h-18 text-4xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-[var(--theme-tertiary)] hover:scale-105 active:scale-95 disabled:opacity-60 disabled:cursor-not-allowed`}
                onClick={togglePlayPause}
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="animate-spin">
                    <Hourglass />
                  </span>
                ) : isPlaying ? (
                  <Pause fill="currentColor" />
                ) : (
                  <Play fill="currentColor" />
                )}
              </button>

              <button
                className="border-0 rounded-full w-12 h-12 text-2xl cursor-pointer transition-all duration-300 backdrop-blur-sm flex items-center justify-center hover:bg-[var(--theme-tertiary)] hover:scale-105 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
                onClick={onNext}
                disabled={!hasNext || isLoading}
                title="Next track"
              >
                <SkipForward fill="currentColor" />
              </button>
            </div>
          </div>

          <div className="mt-2 md:mt-5 w-full">
            <div
              className={`bg-[var(--theme-primary)] h-2 rounded-sm overflow-hidden mb-2 backdrop-blur-sm cursor-pointer transition-all duration-300 relative hover:h-2.5 hover:-translate-y-0.5 active:translate-y-0`}
              onClick={handleProgressBarClick}
              title="Click to seek"
            >
              <div
                className={`bg-[var(--theme-secondary)] h-full transition-all duration-100 rounded-sm relative hover:bg-[var(--theme-secondary)] hover:shadow-lg hover:shadow-black/50`}
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <div className="flex justify-between text-sm font-medium opacity-90">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(effectiveDuration)}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }
);

MediaPlayer.displayName = "MediaPlayer";

export default MediaPlayer;
