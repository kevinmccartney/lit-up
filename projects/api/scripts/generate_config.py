#!/usr/bin/env python3
"""
Script to convert lit_up_config.yaml to appConfig.json for the React app.
This script transforms the YAML configuration into the JSON format expected by
the app.
"""

import argparse
import datetime
import json
import secrets
import sys
from pathlib import Path

import yaml


def generate_app_config(config_path: Path, out_dir: Path):
    """Generate appConfig.json from lit_up_config.yaml."""
    # Check if YAML file exists
    if not config_path.exists():
        print(f"❌ Error: {config_path} not found")
        return False

    # Load YAML file
    print(f"📖 Loading configuration from {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        yaml_error = getattr(yaml, "YAMLError", Exception)
        try:
            data = yaml.safe_load(f)
        except yaml_error as e:  # type: ignore[misc]
            print(f"❌ Error parsing YAML file: {e}")
            return False

    if "songs" not in data:
        print("❌ Error: No 'songs' key found in YAML file")
        return False

    # Optional site-wide header message
    header_message = data.get("header_message")

    # Transform songs to app format
    tracks = []
    for song in data["songs"]:
        # Validate required fields
        required_fields = ["id", "title", "artist", "duration"]
        missing_fields = [field for field in required_fields if field not in song]
        if missing_fields:
            print(
                f"⚠️  Warning: Song {song.get('id', 'unknown')} "
                f"missing fields: {missing_fields}"
            )
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
        print("❌ Error: No valid tracks found in YAML file")
        return False

    # Create app config
    build_hash = secrets.token_hex(16)
    app_config = {
        "tracks": tracks,
        "headerMessage": header_message,
        "buildDatetime": datetime.datetime.now().isoformat(),
        "buildHash": build_hash,
    }

    # Save to output directory
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "appConfig.json"

    print(f"💾 Saving configuration to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(app_config, f, indent=2)

    print(f"✅ Generated appConfig.json with {len(tracks)} tracks")
    return True


def main():
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

    print("🔄 Converting YAML to JSON...")
    success = generate_app_config(args.config.resolve(), args.out_dir.resolve())

    if not success:
        sys.exit(1)

    print("🎉 Configuration generation completed successfully!")


if __name__ == "__main__":
    main()
