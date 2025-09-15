import { useState, useEffect } from "react";
import MediaPlayer from "./components/MediaPlayer";
import MediaLibrary, { Track } from "./components/MediaLibrary";
import { useTracks } from "./hooks/useTracks";
import { Heart } from "lucide-react";

function App(): JSX.Element {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedTrack, setSelectedTrack] = useState<Track | null>(null);
  const [autoPlay, setAutoPlay] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load tracks from appConfig.json on component mount
  useEffect(() => {
    const loadTracksData = async () => {
      try {
        const loadedTracks = await useTracks();
        setTracks(loadedTracks);
        if (loadedTracks.length > 0) {
          setSelectedTrack(loadedTracks[0]);
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
      <header className="p-4 flex-shrink-0">
        <h1 className="text-2xl font-bold">✨ Lit Up</h1>
      </header>
      <main className="flex-1 flex flex-col md:flex-row gap-8 p-4 overflow-auto">
        <MediaLibrary
          tracks={tracks}
          onTrackSelect={handleTrackSelect}
          selectedTrack={selectedTrack}
          className="order-2 md:order-1 md:self-start"
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
        />
        {selectedTrack && (
          <MediaPlayer
            key={selectedTrack.id} // Force re-render when track changes
            src={selectedTrack.src}
            title={selectedTrack.title}
            cover={selectedTrack.cover}
            autoPlay={autoPlay}
            onPrevious={handlePrevious}
            onNext={handleNext}
            hasPrevious={getCurrentTrackIndex() > 0}
            hasNext={getCurrentTrackIndex() < tracks.length - 1}
            className="order-1 md:order-2 w-full md:w-auto"
            isPlaying={isPlaying}
            onPlayPause={handlePlayPause}
          />
        )}
      </main>
      <footer className="p-4 flex-shrink-0 text-sm text-center">
        <p className="flex items-center justify-center gap-2">
          Built with{" "}
          <span className="transition-all duration-300 hover:scale-125 hover:text-palette-pink text-palette-coral cursor-pointer">
            <Heart fill="currentColor" stroke="currentColor" size={16} />
          </span>
          by HK
        </p>
      </footer>
    </div>
  );
}

export default App;
