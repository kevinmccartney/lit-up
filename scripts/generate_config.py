#!/usr/bin/env python3
"""
Script to convert song_list.yaml to appConfig.json for the React app.
This script transforms the YAML configuration into the JSON format expected by the app.
"""

import yaml
import json
import sys
from pathlib import Path


def generate_app_config():
    """Generate appConfig.json from song_list.yaml."""
    try:
        # Get the script directory and workspace root
        script_dir = Path(__file__).parent
        workspace_dir = script_dir.parent
        yaml_path = workspace_dir / "song_list.yaml"

        # Check if YAML file exists
        if not yaml_path.exists():
            print(f"❌ Error: {yaml_path} not found")
            print("Please ensure song_list.yaml exists in the workspace root")
            return False

        # Load YAML file
        print(f"📖 Loading configuration from {yaml_path}")
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if "songs" not in data:
            print("❌ Error: No 'songs' key found in YAML file")
            return False

        # Transform songs to app format
        tracks = []
        for song in data["songs"]:
            # Validate required fields
            required_fields = ["id", "title", "artist", "duration"]
            missing_fields = [field for field in required_fields if field not in song]
            if missing_fields:
                print(
                    f"⚠️  Warning: Song {song.get('id', 'unknown')} missing fields: {missing_fields}"
                )
                continue

            track = {
                "id": song["id"],
                "src": f'/songs/{song["id"]}.mp3',
                "title": song["title"],
                "artist": song["artist"],
                "duration": song["duration"],
                "cover": f'/album_art/{song["id"]}.jpg',
            }
            tracks.append(track)

        if not tracks:
            print("❌ Error: No valid tracks found in YAML file")
            return False

        # Create app config
        app_config = {"tracks": tracks}

        # Save to public directory
        public_dir = workspace_dir / "public"
        public_dir.mkdir(exist_ok=True)
        output_path = public_dir / "appConfig.json"

        print(f"💾 Saving configuration to {output_path}")
        with open(output_path, "w") as f:
            json.dump(app_config, f, indent=2)

        print(f"✅ Generated appConfig.json with {len(tracks)} tracks")
        return True

    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function."""
    print("🔄 Converting YAML to JSON...")
    success = generate_app_config()

    if not success:
        sys.exit(1)

    print("🎉 Configuration generation completed successfully!")


if __name__ == "__main__":
    main()
