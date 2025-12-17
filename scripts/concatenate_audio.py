#!/usr/bin/env python3
"""
Script to concatenate individual MP3 files into a single playlist file.
This creates a continuous audio stream that can be used with timestamp-based seeking
to solve iOS lock screen auto-advance issues.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_duration(duration_str: str) -> float:
    """
    Parse duration string (MM:SS) to seconds.

    Args:
        duration_str: Duration in MM:SS format

    Returns:
        float: Duration in seconds
    """
    try:
        parts = duration_str.split(":")
        if len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            logger.warning(f"Invalid duration format: {duration_str}")
            return 0.0
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse duration: {duration_str}")
        return 0.0


def get_audio_duration(file_path: Path) -> float:
    """
    Get the actual duration of an MP3 file.

    Args:
        file_path: Path to the MP3 file

    Returns:
        float: Duration in seconds
    """
    try:
        # Try using mutagen first
        mutagen = importlib.import_module("mutagen")
        audio_file = mutagen.File(file_path)
        if audio_file is not None and hasattr(audio_file, "info"):
            return audio_file.info.length
    except (ImportError, Exception) as e:
        logger.warning(f"Could not get duration with mutagen: {e}")

    # Fallback: return 0 if we can't determine duration
    logger.warning(f"Could not determine duration for {file_path.name}")
    return 0.0


def analyze_audio_file(file_path: Path) -> dict:
    """
    Analyze an audio file to get its format information.

    Args:
        file_path: Path to the audio file

    Returns:
        dict: Audio format information
    """
    try:
        import subprocess

        # Use ffprobe to get detailed audio information
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(file_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)

            # Extract audio stream info
            audio_stream = None
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    audio_stream = stream
                    break

            if audio_stream:
                return {
                    "codec": audio_stream.get("codec_name", "unknown"),
                    "bitrate": audio_stream.get("bit_rate", "unknown"),
                    "sample_rate": audio_stream.get("sample_rate", "unknown"),
                    "channels": audio_stream.get("channels", "unknown"),
                    "duration": float(audio_stream.get("duration", 0)),
                }
    except Exception as e:
        logger.warning(f"Could not analyze audio file {file_path.name}: {e}")

    return {"error": "Could not analyze file"}


def create_concatenated_playlist_alternative(
    songs_dir: Path,
    output_dir: Path,
    app_config_path: Path,
    public_tracks: list,
    track_timestamps: list,
) -> bool:
    """
    Alternative concatenation approach that processes files individually to ensure compatibility.
    """
    try:
        import subprocess

        output_file = output_dir / "playlist.mp3"

        # Create a temporary directory for processed files
        temp_dir = output_dir / "temp_processed"
        temp_dir.mkdir(exist_ok=True)

        processed_files = []

        logger.info("Processing files individually to ensure format consistency...")

        for i, track in enumerate(public_tracks):
            track_id = track["id"]
            input_file = songs_dir / f"{track_id}.mp3"
            processed_file = temp_dir / f"processed_{i:03d}.mp3"

            # Process each file individually to ensure consistent format
            cmd = [
                "ffmpeg",
                "-i",
                str(input_file),
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-y",
                str(processed_file),
            ]

            logger.info(f"Processing {track['title']}...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                processed_files.append(str(processed_file))
                logger.info(f"✅ Processed {track['title']}")
            else:
                logger.error(f"❌ Failed to process {track['title']}: {result.stderr}")
                return False

        # Now concatenate the processed files
        file_list_path = temp_dir / "processed_list.txt"
        with open(file_list_path, "w", encoding="utf-8") as f:
            for processed_file in processed_files:
                f.write(f"file '{processed_file}'\n")

        # Concatenate the processed files
        concat_cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(file_list_path),
            "-c",
            "copy",
            "-y",
            str(output_file),
        ]

        logger.info("Concatenating processed files...")
        result = subprocess.run(concat_cmd, capture_output=True, text=True)

        # Clean up temporary files
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

        if result.returncode != 0:
            logger.error(f"Concatenation failed: {result.stderr}")
            return False

        logger.info(f"✅ Alternative concatenation successful: {output_file}")

        # Update the app config
        with open(app_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["concatenatedPlaylist"] = {
            "enabled": True,
            "file": "/playlist.mp3",
            "tracks": track_timestamps,
            "totalDuration": sum(t["duration"] for t in track_timestamps),
        }

        with open(app_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return True

    except Exception as e:
        logger.error(f"Alternative concatenation failed: {e}")
        return False


def create_concatenated_playlist(
    songs_dir: Path, output_dir: Path, app_config_path: Path
) -> bool:
    """
    Create a concatenated audio file and update the app config with timestamp data.

    Args:
        songs_dir: Directory containing individual MP3 files
        output_dir: Directory to save the concatenated file
        app_config_path: Path to the appConfig.json file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load the app config
        with open(app_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        tracks = config.get("tracks", [])
        if not tracks:
            logger.error("No tracks found in app config")
            return False

        # Filter out secret tracks for the main playlist
        public_tracks = [track for track in tracks if not track.get("isSecret", False)]

        if not public_tracks:
            logger.error("No public tracks found for concatenation")
            return False

        logger.info(f"Processing {len(public_tracks)} tracks for concatenation")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build the concatenation command
        input_files = []
        track_timestamps = []
        current_time = 0.0

        for track in public_tracks:
            track_id = track["id"]
            mp3_file = songs_dir / f"{track_id}.mp3"

            if not mp3_file.exists():
                logger.warning(f"MP3 file not found: {mp3_file}")
                continue

            # Analyze the audio file format
            audio_info = analyze_audio_file(mp3_file)
            if "error" not in audio_info:
                logger.info(
                    f"📊 {track['title']}: {audio_info['codec']}, {audio_info['sample_rate']}Hz, {audio_info['channels']}ch, {audio_info.get('bitrate', 'unknown')}bps"
                )
            else:
                logger.warning(f"⚠️  Could not analyze {track['title']}")

            # Get actual duration from the file
            actual_duration = get_audio_duration(mp3_file)
            if actual_duration <= 0:
                # Fallback to duration from config
                duration_str = track.get("duration", "0:00")
                actual_duration = parse_duration(duration_str)

            if actual_duration <= 0:
                logger.warning(f"Could not determine duration for {track_id}, skipping")
                continue

            input_files.append(str(mp3_file))

            # Store timestamp information
            track_timestamps.append(
                {
                    "id": track_id,
                    "title": track["title"],
                    "artist": track.get("artist", "Unknown"),
                    "startTime": current_time,
                    "endTime": current_time + actual_duration,
                    "duration": actual_duration,
                }
            )

            current_time += actual_duration
            logger.info(
                f"Added {track['title']} ({actual_duration:.1f}s) at {current_time - actual_duration:.1f}s"
            )

        if not input_files:
            logger.error("No valid input files found")
            return False

        # Create concatenated file using ffmpeg
        output_file = output_dir / "playlist.mp3"

        # Create a temporary file list for ffmpeg
        file_list_path = output_dir / "file_list.txt"
        with open(file_list_path, "w", encoding="utf-8") as f:
            for input_file in input_files:
                f.write(f"file '{input_file}'\n")

        # Run ffmpeg to concatenate
        import subprocess

        ffmpeg_cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(file_list_path),
            "-c:a",
            "libmp3lame",  # Re-encode to ensure consistent format
            "-b:a",
            "192k",  # Standard bitrate
            "-ar",
            "44100",  # Standard sample rate
            "-ac",
            "2",  # Stereo
            "-y",  # Overwrite output file
            str(output_file),
        ]

        logger.info("Running ffmpeg to concatenate audio files...")
        logger.info(f"Command: {' '.join(ffmpeg_cmd)}")

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"ffmpeg failed with return code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            logger.error(f"stdout: {result.stdout}")

            # Try alternative approach with individual file processing
            logger.info("Trying alternative concatenation approach...")
            return create_concatenated_playlist_alternative(
                songs_dir, output_dir, app_config_path, public_tracks, track_timestamps
            )

        logger.info(f"✅ Concatenated playlist created: {output_file}")

        # Clean up temporary file
        file_list_path.unlink()

        # Update the app config with timestamp data
        config["concatenatedPlaylist"] = {
            "enabled": True,
            "file": "/playlist.mp3",
            "tracks": track_timestamps,
            "totalDuration": current_time,
        }

        # Save updated config
        with open(app_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info(
            f"✅ Updated app config with {len(track_timestamps)} track timestamps"
        )
        logger.info(
            f"Total playlist duration: {current_time:.1f} seconds ({current_time/60:.1f} minutes)"
        )

        return True

    except Exception as e:
        logger.error(f"Error creating concatenated playlist: {e}")
        return False


def main():
    """Main function to create concatenated playlist."""
    try:
        # Get workspace directories
        script_dir = Path(__file__).parent
        workspace_dir = script_dir.parent

        songs_dir = workspace_dir / ".out" / "songs"
        output_dir = workspace_dir / ".out"
        app_config_path = workspace_dir / ".out" / "appConfig.json"

        # Check if required files exist
        if not songs_dir.exists():
            logger.error(f"Songs directory not found: {songs_dir}")
            return False

        if not app_config_path.exists():
            logger.error(f"App config not found: {app_config_path}")
            logger.info("Please run generate_config.py first")
            return False

        # Check if ffmpeg is available
        import subprocess

        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            logger.info("✅ ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ ffmpeg is not installed or not in PATH")
            logger.info("Please install ffmpeg: https://ffmpeg.org/download.html")
            return False

        logger.info("🎵 Creating concatenated audio playlist...")
        success = create_concatenated_playlist(songs_dir, output_dir, app_config_path)

        if success:
            logger.info("🎉 Concatenated playlist created successfully!")
            logger.info("The app will now use timestamp-based seeking for auto-advance")

            # Verify the output file
            output_file = output_dir / "playlist.mp3"
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                logger.info(f"📁 Output file size: {file_size:.1f} MB")

                # Test the file with ffprobe
                test_cmd = [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    str(output_file),
                ]
                test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                if test_result.returncode == 0:
                    logger.info("✅ Output file is valid and playable")
                else:
                    logger.warning("⚠️  Output file may have issues")
        else:
            logger.error("❌ Failed to create concatenated playlist")

        return success

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
