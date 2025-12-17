#!/usr/bin/env python3
"""
Script to convert lit_up_config.yaml to appConfig.json for the React app.
This script transforms the YAML configuration into the JSON format expected by
the app.
"""

import datetime
import importlib
import json
import sys
from pathlib import Path
import secrets


def generate_app_config():
    """Generate appConfig.json from lit_up_config.yaml."""
    # Get the script directory and workspace root
    script_dir = Path(__file__).parent
    workspace_dir = script_dir.parent
    yaml_path = workspace_dir / "lit_up_config.yaml"

    # Check if YAML file exists
    if not yaml_path.exists():
        print(f"❌ Error: {yaml_path} not found")
        print("Please ensure lit_up_config.yaml exists in the workspace root")
        return False

    # Load YAML file
    print(f"📖 Loading configuration from {yaml_path}")
    try:
        yaml = importlib.import_module("yaml")
    except ModuleNotFoundError:
        print("❌ Error: PyYAML is not installed. Please install 'pyyaml'.")
        return False
    with open(yaml_path, "r", encoding="utf-8") as f:
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

    # Save to .out directory
    out_dir = workspace_dir / ".out"
    out_dir.mkdir(exist_ok=True)
    output_path = out_dir / "appConfig.json"

    print(f"💾 Saving configuration to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(app_config, f, indent=2)

    print(f"✅ Generated appConfig.json with {len(tracks)} tracks")
    return True


def main():
    """Main function."""
    print("🔄 Converting YAML to JSON...")
    success = generate_app_config()

    if not success:
        sys.exit(1)

    print("🎉 Configuration generation completed successfully!")


if __name__ == "__main__":
    main()
