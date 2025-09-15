#!/usr/bin/env python3
"""
Create a favicon from the Virgo emoji ♍️
"""

import requests
import os
from pathlib import Path


def create_emoji_favicon():
    """Create favicon from emoji using online service"""

    # The emoji we want to use
    emoji = "♍️"

    # Create public directory if it doesn't exist
    public_dir = Path(__file__).parent.parent / "public"
    public_dir.mkdir(exist_ok=True)

    print(f"Creating favicon from emoji: {emoji}")

    # Try to use favicon.io API (this is a simplified approach)
    # For a more robust solution, we'll create an SVG and convert it

    # Create SVG favicon
    svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
    <rect width="32" height="32" fill="transparent"/>
    <text x="16" y="24" font-family="Arial, sans-serif" font-size="24" text-anchor="middle" fill="black">{emoji}</text>
</svg>"""

    svg_path = public_dir / "favicon.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"✅ Created SVG favicon: {svg_path}")

    # Create a simple HTML file for testing
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Favicon Test</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
</head>
<body>
    <h1>Favicon Test - {emoji}</h1>
    <p>Check the browser tab to see the favicon!</p>
</body>
</html>"""

    html_path = public_dir / "favicon-test.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Created test HTML: {html_path}")
    print(f"📝 To complete the favicon setup:")
    print(f"   1. Visit https://favicon.io/emoji-favicons/")
    print(f"   2. Paste the emoji: {emoji}")
    print(f"   3. Download the generated favicon files")
    print(f"   4. Place them in the public/ directory")
    print(f"   5. Add the favicon links to your index.html")


if __name__ == "__main__":
    create_emoji_favicon()
