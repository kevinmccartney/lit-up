import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import MediaPlayer, { MediaPlayerRef } from "./components/MediaPlayer";
import MediaLibrary, { Track } from "./components/MediaLibrary";
import { useTracks } from "./hooks/useTracks";
import { Heart } from "lucide-react";
import ThemePicker from "./components/ThemePicker";

function App(): JSX.Element {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [autoPlay, setAutoPlay] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showMeadow, setShowMeadow] = useState<boolean>(false);
  const [secretTrackPlaying, setSecretTrackPlaying] = useState<boolean>(false);
  const [allTracks, setAllTracks] = useState<Track[]>([]);
  const [mainPlayerPaused, setMainPlayerPaused] = useState<boolean>(false);
  const mainPlayerRef = useRef<MediaPlayerRef>(null);
  const secretTrack = useMemo(
    () => allTracks.find((track) => track.isSecret) ?? null,
    [allTracks]
  );

  // Load tracks from appConfig.json on component mount
  useEffect(() => {
    const loadTracksData = async () => {
      try {
        const loadedTracks = await useTracks();
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

  // Update the browser tab title to reflect the currently playing song
  useEffect(() => {
    const baseTitle = "Lit Up";

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
  }, [selectedTrack, isPlaying, showMeadow, secretTrackPlaying, secretTrack]);

  const handleTrackSelect = useCallback((track: Track) => {
    setSelectedTrack(track);
    setAutoPlay(true); // Enable auto-play for new track selection
    setIsPlaying(true); // Start playing when selecting a new track

    // Reset auto-play after a brief delay to prevent it from affecting subsequent loads
    setTimeout(() => setAutoPlay(false), 100);
  }, []);

  const getCurrentTrackIndex = useCallback(() => {
    if (!selectedTrack) return -1;
    return tracks.findIndex((track) => track.id === selectedTrack.id);
  }, [tracks, selectedTrack]);

  const handlePrevious = useCallback(() => {
    const currentIndex = getCurrentTrackIndex();
    if (tracks.length === 0) return;
    const previousIndex =
      currentIndex > 0 ? currentIndex - 1 : tracks.length - 1;
    const previousTrack = tracks[previousIndex];
    handleTrackSelect(previousTrack);
  }, [tracks, getCurrentTrackIndex, handleTrackSelect]);

  const handleNext = useCallback(() => {
    const currentIndex = getCurrentTrackIndex();
    if (tracks.length === 0) return;
    const nextIndex = currentIndex < tracks.length - 1 ? currentIndex + 1 : 0;
    const nextTrack = tracks[nextIndex];
    handleTrackSelect(nextTrack);
  }, [tracks, getCurrentTrackIndex, handleTrackSelect]);

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
        case 179: // MediaPlayPause
        case 179: // F8 equivalent
          event.preventDefault();
          handlePlayPause();
          break;
        case 176: // MediaTrackNext
        case 176: // F10 equivalent
          event.preventDefault();
          handleNext();
          break;
        case 177: // MediaTrackPrevious
        case 177: // F9 equivalent
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
        handlePlayPause();
      });

      navigator.mediaSession.setActionHandler("pause", () => {
        handlePlayPause();
      });

      navigator.mediaSession.setActionHandler("previoustrack", () => {
        handlePrevious();
      });

      navigator.mediaSession.setActionHandler("nexttrack", () => {
        handleNext();
      });
    }
  }, [handlePlayPause, handleNext, handlePrevious]);

  // Update Media Session metadata when track changes
  useEffect(() => {
    if ("mediaSession" in navigator && selectedTrack) {
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
    }
  }, [selectedTrack]);

  // Show loading state while tracks are being loaded
  if (isLoading) {
    return (
      <div className="h-screen flex flex-col bg-palette-cyan">
        <header className="p-4 flex-shrink-0">
          <h1 className="text-2xl font-bold">✨ Lit Up</h1>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-palette-coral mx-auto mb-4"></div>
            <p className="text-palette-coral">Loading your music library...</p>
          </div>
        </main>
      </div>
    );
  }

  // Show empty state if no tracks are loaded
  if (tracks.length === 0) {
    return (
      <div className="h-screen flex flex-col bg-palette-cyan">
        <header className="p-4 flex-shrink-0">
          <h1 className="text-2xl font-bold">✨ Lit Up</h1>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p>No tracks found. Please check your configuration.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-palette-cyan">
      <header className="p-4 flex-shrink-0 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center justify-between gap-4 marquee">
          <h1 className="text-2xl font-bold">♍️ Happy Birthday Sarah!! 🥳</h1>
        </div>
        <ThemePicker className="w-full md:w-auto justify-end" />
      </header>
      <main className="flex-1 flex flex-col md:flex-row gap-4 px-4 min-h-0">
        {/* Main interface - hidden when meadow is shown */}
        <div
          className={`flex-1 flex flex-col md:flex-row gap-4 min-h-0 ${
            showMeadow ? "hidden" : ""
          }`}
        >
          <MediaLibrary
            tracks={tracks}
            onTrackSelect={handleTrackSelect}
            selectedTrack={selectedTrack}
            className="order-2 md:order-1 md:w-80 md:flex-shrink-0 overflow-y-auto flex-1 md:flex-none"
            isPlaying={isPlaying}
            onPlayPause={handlePlayPause}
          />
          {selectedTrack && (
            <MediaPlayer
              ref={mainPlayerRef}
              key={selectedTrack.id} // Force re-render when track changes
              src={selectedTrack.src}
              title={selectedTrack.title}
              cover={selectedTrack.cover}
              autoPlay={autoPlay}
              onPrevious={handlePrevious}
              onNext={handleNext}
              onEnded={handleNext}
              hasPrevious={tracks.length > 1}
              hasNext={tracks.length > 1}
              className="order-1 md:order-2 flex-shrink-0 md:flex-1 min-h-0 md:self-start"
              isPlaying={isPlaying}
              onPlayPause={handlePlayPause}
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
              className="w-full h-full object-contain"
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
      <footer className="p-2 flex-shrink-0 text-sm text-center">
        <p className="flex items-center justify-center gap-2">
          Built with{" "}
          <span
            className="transition-all duration-300 hover:scale-125 hover:text-palette-pink text-palette-coral cursor-pointer"
            onClick={handleHeartClick}
          >
            <Heart fill="currentColor" stroke="currentColor" size={16} />
          </span>
          by HK
        </p>
      </footer>
    </div>
  );
}

export default App;
