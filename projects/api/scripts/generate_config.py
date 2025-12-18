#!/usr/bin/env python3
"""
Script to convert lit_up_config.yaml to appConfig.json for the React app.
This script transforms the YAML configuration into the JSON format expected by
the app.
"""

import argparse
import datetime
import logging
import secrets
import sys
from pathlib import Path
from typing import Any

from lit_up_script_utils import (
    ConfigError,
    load_yaml_dict,
    require_list_field,
    save_json_atomic,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_app_config(config_path: Path, out_dir: Path) -> bool:
    """Generate appConfig.json from lit_up_config.yaml."""
    # Check if YAML file exists
    logger.info("Loading configuration from %s", config_path)
    try:
        data = load_yaml_dict(config_path)
    except ConfigError as e:
        logger.error("%s", e)
        return False

    # Optional site-wide header message
    header_message = data.get("header_message")

    # Transform songs to app format
    try:
        songs = require_list_field(data, "songs", context="lit_up_config.yaml")
    except ConfigError as e:
        logger.error("%s", e)
        return False

    tracks: list[dict[str, Any]] = []
    for song in songs:
        if not isinstance(song, dict):
            logger.warning("Skipping non-dict song entry: %r", song)
            continue

        # Validate required fields
        required_fields = ["id", "title", "artist", "duration"]
        missing_fields = [field for field in required_fields if field not in song]
        if missing_fields:
            logger.warning(
                "Song %s missing fields: %s",
                song.get("id", "unknown"),
                missing_fields,
            )
            continue

        if not isinstance(song["id"], str) or not song["id"].strip():
            logger.warning("Skipping song with invalid id: %r", song["id"])
            continue

        track = {
            "id": song["id"],
            "src": f'/songs/{song["id"]}.mp3',
            "title": song["title"],
            "artist": song["artist"],
            "duration": song["duration"],
            "cover": f'/album_art/{song["id"]}.jpg',
            "isSecret": song.get("isSecret", False),
        }
        tracks.append(track)

    if not tracks:
        logger.error("Error: No valid tracks found in YAML file")
        return False

    # Create app config
    build_hash = secrets.token_hex(16)
    app_config: dict[str, Any] = {
        "tracks": tracks,
        "headerMessage": header_message,
        "buildDatetime": datetime.datetime.now().isoformat(),
        "buildHash": build_hash,
    }

    # Save to output directory
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "appConfig.json"

    logger.info("Saving configuration to %s", output_path)
    save_json_atomic(output_path, app_config, indent=2)

    logger.info("Generated appConfig.json with %s tracks", len(tracks))
    return True


def main() -> int:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Convert lit_up_config.yaml to appConfig.json for the React app"
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
        help="Output directory (default: current directory)",
    )

    args = parser.parse_args()

    logger.info("Converting YAML to JSON...")
    success = generate_app_config(args.config.resolve(), args.out_dir.resolve())

    if not success:
        return 1

    logger.info("Configuration generation completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
