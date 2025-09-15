import { useState, useEffect, useMemo, useRef } from "react";
import MediaPlayer, { MediaPlayerRef } from "./components/MediaPlayer";
import MediaLibrary, { Track } from "./components/MediaLibrary";
import { useTracks } from "./hooks/useTracks";
import { Heart } from "lucide-react";

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

  const handleTrackSelect = (track: Track) => {
    setSelectedTrack(track);
    setAutoPlay(true); // Enable auto-play for new track selection
    setIsPlaying(true); // Start playing when selecting a new track

    // Reset auto-play after a brief delay to prevent it from affecting subsequent loads
    setTimeout(() => setAutoPlay(false), 100);
  };

  const getCurrentTrackIndex = () => {
    if (!selectedTrack) return -1;
    return tracks.findIndex((track) => track.id === selectedTrack.id);
  };

  const handlePrevious = () => {
    const currentIndex = getCurrentTrackIndex();
    if (currentIndex > 0) {
      const previousTrack = tracks[currentIndex - 1];
      handleTrackSelect(previousTrack);
    }
  };

  const handleNext = () => {
    const currentIndex = getCurrentTrackIndex();
    if (currentIndex < tracks.length - 1) {
      const nextTrack = tracks[currentIndex + 1];
      handleTrackSelect(nextTrack);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleHeartClick = () => {
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
  };

  const handleMeadowClick = () => {
    setShowMeadow(false);
    setSecretTrackPlaying(false);
    // Resume main player if it was paused
    if (mainPlayerPaused && mainPlayerRef.current) {
      mainPlayerRef.current.play();
      setMainPlayerPaused(false);
    }
  };

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
            <p className="text-palette-coral">
              No tracks found. Please check your configuration.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-palette-cyan">
      <header className="p-4 flex-shrink-0 marquee">
        <h1 className="text-2xl font-bold">♍️ Happy Birthday Sarah!! 🥳</h1>
      </header>
      <main className="flex-1 flex flex-col md:flex-row gap-4 p-4 min-h-0">
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
              hasPrevious={getCurrentTrackIndex() > 0}
              hasNext={getCurrentTrackIndex() < tracks.length - 1}
              className="order-1 md:order-2 flex-shrink-0 md:flex-1 min-h-0"
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
      <footer className="p-4 flex-shrink-0 text-sm text-center">
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
