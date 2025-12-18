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
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, NotRequired, Required, TypedDict

from lit_up_script_utils import create_filename_from_id, save_json_atomic

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Lambda-oriented subprocess bounds:
# - Default Lambda max duration is 15 minutes; leave headroom for Python overhead.
FFMPEG_TIMEOUT_SECONDS = 12 * 60
FFPROBE_TIMEOUT_SECONDS = 30
STDERR_TAIL_MAX_BYTES = 64 * 1024
STDERR_TAIL_MAX_LINES = 200


class Track(TypedDict, total=False):
    id: Required[str]
    title: Required[str]
    artist: NotRequired[str]
    duration: NotRequired[str]
    isSecret: NotRequired[bool]


class TrackTimestamp(TypedDict):
    id: str
    title: str
    artist: str
    startTime: float
    endTime: float
    duration: float


def load_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON root to be an object/dict: {path}")
    return data


def update_concatenated_playlist_config(
    config: dict[str, Any],
    *,
    track_timestamps: list[TrackTimestamp],
    total_duration: float,
) -> None:
    config["concatenatedPlaylist"] = {
        "enabled": True,
        "file": "/playlist.mp3",
        "tracks": track_timestamps,
        "totalDuration": total_duration,
    }


def run_cmd(
    cmd: list[str],
    *,
    capture_output: bool = True,
    check: bool = False,
    timeout_seconds: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess command with consistent defaults."""
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=check,
        timeout=timeout_seconds,
    )


def _format_cmd(cmd: list[str]) -> str:
    return shlex.join(cmd)


def _tail_text_file(path: Path, *, max_bytes: int, max_lines: int) -> str:
    """
    Read a bounded tail of a text file.

    We prefer bytes-based tailing so very large ffmpeg logs don't blow up memory.
    """
    try:
        with open(path, "rb") as f:
            try:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - max_bytes), 0)
            except OSError:
                # Some file-like objects may not support seeking; fallback.
                pass
            chunk = f.read()

        text = chunk.decode("utf-8", errors="replace")
        lines = text.splitlines()
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return "\n".join(lines[-max_lines:])
    except OSError as e:
        return f"<unable to read stderr log: {e}>"


def run_ffmpeg(
    cmd: list[str],
    *,
    timeout_seconds: float = FFMPEG_TIMEOUT_SECONDS,
    label: str,
) -> tuple[int, str]:
    """
    Run ffmpeg without capturing unbounded output.

    Returns (returncode, stderr_tail).
    """
    log_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=tempfile.gettempdir(),
            prefix=".ffmpeg.",
            suffix=".log",
        ) as log_file:
            log_path = Path(log_file.name)
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=log_file,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )

        stderr_tail = _tail_text_file(
            log_path, max_bytes=STDERR_TAIL_MAX_BYTES, max_lines=STDERR_TAIL_MAX_LINES
        )

        if result.returncode != 0:
            logger.error("ffmpeg failed (%s) rc=%s", label, result.returncode)
            logger.error("Command: %s", _format_cmd(cmd))
            logger.error("stderr (tail):\n%s", stderr_tail)

        return result.returncode, stderr_tail
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out (%s) after %ss", label, timeout_seconds)
        logger.error("Command: %s", _format_cmd(cmd))
        stderr_tail = ""
        if log_path is not None:
            stderr_tail = _tail_text_file(
                log_path,
                max_bytes=STDERR_TAIL_MAX_BYTES,
                max_lines=STDERR_TAIL_MAX_LINES,
            )
            logger.error("stderr (tail):\n%s", stderr_tail)
        return 124, stderr_tail
    finally:
        if log_path is not None:
            log_path.unlink(missing_ok=True)


def resolve_track_mp3_path(songs_dir: Path, track_id: str) -> Path | None:
    """
    Resolve the MP3 path for a track id.

    Backwards compatible: try the historical unsanitized filename first, then a
    sanitized filename for ids containing forbidden characters.
    """
    legacy_path = songs_dir / f"{track_id}.mp3"
    if legacy_path.exists():
        return legacy_path

    sanitized_path = songs_dir / create_filename_from_id(track_id, "mp3")
    if sanitized_path.exists():
        return sanitized_path

    return None


def resolve_duration_seconds(track: Track, mp3_file: Path) -> float:
    actual_duration = get_audio_duration(mp3_file)
    if actual_duration > 0:
        return actual_duration

    duration_str = track.get("duration", "0:00")
    return parse_duration(duration_str)


def build_concatenation_plan(
    public_tracks: list[Track],
    songs_dir: Path,
    *,
    analyze_formats: bool = True,
) -> tuple[list[str], list[TrackTimestamp], float]:
    """
    Build the ordered list of input files and track timestamps, without running ffmpeg.
    """
    input_files: list[str] = []
    track_timestamps: list[TrackTimestamp] = []
    current_time = 0.0

    for track in public_tracks:
        track_id = track["id"]
        mp3_file = resolve_track_mp3_path(songs_dir, track_id)
        if mp3_file is None:
            logger.warning("MP3 file not found: %s", songs_dir / f"{track_id}.mp3")
            continue

        if analyze_formats:
            audio_info = analyze_audio_file(mp3_file)
            if "error" not in audio_info:
                logger.debug(
                    "Audio: %s: %s, %sHz, %sch, %sbps",
                    track["title"],
                    audio_info["codec"],
                    audio_info["sample_rate"],
                    audio_info["channels"],
                    audio_info.get("bitrate", "unknown"),
                )
            else:
                logger.warning("Could not analyze %s", track["title"])

        duration_seconds = resolve_duration_seconds(track, mp3_file)
        if duration_seconds <= 0:
            logger.warning(
                "Could not determine duration for %s, skipping",
                track_id,
            )
            continue

        input_files.append(str(mp3_file))

        start_time = current_time
        end_time = current_time + duration_seconds
        track_timestamps.append(
            {
                "id": track_id,
                "title": track["title"],
                "artist": track.get("artist", "Unknown"),
                "startTime": start_time,
                "endTime": end_time,
                "duration": duration_seconds,
            }
        )

        current_time = end_time
        logger.debug(
            "Added %s (%.1fs) at %.1fs",
            track["title"],
            duration_seconds,
            start_time,
        )

    return input_files, track_timestamps, current_time


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

        result = run_cmd(
            cmd,
            capture_output=True,
            check=True,
            timeout_seconds=FFPROBE_TIMEOUT_SECONDS,
        )

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
    public_tracks: list[Track],
    track_timestamps: list[TrackTimestamp],
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

        try:
            for i, track in enumerate(public_tracks):
                track_id = track["id"]
                input_file = resolve_track_mp3_path(songs_dir, track_id)
                if input_file is None:
                    logger.error("MP3 file not found: %s", track_id)
                    return False
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

                logger.debug("Processing %s...", track["title"])
                returncode, _stderr_tail = run_ffmpeg(
                    cmd,
                    timeout_seconds=FFMPEG_TIMEOUT_SECONDS,
                    label=f"process:{track_id}",
                )

                if returncode == 0:
                    processed_files.append(str(processed_file))
                    logger.debug("Processed %s", track["title"])
                else:
                    logger.error("Failed to process %s", track["title"])
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
            returncode, _stderr_tail = run_ffmpeg(
                concat_cmd,
                timeout_seconds=FFMPEG_TIMEOUT_SECONDS,
                label="concat:alternative",
            )

            if returncode != 0:
                logger.error("Concatenation failed")
                return False
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)

        logger.info("Alternative concatenation successful: %s", output_file)

        # Update the app config
        config = load_json(app_config_path)
        total_duration = sum(t["duration"] for t in track_timestamps)
        update_concatenated_playlist_config(
            config, track_timestamps=track_timestamps, total_duration=total_duration
        )
        save_json_atomic(app_config_path, config, indent=2)

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
        config = load_json(app_config_path)

        tracks = config.get("tracks", [])
        if not tracks:
            logger.error("No tracks found in app config")
            return False

        # Filter out secret tracks for the main playlist
        public_tracks: list[Track] = [
            track for track in tracks if not track.get("isSecret", False)
        ]

        if not public_tracks:
            logger.error("No public tracks found for concatenation")
            return False

        logger.info(
            "Processing %s tracks for concatenation",
            len(public_tracks),
        )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        input_files, track_timestamps, current_time = build_concatenation_plan(
            public_tracks, songs_dir, analyze_formats=True
        )
        logger.info(
            "Planned %s tracks for concatenation (total_duration_s=%.1f)",
            len(track_timestamps),
            current_time,
        )

        if not input_files:
            logger.error("No valid input files found")
            return False

        # Create concatenated file using ffmpeg
        output_file = output_dir / "playlist.mp3"

        file_list_path: Path | None = None
        try:
            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                delete=False,
                dir=output_dir,
                prefix=".file_list.",
                suffix=".txt",
            ) as f:
                file_list_path = Path(f.name)
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
            logger.debug("Command: %s", _format_cmd(ffmpeg_cmd))

            returncode, _stderr_tail = run_ffmpeg(
                ffmpeg_cmd,
                timeout_seconds=FFMPEG_TIMEOUT_SECONDS,
                label="concat:main",
            )
            if returncode != 0:
                # Try alternative approach with individual file processing
                logger.info("Trying alternative concatenation approach...")
                return create_concatenated_playlist_alternative(
                    songs_dir,
                    output_dir,
                    app_config_path,
                    public_tracks,
                    track_timestamps,
                )
        finally:
            # Clean up temporary file
            if file_list_path is not None:
                file_list_path.unlink(missing_ok=True)

        logger.info("Concatenated playlist created: %s", output_file)

        # Update the app config with timestamp data
        update_concatenated_playlist_config(
            config, track_timestamps=track_timestamps, total_duration=current_time
        )
        save_json_atomic(app_config_path, config, indent=2)

        logger.info(
            "Updated app config with %s track timestamps",
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
            logger.debug("ffmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ffmpeg is not installed or not in PATH")
            logger.info("Please install ffmpeg: https://ffmpeg.org/download.html")
            return False

        logger.info("Creating concatenated audio playlist...")
        concatenated_playlist_created = create_concatenated_playlist(
            songs_dir, output_dir, app_config_path
        )

        if concatenated_playlist_created:
            logger.info("Concatenated playlist created successfully!")
            logger.info("The app will now use timestamp-based seeking for auto-advance")

            # Verify the output file
            output_file = output_dir / "playlist.mp3"
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                logger.debug("Output file size: %.1f MB", file_size)

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
                    logger.info("Output file is valid and playable")
                else:
                    logger.warning("Output file may have issues")
        else:
            logger.error("Failed to create concatenated playlist")

        return concatenated_playlist_created

    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return False


if __name__ == "__main__":
    CONCATENATED_PLAYLIST_CREATED = main()
    sys.exit(0 if CONCATENATED_PLAYLIST_CREATED else 1)
