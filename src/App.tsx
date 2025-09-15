import { useState } from "react";
import MediaPlayer from "./components/MediaPlayer";
import MediaLibrary, { Track } from "./components/MediaLibrary";
import { availableTracks } from "./data/tracks";
import { Heart } from "lucide-react";
import { palette } from "./constants";
function App(): JSX.Element {
  const [selectedTrack, setSelectedTrack] = useState<Track>(availableTracks[0]);
  const [autoPlay, setAutoPlay] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const handleTrackSelect = (track: Track) => {
    setSelectedTrack(track);
    setAutoPlay(true); // Enable auto-play for new track selection
    setIsPlaying(true); // Start playing when selecting a new track

    // Reset auto-play after a brief delay to prevent it from affecting subsequent loads
    setTimeout(() => setAutoPlay(false), 100);
  };

  const getCurrentTrackIndex = () => {
    return availableTracks.findIndex((track) => track.id === selectedTrack.id);
  };

  const handlePrevious = () => {
    const currentIndex = getCurrentTrackIndex();
    if (currentIndex > 0) {
      const previousTrack = availableTracks[currentIndex - 1];
      handleTrackSelect(previousTrack);
    }
  };

  const handleNext = () => {
    const currentIndex = getCurrentTrackIndex();
    if (currentIndex < availableTracks.length - 1) {
      const nextTrack = availableTracks[currentIndex + 1];
      handleTrackSelect(nextTrack);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="h-screen flex flex-col bg-palette-cyan">
      <header className="p-4 flex-shrink-0">
        <h1 className="text-2xl font-bold">✨ Lit Up</h1>
      </header>
      <main className="flex-1 flex flex-col md:flex-row gap-8 p-4 overflow-auto">
        <MediaLibrary
          tracks={availableTracks}
          onTrackSelect={handleTrackSelect}
          selectedTrack={selectedTrack}
          className="order-2 md:order-1 md:self-start"
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
        />
        <MediaPlayer
          key={selectedTrack.id} // Force re-render when track changes
          src={selectedTrack.src}
          title={selectedTrack.title}
          cover={selectedTrack.cover}
          autoPlay={autoPlay}
          onPrevious={handlePrevious}
          onNext={handleNext}
          hasPrevious={getCurrentTrackIndex() > 0}
          hasNext={getCurrentTrackIndex() < availableTracks.length - 1}
          className="order-1 md:order-2 w-full md:w-auto"
          isPlaying={isPlaying}
          onPlayPause={handlePlayPause}
        />
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
