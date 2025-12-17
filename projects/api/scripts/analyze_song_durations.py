#!/usr/bin/env python
"""
Script to analyze existing MP3 files and update lit_up_config.yaml with actual durations.
This script reads the lit_up_config.yaml file, checks for corresponding MP3 files,
and updates the duration field with the actual duration from the MP3 files.
"""

import argparse
import yaml
import logging
from pathlib import Path
from mutagen import File

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_mp3_duration(mp3_file_path):
    """
    Get the duration of an MP3 file in seconds.

    Args:
        mp3_file_path: Path to the MP3 file

    Returns:
        float: Duration in seconds, or None if unable to determine
    """
    try:
        audio_file = File(mp3_file_path)
        if audio_file is not None and hasattr(audio_file, "info"):
            duration = audio_file.info.length
            return duration
        else:
            logger.warning(f"⚠ Could not read MP3 file: {mp3_file_path}")
            return None
    except Exception as e:
        logger.warning(f"⚠ Error getting MP3 duration: {e}")
        return None


def format_duration(seconds):
    """
    Format duration in seconds to MM:SS format.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration string (MM:SS)
    """
    if seconds is None:
        return "0:00"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def create_filename_from_id(song_id, extension="mp3"):
    """
    Create a filename from a song ID.

    Args:
        song_id: The song ID from the YAML file
        extension: File extension (default: "mp3")

    Returns:
        str: Safe filename using the song ID
    """
    # Clean the ID to make it filesystem-safe
    safe_id = str(song_id).replace("/", "_").replace("\\", "_").replace(":", "_")
    return f"{safe_id}.{extension}"


def analyze_and_update_durations(yaml_file_path, songs_dir):
    """
    Analyze MP3 files and update the YAML file with actual durations.

    Args:
        yaml_file_path: Path to the lit_up_config.yaml file
        songs_dir: Directory containing the MP3 files

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Load the YAML file
        with open(yaml_file_path, "r") as file:
            data = yaml.safe_load(file)

        if "songs" not in data:
            logger.error("No 'songs' key found in YAML file")
            return False

        songs = data["songs"]
        if not isinstance(songs, list):
            logger.error("'songs' should be a list")
            return False

        updated_count = 0
        missing_files = 0

        # Process each song
        for i, song in enumerate(songs):
            if not isinstance(song, dict) or "id" not in song:
                logger.warning(f"Song {i+1} missing 'id' field, skipping")
                continue

            song_id = song["id"]
            mp3_filename = create_filename_from_id(song_id, "mp3")
            mp3_filepath = songs_dir / mp3_filename

            if mp3_filepath.exists():
                # Get the actual duration from the MP3 file
                duration_seconds = get_mp3_duration(mp3_filepath)

                if duration_seconds is not None:
                    formatted_duration = format_duration(duration_seconds)

                    # Update the duration in the song data
                    old_duration = song.get("duration", "unknown")
                    song["duration"] = formatted_duration

                    if old_duration != formatted_duration:
                        logger.info(
                            f"✓ Updated {song.get('title', song_id)}: {old_duration} → {formatted_duration}"
                        )
                        updated_count += 1
                    else:
                        logger.info(
                            f"✓ {song.get('title', song_id)}: {formatted_duration} (unchanged)"
                        )
                else:
                    logger.warning(
                        f"⚠ Could not get duration for {song.get('title', song_id)}"
                    )
            else:
                logger.warning(f"⚠ MP3 file not found: {mp3_filename}")
                missing_files += 1

        # Save the updated YAML file
        with open(yaml_file_path, "w") as file:
            yaml.dump(data, file, default_flow_style=False, sort_keys=False)

        logger.info(f"✅ Analysis complete!")
        logger.info(f"   Updated durations: {updated_count}")
        logger.info(f"   Missing MP3 files: {missing_files}")
        logger.info(f"   Total songs: {len(songs)}")

        return True

    except FileNotFoundError:
        logger.error(f"YAML file not found: {yaml_file_path}")
        return False
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    """Main function to analyze MP3 durations and update YAML."""
    parser = argparse.ArgumentParser(
        description="Analyze MP3 files and update lit_up_config.yaml with actual durations"
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to lit_up_config.yaml",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("."),
        help="Output directory containing songs (default: current directory)",
    )

    args = parser.parse_args()

    try:
        logger.info("Starting MP3 duration analysis...")

        # Set up paths
        yaml_file_path = args.config.resolve()
        songs_dir = args.out_dir.resolve() / "songs"

        logger.info(f"YAML file: {yaml_file_path}")
        logger.info(f"Songs directory: {songs_dir}")

        # Check if directories exist
        if not yaml_file_path.exists():
            logger.error(f"YAML file not found: {yaml_file_path}")
            return False

        if not songs_dir.exists():
            logger.error(f"Songs directory not found: {songs_dir}")
            return False

        # Analyze and update durations
        success = analyze_and_update_durations(yaml_file_path, songs_dir)

        if success:
            logger.info("🎉 Duration analysis completed successfully!")
        else:
            logger.error("❌ Duration analysis failed!")

        return success

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
