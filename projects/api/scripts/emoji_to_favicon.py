#!/usr/bin/env python3
"""
Convert an emoji to a favicon SVG or PNG.

Usage:
    python emoji_to_favicon.py [--config CONFIG] [--emoji EMOJI]
        [--output OUTPUT] [--size SIZE] [--format FORMAT]

If --config is provided, reads favicon emoji from lit_up_config.yaml.
Otherwise, requires --emoji argument.

Formats:
    - svg: Embed emoji as text in SVG (default, no dependencies)
    - png: Convert SVG to PNG using cairosvg (requires cairosvg)
"""

import argparse
import sys
from pathlib import Path

import cairosvg
import yaml


def emoji_to_svg_text(emoji: str, size: int = 32) -> str:
    """
    Method 1: Embed emoji directly as text in SVG.
    Simple and works well in modern browsers.
    """
    font_size = int(size * 0.75)
    font_family = "Apple Color Emoji, Segoe UI Emoji, " + "Noto Color Emoji, sans-serif"
    center = size // 2
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"
     xmlns="http://www.w3.org/2000/svg">
    <rect width="{size}" height="{size}" fill="transparent"/>
    <text x="{center}" y="{center}"
          font-family="{font_family}"
          font-size="{font_size}"
          text-anchor="middle"
          dominant-baseline="middle">{emoji}</text>
</svg>"""


def emoji_to_png(emoji: str, size: int = 32) -> bytes:
    """
    Convert emoji to PNG by first generating SVG, then converting to PNG.
    Returns PNG image bytes.
    """
    # Generate SVG first
    svg_content = emoji_to_svg_text(emoji, size)

    # Convert SVG to PNG
    png_bytes = cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        output_width=size,
        output_height=size,
    )

    return png_bytes


def load_config(config_path: Path) -> dict:
    """Load the config file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (OSError, IOError, yaml.YAMLError) as e:
        print(f"Error reading config file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Runs the Emoji to Favicon script."""
    parser = argparse.ArgumentParser(
        description="Convert an emoji to a favicon SVG or PNG"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to lit_up_config.yaml (reads favicon from config)",
    )
    parser.add_argument(
        "--emoji",
        help=(
            "The emoji to convert (e.g., 🎵, 🔥, etc.) "
            "- required if --config not used"
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output file path " "(default: favicon.svg or favicon.png based on format)"
        ),
    )
    parser.add_argument(
        "-s",
        "--size",
        type=int,
        default=32,
        help="Size in pixels (default: 32)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["svg", "png"],
        default="svg",
        help="Output format: svg or png (default: svg)",
    )

    args = parser.parse_args()

    # Get emoji from config or argument
    emoji = None
    if args.config:
        config = load_config(args.config)
        emoji = config.get("favicon", "♍️")
    elif args.emoji:
        emoji = args.emoji
    else:
        parser.error("Either --config or --emoji must be provided")

    if not emoji:
        print("Error: No emoji found in config or provided", file=sys.stderr)
        sys.exit(1)

    # Determine output file path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"favicon.{args.format}")

    # Generate output based on format
    if args.format == "svg":
        content = emoji_to_svg_text(emoji, args.size)
        output_path.write_text(content, encoding="utf-8")
    elif args.format == "png":
        png_bytes = emoji_to_png(emoji, args.size)
        output_path.write_bytes(png_bytes)

    size_str = f"{args.size}x{args.size}"
    format_upper = args.format.upper()
    print(f"✓ Created {output_path} ({size_str}px) as {format_upper}")


if __name__ == "__main__":
    main()
