#!/usr/bin/env python3
"""
Script to concatenate individual MP3 files into a single playlist file.
This creates a continuous audio stream that can be used with timestamp-based seeking
to solve iOS lock screen auto-advance issues.
"""
# pylint: disable=broad-exception-caught

import argparse
import importlib
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

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

        logger.warning("Invalid duration format: %s", duration_str)
        return 0.0

    except (ValueError, AttributeError):
        logger.warning("Could not parse duration: %s", duration_str)
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
        logger.warning("Could not get duration with mutagen: %s", e)

    # Fallback: return 0 if we can't determine duration
    logger.warning("Could not determine duration for %s", file_path.name)
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

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.returncode == 0:

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
        logger.warning("Could not analyze audio file %s: %s", file_path.name, e)

    return {"error": "Could not analyze file"}


def create_concatenated_playlist_alternative(
    songs_dir: Path,
    output_dir: Path,
    app_config_path: Path,
    public_tracks: list,
    track_timestamps: list,
) -> bool:
    """
    Alternative concatenation approach that processes files individually
    to ensure compatibility.
    """
    # pylint: disable=too-many-locals
    try:
        output_file = output_dir / "playlist.mp3"

        # Create a temporary directory for processed files
        temp_dir = output_dir / "temp_processed"
        temp_dir.mkdir(exist_ok=True)

        processed_files: list[str] = []

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

            logger.info("Processing %s...", track["title"])
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.returncode == 0:
                processed_files.append(str(processed_file))
                logger.info("✅ Processed %s", track["title"])
            else:
                logger.error(
                    "❌ Failed to process %s: %s",
                    track["title"],
                    result.stderr,
                )
                return False

        # Now concatenate the processed files
        file_list_path = temp_dir / "processed_list.txt"
        with open(file_list_path, "w", encoding="utf-8") as f:
            for processed_file_str in processed_files:
                f.write(f"file '{processed_file_str}'\n")

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
        result = subprocess.run(concat_cmd, capture_output=True, text=True, check=True)

        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)

        if result.returncode != 0:
            logger.error("Concatenation failed: %s", result.stderr)
            return False

        logger.info("✅ Alternative concatenation successful: %s", output_file)

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
        logger.error("Alternative concatenation failed: %s", e)
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

    # pylint: disable=too-many-locals,too-many-statements

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

        logger.info(
            "Processing %s tracks for concatenation",
            len(public_tracks),
        )

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
                logger.warning("MP3 file not found: %s", mp3_file)
                continue

            # Analyze the audio file format
            audio_info = analyze_audio_file(mp3_file)
            if "error" not in audio_info:
                logger.info(
                    "📊 %s: %s, %sHz, %sch, %sbps",
                    track["title"],
                    audio_info["codec"],
                    audio_info["sample_rate"],
                    audio_info["channels"],
                    audio_info.get("bitrate", "unknown"),
                )
            else:
                logger.warning("⚠️  Could not analyze %s", track["title"])

            # Get actual duration from the file
            actual_duration = get_audio_duration(mp3_file)
            if actual_duration <= 0:
                # Fallback to duration from config
                duration_str = track.get("duration", "0:00")
                actual_duration = parse_duration(duration_str)

            if actual_duration <= 0:
                logger.warning(
                    "Could not determine duration for %s, skipping",
                    track_id,
                )
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
                "Added %s (%.1fs) at %.1fs",
                track["title"],
                actual_duration,
                current_time - actual_duration,
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
        logger.info("Command: %s", " ".join(ffmpeg_cmd))

        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)

        if result.returncode != 0:
            logger.error("ffmpeg failed with return code %s", result.returncode)
            logger.error("stderr: %s", result.stderr)
            logger.error("stdout: %s", result.stdout)

            # Try alternative approach with individual file processing
            logger.info("Trying alternative concatenation approach...")
            return create_concatenated_playlist_alternative(
                songs_dir, output_dir, app_config_path, public_tracks, track_timestamps
            )

        logger.info("✅ Concatenated playlist created: %s", output_file)

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
            "✅ Updated app config with %s track timestamps",
            len(track_timestamps),
        )
        logger.info(
            "Total playlist duration: %.1f seconds (%.1f minutes)",
            current_time,
            current_time / 60,
        )

        return True

    except Exception as e:
        logger.error("Error creating concatenated playlist: %s", e)
        return False


def main():
    """Main function to create concatenated playlist."""
    parser = argparse.ArgumentParser(
        description="Create concatenated audio playlist for iOS lock screen compatibility"  # noqa: E501 pylint: disable=line-too-long
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("."),
        help="Output directory (default: current directory)",
    )

    args = parser.parse_args()

    try:
        # Get workspace directories
        output_dir = args.out_dir.resolve()
        songs_dir = output_dir / "songs"
        app_config_path = output_dir / "appConfig.json"

        # Check if required files exist
        if not songs_dir.exists():
            logger.error("Songs directory not found: %s", songs_dir)
            return False

        if not app_config_path.exists():
            logger.error("App config not found: %s", app_config_path)
            logger.info("Please run generate_config.py first")
            return False

        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            logger.info("✅ ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ ffmpeg is not installed or not in PATH")
            logger.info("Please install ffmpeg: https://ffmpeg.org/download.html")
            return False

        logger.info("🎵 Creating concatenated audio playlist...")
        concatenated_playlist_created = create_concatenated_playlist(
            songs_dir, output_dir, app_config_path
        )

        if concatenated_playlist_created:
            logger.info("🎉 Concatenated playlist created successfully!")
            logger.info("The app will now use timestamp-based seeking for auto-advance")

            # Verify the output file
            output_file = output_dir / "playlist.mp3"
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                logger.info("📁 Output file size: %.1f MB", file_size)

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
                test_result = subprocess.run(
                    test_cmd, capture_output=True, text=True, check=True
                )
                if test_result.returncode == 0:
                    logger.info("✅ Output file is valid and playable")
                else:
                    logger.warning("⚠️  Output file may have issues")
        else:
            logger.error("❌ Failed to create concatenated playlist")

        return concatenated_playlist_created

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return False


if __name__ == "__main__":
    CONCATENATED_PLAYLIST_CREATED = main()
    sys.exit(0 if CONCATENATED_PLAYLIST_CREATED else 1)
