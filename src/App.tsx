import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import MediaPlayer, { MediaPlayerRef } from "./components/MediaPlayer";
import MediaLibrary, { Track } from "./components/MediaLibrary";
import {
  AppConfig,
  ConcatenatedPlaylist,
  getAppConfigUrl,
  useTracks,
  withAppBase,
} from "./hooks/useTracks";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import { Heart, Settings } from "lucide-react";
import ThemePicker from "./components/ThemePicker";
import DevBuildInfo from "./components/DevBuildInfo";
import PWAInstallPrompt from "./components/PWAInstallPrompt";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import VersionPicker from "./components/VersionPicker";

function AppContent(): JSX.Element {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [autoPlay, setAutoPlay] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [headerMessage, setHeaderMessage] = useState<string>("");
  const [showMeadow, setShowMeadow] = useState<boolean>(false);
  const [secretTrackPlaying, setSecretTrackPlaying] = useState<boolean>(false);
  const [allTracks, setAllTracks] = useState<Track[]>([]);
  const [mainPlayerPaused, setMainPlayerPaused] = useState<boolean>(false);
  const [concatenatedPlaylist, setConcatenatedPlaylist] =
    useState<ConcatenatedPlaylist | null>(null);
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
  const trackEndTimeoutRef = useRef<number | null>(null);
  const [buildInfo, setBuildInfo] = useState<{
    buildDatetime?: string;
    buildHash?: string;
  }>({});
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const mainPlayerRef = useRef<MediaPlayerRef>(null);
  const { theme, primaryColor, secondaryColor, tertiaryColor } = useTheme();
  const secretTrack = useMemo(
    () => allTracks.find((track) => track.isSecret) ?? null,
    [allTracks]
  );

  useEffect(() => {
    console.log(theme);
  }, [theme]);

  // Close dropdown when screen goes below md breakpoint (768px)
  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 768px)");

    const handleMediaChange = (e: MediaQueryListEvent | MediaQueryList) => {
      // If screen goes below md, close the dropdown
      if (!e.matches && isDropdownOpen) {
        setIsDropdownOpen(false);
      }
    };

    // Check initial state
    handleMediaChange(mediaQuery);

    // Listen for changes
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener("change", handleMediaChange);
      return () => mediaQuery.removeEventListener("change", handleMediaChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleMediaChange);
      return () => mediaQuery.removeListener(handleMediaChange);
    }
  }, [isDropdownOpen]);

  // Create dynamic CSS custom properties for theme colors
  const themeStyles = useMemo(() => {
    return {
      "--theme-primary": primaryColor,
      "--theme-secondary": secondaryColor,
      "--theme-tertiary": tertiaryColor,
    } as React.CSSProperties;
  }, [primaryColor, secondaryColor, tertiaryColor]);

  // Load tracks from appConfig.json on component mount
  useEffect(() => {
    const loadTracksData = async () => {
      try {
        // Load tracks
        const loadedTracks = await useTracks();
        // Also fetch build info and concatenated playlist data
        try {
          const res = await fetch(getAppConfigUrl());
          if (res.ok) {
            const cfg: AppConfig = await res.json();
            if (
              typeof cfg.headerMessage === "string" &&
              cfg.headerMessage.trim()
            ) {
              setHeaderMessage(cfg.headerMessage.trim());
            }
            setBuildInfo({
              buildDatetime: cfg.buildDatetime,
              buildHash: cfg.buildHash,
            });
            // Check for concatenated playlist
            if (cfg.concatenatedPlaylist && cfg.concatenatedPlaylist.enabled) {
              setConcatenatedPlaylist({
                ...cfg.concatenatedPlaylist,
                file: withAppBase(cfg.concatenatedPlaylist.file),
              });
            }
          }
        } catch (e) {
          // ignore build info errors
        }
        setAllTracks(loadedTracks);
        // Filter out secret tracks from the main tracks list
        const publicTracks = loadedTracks.filter((track) => !track.isSecret);
        setTracks(publicTracks);
        if (publicTracks.length > 0) {
          setSelectedTrack(publicTracks[0]);
        }
      } catch (error) {
        console.error("Failed to load tracks:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadTracksData();
  }, []);

  const isDevOverlayEnabled = useMemo(() => {
    const flag = import.meta.env.VITE_LIT_UP_APP_DEV;
    return flag === "true" || flag === "1";
  }, []);

  // Get current version from Vite's BASE_URL
  const getCurrentVersion = useCallback((): string => {
    const baseUrl = import.meta.env.BASE_URL || "/";
    // BASE_URL will be like /v1/ or /v2/, extract the version
    const match = baseUrl.match(/\/(v\d+)\//);
    if (match && match[1]) {
      return match[1];
    }
    // Default fallback
    return "v1";
  }, []);

  // Update the browser tab title to reflect the currently playing song
  useEffect(() => {
    const version = getCurrentVersion();
    const baseTitle = `Lit Up ${version}`;

    // Determine which track is effectively playing (secret track takes precedence when meadow is shown)
    const activeSecret = showMeadow && secretTrackPlaying && secretTrack;
    const activeTrack = activeSecret ? secretTrack : selectedTrack;

    if (activeTrack) {
      const artist = (activeTrack as any).artist
        ? ` — ${(activeTrack as any).artist}`
        : "";
      document.title = `${baseTitle} | ${activeTrack.title}${artist}`;
    } else {
      document.title = baseTitle;
    }
  }, [
    selectedTrack,
    isPlaying,
    showMeadow,
    secretTrackPlaying,
    secretTrack,
    getCurrentVersion,
  ]);

  const handleTrackSelect = useCallback((track: Track) => {
    setSelectedTrack(track);
    setAutoPlay(true); // Enable auto-play for new track selection
    setIsPlaying(true); // Start playing when selecting a new track

    // Reset auto-play after a brief delay to prevent it from affecting subsequent loads
    setTimeout(() => setAutoPlay(false), 100);

    // Ensure Media Session is updated immediately
    if ("mediaSession" in navigator) {
      requestAnimationFrame(() => {
        navigator.mediaSession.playbackState = "playing";
      });
    }
  }, []);

  const getCurrentTrackIndex = useCallback(() => {
    if (!selectedTrack) return -1;
    return tracks.findIndex((track) => track.id === selectedTrack.id);
  }, [tracks, selectedTrack]);

  // Helper function to get track timing info from concatenated playlist
  const getTrackTiming = useCallback(
    (trackId: string) => {
      if (!concatenatedPlaylist || !concatenatedPlaylist.tracks) {
        return null;
      }
      return concatenatedPlaylist.tracks.find((t) => t.id === trackId);
    },
    [concatenatedPlaylist]
  );

  const handlePrevious = useCallback(() => {
    const currentIndex = getCurrentTrackIndex();
    if (tracks.length === 0) return;

    // Check if we're in the middle of a song (> 3 seconds played)
    if (mainPlayerRef.current) {
      const currentTime = mainPlayerRef.current.getCurrentTime();
      const currentTrackTiming = getTrackTiming(selectedTrack?.id ?? "");
      const currentTrackTime =
        currentTime - (currentTrackTiming?.startTime ?? 0);
      if (currentTrackTime > 3) {
        // Restart current song
        if (concatenatedPlaylist && selectedTrack) {
          // In concatenated playlist mode, restart from the track's start time
          const trackTiming = getTrackTiming(selectedTrack.id);
          if (trackTiming && trackTiming.startTime !== undefined) {
            mainPlayerRef.current.setCurrentTime(trackTiming.startTime);
          }
        } else {
          // In individual track mode, restart from beginning
          mainPlayerRef.current.setCurrentTime(0);
        }
        return;
      } else {
        const previousTrack = tracks[currentIndex - 1];
        const previousTrackTiming = getTrackTiming(previousTrack.id);

        if (previousTrackTiming && previousTrackTiming.endTime !== undefined) {
          mainPlayerRef.current.setCurrentTime(previousTrackTiming.endTime);
        }
      }
    }

    // Otherwise, go to previous track
    const previousIndex =
      currentIndex > 0 ? currentIndex - 1 : tracks.length - 1;
    const previousTrack = tracks[previousIndex];
    handleTrackSelect(previousTrack);
  }, [
    tracks,
    getCurrentTrackIndex,
    handleTrackSelect,
    concatenatedPlaylist,
    selectedTrack,
    getTrackTiming,
  ]);

  const handleNext = useCallback(() => {
    const currentIndex = getCurrentTrackIndex();
    if (tracks.length === 0) return;
    const nextIndex = currentIndex < tracks.length - 1 ? currentIndex + 1 : 0;
    const nextTrack = tracks[nextIndex];
    handleTrackSelect(nextTrack);
  }, [tracks, getCurrentTrackIndex, handleTrackSelect]);

  // Handle track end in concatenated playlist mode
  const handleTrackEnd = useCallback(() => {
    if (concatenatedPlaylist && !isTransitioning) {
      // Clear any existing timeout to prevent multiple rapid transitions
      if (trackEndTimeoutRef.current) {
        clearTimeout(trackEndTimeoutRef.current);
      }

      setIsTransitioning(true);

      // Use a longer delay to ensure the track has actually ended
      trackEndTimeoutRef.current = setTimeout(() => {
        handleNext();
        // Reset transition state after a delay
        setTimeout(() => {
          setIsTransitioning(false);
        }, 300);
      }, 150);
    }
  }, [concatenatedPlaylist, handleNext, isTransitioning]);

  const handlePlayPause = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleHeartClick = useCallback(() => {
    if (!showMeadow && secretTrack) {
      // Show meadow and start playing secret track
      setShowMeadow(true);
      setSecretTrackPlaying(true);
      // Pause main player if it's playing
      if (isPlaying && mainPlayerRef.current) {
        setMainPlayerPaused(true);
        mainPlayerRef.current.pause();
      }
    } else {
      // Hide meadow and stop secret track
      setShowMeadow(false);
      setSecretTrackPlaying(false);
      // Resume main player if it was paused
      if (mainPlayerPaused && mainPlayerRef.current) {
        mainPlayerRef.current.play();
        setMainPlayerPaused(false);
      }
    }
  }, [showMeadow, secretTrack, isPlaying, mainPlayerPaused]);

  const handleMeadowClick = useCallback(() => {
    setShowMeadow(false);
    setSecretTrackPlaying(false);
    // Resume main player if it was paused
    if (mainPlayerPaused && mainPlayerRef.current) {
      mainPlayerRef.current.play();
      setMainPlayerPaused(false);
    }
  }, [mainPlayerPaused]);

  // Handle media key events (play/pause, forward, back buttons on keyboard)
  useEffect(() => {
    const handleMediaKeyDown = (event: KeyboardEvent) => {
      // Check for media keys
      switch (event.code) {
        case "MediaPlayPause":
        case "F8": // Mac play/pause key
          event.preventDefault();
          handlePlayPause();
          break;
        case "MediaTrackNext":
        case "F10": // Mac forward key
          event.preventDefault();
          handleNext();
          break;
        case "MediaTrackPrevious":
        case "F9": // Mac back key
          event.preventDefault();
          handlePrevious();
          break;
      }
    };

    // Also listen for the older keyCode events for broader compatibility
    const handleLegacyMediaKeys = (event: KeyboardEvent) => {
      switch (event.keyCode) {
        case 179: // MediaPlayPause or F8 equivalent
          event.preventDefault();
          handlePlayPause();
          break;
        case 176: // MediaTrackNext or F10 equivalent
          event.preventDefault();
          handleNext();
          break;
        case 177: // MediaTrackPrevious or F9 equivalent
          event.preventDefault();
          handlePrevious();
          break;
      }
    };

    document.addEventListener("keydown", handleMediaKeyDown);
    document.addEventListener("keydown", handleLegacyMediaKeys);

    return () => {
      document.removeEventListener("keydown", handleMediaKeyDown);
      document.removeEventListener("keydown", handleLegacyMediaKeys);
    };
  }, [handlePlayPause, handleNext, handlePrevious]);

  // Set up Media Session API for proper media key handling
  useEffect(() => {
    if ("mediaSession" in navigator) {
      navigator.mediaSession.setActionHandler("play", () => {
        console.log("Media Session: Play action triggered");
        handlePlayPause();
      });

      navigator.mediaSession.setActionHandler("pause", () => {
        console.log("Media Session: Pause action triggered");
        handlePlayPause();
      });

      navigator.mediaSession.setActionHandler("previoustrack", () => {
        console.log("Media Session: Previous track action triggered");
        handlePrevious();
      });

      navigator.mediaSession.setActionHandler("nexttrack", () => {
        console.log("Media Session: Next track action triggered");
        handleNext();
      });

      // Add seekbackward and seekforward for better PWA support
      navigator.mediaSession.setActionHandler("seekbackward", (details) => {
        console.log("Media Session: Seek backward action triggered");
        if (mainPlayerRef.current) {
          const currentTime = mainPlayerRef.current.getCurrentTime();
          const seekTime = Math.max(
            0,
            currentTime - (details.seekOffset || 10)
          );
          mainPlayerRef.current.setCurrentTime(seekTime);
        }
      });

      navigator.mediaSession.setActionHandler("seekforward", (details) => {
        console.log("Media Session: Seek forward action triggered");
        if (mainPlayerRef.current) {
          const currentTime = mainPlayerRef.current.getCurrentTime();
          const seekTime = currentTime + (details.seekOffset || 10);
          mainPlayerRef.current.setCurrentTime(seekTime);
        }
      });
    }
  }, [handlePlayPause, handleNext, handlePrevious]);

  // Update Media Session metadata when track changes
  useEffect(() => {
    if ("mediaSession" in navigator && selectedTrack) {
      // Use requestAnimationFrame to ensure metadata update doesn't interfere with playback
      requestAnimationFrame(() => {
        navigator.mediaSession.metadata = new MediaMetadata({
          title: selectedTrack.title,
          artist: (selectedTrack as any).artist || "Unknown Artist",
          album: "Lit Up",
          artwork: [
            {
              src: selectedTrack.cover,
              sizes: "512x512",
              type: "image/jpeg",
            },
          ],
        });

        // Ensure the playback state is properly set
        navigator.mediaSession.playbackState = isPlaying ? "playing" : "paused";
      });
    }
  }, [selectedTrack, isPlaying]);

  // Update Media Session playback state when playing state changes
  useEffect(() => {
    if ("mediaSession" in navigator) {
      navigator.mediaSession.playbackState = isPlaying ? "playing" : "paused";
    }
  }, [isPlaying]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (trackEndTimeoutRef.current) {
        clearTimeout(trackEndTimeoutRef.current);
      }
    };
  }, []);

  // Show loading state while tracks are being loaded
  if (isLoading) {
    return (
      <div
        className="flex flex-col bg-[var(--theme-primary)] h-screen-mobile-portrait"
        style={themeStyles}
      ></div>
    );
  }

  // Show empty state if no tracks are loaded
  if (tracks.length === 0) {
    return (
      <div
        className="flex flex-col bg-[var(--theme-primary)] h-screen-mobile-portrait"
        style={themeStyles}
      >
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p>No tracks found. Please check your configuration.</p>
          </div>
        </main>
      </div>
    );
  }

  const settingsMenu = (
    <div className="flex flex-row md:flex-col gap-4 md:gap-2">
      <ThemePicker className="w-full" />
      <VersionPicker className="w-full" />
    </div>
  );

  return (
    <div
      className="flex flex-col bg-[var(--theme-primary)] h-screen-mobile-portrait"
      style={themeStyles}
    >
      <header
        className={`flex-shrink-0 flex flex-col md:flex-row justify-between mb-8 md:mb-4`}
      >
        <div
          className={`py-2 bg-[var(--theme-tertiary)] w-full md:border-b-2 border-[var(--theme-secondary)]`}
        >
          <div className="flex items-center justify-between gap-4 marquee w-full md:w-11/12">
            <h1 className="text-2xl font-bold">{headerMessage}</h1>
          </div>
        </div>
        <div className="flex justify-end md:hidden bg-[var(--theme-tertiary)] border-b-2 border-[var(--theme-secondary)] pb-2 px-4">
          {settingsMenu}
        </div>
        <div className="hidden md:flex">
          <DropdownMenu.Root
            open={isDropdownOpen}
            onOpenChange={setIsDropdownOpen}
          >
            <DropdownMenu.Trigger asChild>
              <button
                className={`w-full md:w-auto p-4 md:p-2 bg-[var(--theme-tertiary)] border-b-2 border-[var(--theme-secondary)] hover:bg-[var(--theme-secondary)] transition-colors flex items-center justify-center md:justify-end`}
                aria-label="Settings"
              >
                <Settings className="w-5 h-5 md:w-6 md:h-6" />
              </button>
            </DropdownMenu.Trigger>

            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="min-w-[200px] bg-[var(--theme-tertiary)] border-2 border-[var(--theme-secondary)] rounded-md shadow-lg p-4 z-50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95"
                style={themeStyles}
                sideOffset={5}
                align="end"
                side="bottom"
              >
                {settingsMenu}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </header>
      <main className="flex-1 flex flex-col md:gap-4 px-0 md:px-4 min-h-0 sm:overflow-y-auto md:overflow-y-hidden">
        {/* Main interface - hidden when meadow is shown */}
        <div
          className={`flex-1 flex flex-col md:flex-row md:gap-4 min-h-0 ${
            showMeadow ? "hidden" : ""
          }`}
        >
          <MediaLibrary
            tracks={tracks}
            onTrackSelect={handleTrackSelect}
            selectedTrack={selectedTrack}
            className="order-2 md:order-1 md:w-80 md:flex-shrink-0 overflow-y-auto sm:overflow-y-visible md:overflow-y-auto flex-1 md:flex-none px-4"
            isPlaying={isPlaying}
            onPlayPause={handlePlayPause}
          />
          {selectedTrack && (
            <MediaPlayer
              ref={mainPlayerRef}
              key={selectedTrack.id} // Force re-render when track changes
              src={
                concatenatedPlaylist
                  ? concatenatedPlaylist.file
                  : selectedTrack.src
              }
              title={selectedTrack.title}
              cover={selectedTrack.cover}
              autoPlay={autoPlay}
              onPrevious={handlePrevious}
              onNext={handleNext}
              onEnded={concatenatedPlaylist ? undefined : handleNext}
              onTrackEnd={concatenatedPlaylist ? handleTrackEnd : undefined}
              hasPrevious={tracks.length > 1}
              hasNext={tracks.length > 1}
              className="order-1 md:order-2 flex-shrink-0 md:flex-1 min-h-0 md:self-start px-4 mx-4"
              isPlaying={isPlaying}
              onPlayPause={handlePlayPause}
              // Concatenated playlist props
              playlistMode={!!concatenatedPlaylist}
              trackStartTime={
                concatenatedPlaylist
                  ? getTrackTiming(selectedTrack.id)?.startTime
                  : undefined
              }
              trackEndTime={
                concatenatedPlaylist
                  ? getTrackTiming(selectedTrack.id)?.endTime
                  : undefined
              }
            />
          )}
        </div>

        {/* Meadow view - shown when meadow is active */}
        {showMeadow && secretTrack && (
          <div
            className="flex-1 flex items-center justify-center cursor-pointer"
            onClick={handleMeadowClick}
          >
            <img
              src={secretTrack.cover}
              alt="Meadow"
              className="object-contain"
            />
            {/* Hidden audio element for secret track */}
            <audio
              key={`secret-audio-${secretTrack.id}`}
              src={secretTrack.src}
              autoPlay={secretTrackPlaying}
              loop
              style={{ display: "none" }}
            />
          </div>
        )}
      </main>
      <footer
        className={`p-2 flex-shrink-0 text-sm text-center bg-[var(--theme-tertiary)] border-t-2 border-[var(--theme-secondary)] mt-8 md:mt-0`}
      >
        <p className="flex items-center justify-center gap-2">
          Built with{" "}
          <span
            className={`transition-all duration-300 hover:scale-125 hover:text-red-500 text-[var(--theme-secondary)] cursor-pointer`}
            onClick={handleHeartClick}
          >
            <Heart fill="currentColor" stroke="currentColor" size={16} />
          </span>
          by HK
        </p>
        {isDevOverlayEnabled &&
          buildInfo.buildDatetime &&
          buildInfo.buildHash && (
            <div className="mt-2 flex justify-center absolute bottom-0 right-0">
              <DevBuildInfo
                buildDatetime={buildInfo.buildDatetime}
                buildHash={buildInfo.buildHash}
              />
            </div>
          )}
      </footer>

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />
    </div>
  );
}

function App(): JSX.Element {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
