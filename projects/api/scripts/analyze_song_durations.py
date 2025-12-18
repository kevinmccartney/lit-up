#!/usr/bin/env python
"""
Script to analyze existing MP3 files and update lit_up_config.yaml with actual durations
This script reads the lit_up_config.yaml file, checks for corresponding MP3 files,
and updates the duration field with the actual duration from the MP3 files.
"""

import argparse
import logging
import sys
from pathlib import Path

from lit_up_script_utils import (
    ConfigError,
    create_filename_from_id,
    format_duration,
)
from lit_up_script_utils import get_mp3_duration as get_mp3_duration_shared
from lit_up_script_utils import (
    load_yaml_dict,
    require_list_field,
    save_yaml_atomic,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_mp3_duration(mp3_file_path: Path) -> float | None:
    """
    Get the duration of an MP3 file in seconds.

    Args:
        mp3_file_path: Path to the MP3 file

    Returns:
        float: Duration in seconds, or None if unable to determine
    """
    duration = get_mp3_duration_shared(mp3_file_path)
    if duration is None:
        logger.warning("Could not read MP3 duration: %s", mp3_file_path)
    return duration


def analyze_and_update_durations(yaml_file_path: Path, songs_dir: Path) -> bool:
    """
    Analyze MP3 files and update the YAML file with actual durations.

    Args:
        yaml_file_path: Path to the lit_up_config.yaml file
        songs_dir: Directory containing the MP3 files

    Returns:
        bool: True if successful, False otherwise
    """
    # pylint: disable=too-many-locals,too-many-branches
    try:
        data = load_yaml_dict(yaml_file_path)

        if "songs" not in data:
            logger.error("No 'songs' key found in YAML file")
            return False

        try:
            songs = require_list_field(data, "songs", context="lit_up_config.yaml")
        except ConfigError as e:
            logger.error("%s", e)
            return False

        updated_count = 0
        missing_files = 0

        # Process each song
        for i, song in enumerate(songs):
            if not isinstance(song, dict) or "id" not in song:
                logger.warning("Song %s missing 'id' field, skipping", i + 1)
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
                        logger.debug(
                            "Updated %s: %s -> %s",
                            song.get("title", song_id),
                            old_duration,
                            formatted_duration,
                        )
                        updated_count += 1
                    else:
                        logger.debug(
                            "%s: %s (unchanged)",
                            song.get("title", song_id),
                            formatted_duration,
                        )
                else:
                    logger.warning(
                        "Could not get duration for %s",
                        song.get("title", song_id),
                    )
            else:
                logger.warning("MP3 file not found: %s", mp3_filename)
                missing_files += 1

        save_yaml_atomic(yaml_file_path, data)

        logger.info("Analysis complete!")
        logger.info(
            "Summary: updated=%s missing_files=%s total_songs=%s",
            updated_count,
            missing_files,
            len(songs),
        )

        return True

    except ConfigError as e:
        logger.error("%s", e)
        return False
    except (OSError, ValueError) as e:
        logger.error("Unexpected error: %s", e)
        return False


def main() -> bool:
    """Main function to analyze MP3 durations and update YAML."""
    parser = argparse.ArgumentParser(
        description="Analyze MP3 files and update lit_up_config.yaml with durations"
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

        logger.info("YAML file: %s", yaml_file_path)
        logger.info("Songs directory: %s", songs_dir)

        # Check if directories exist
        if not yaml_file_path.exists():
            logger.error("YAML file not found: %s", yaml_file_path)
            return False

        if not songs_dir.exists():
            logger.error("Songs directory not found: %s", songs_dir)
            return False

        # Analyze and update durations
        durations_analyzed = analyze_and_update_durations(yaml_file_path, songs_dir)

        if durations_analyzed:
            logger.info("Duration analysis completed successfully!")
        else:
            logger.error("Duration analysis failed!")

        return durations_analyzed

    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("An unexpected error occurred")
        return False


if __name__ == "__main__":
    DURATIONS_ANALYZED = main()
    sys.exit(0 if DURATIONS_ANALYZED else 1)
