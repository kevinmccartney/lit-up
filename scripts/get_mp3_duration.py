#!/usr/bin/env python
"""
Simple script to get the duration of a single MP3 file.
Usage: python get_mp3_duration.py <path_to_mp3_file>
"""

import sys
import logging
from pathlib import Path
from mutagen import File

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
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
            logger.warning(f"Could not read MP3 file: {mp3_file_path}")
            return None
    except Exception as e:
        logger.warning(f"Error getting MP3 duration: {e}")
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


def main():
    """Main function to get MP3 duration."""
    if len(sys.argv) != 2:
        print("Usage: python get_mp3_duration.py <path_to_mp3_file>")
        sys.exit(1)

    mp3_file_path = Path(sys.argv[1])

    if not mp3_file_path.exists():
        logger.error(f"File not found: {mp3_file_path}")
        sys.exit(1)

    if not mp3_file_path.suffix.lower() == ".mp3":
        logger.error(f"File is not an MP3: {mp3_file_path}")
        sys.exit(1)

    duration_seconds = get_mp3_duration(mp3_file_path)

    if duration_seconds is not None:
        formatted_duration = format_duration(duration_seconds)
        print(f"Duration: {formatted_duration} ({duration_seconds:.2f} seconds)")
    else:
        logger.error("Could not determine duration")
        sys.exit(1)


if __name__ == "__main__":
    main()
