"""
Shared helpers for the `projects/api/scripts/*` scripts.

Kept as a plain module in the scripts directory so it can be imported when scripts
are executed directly (the script directory is on `sys.path`).
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, cast

import yaml
from mutagen import File, MutagenError

_FILENAME_FORBIDDEN_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def create_filename_from_id(value: Any, extension: str = "mp3") -> str:
    """Create a filesystem-safe filename from an id-like value."""
    safe_id = _FILENAME_FORBIDDEN_CHARS_RE.sub("_", str(value))
    return f"{safe_id}.{extension}"


def format_duration(seconds: float | None) -> str:
    """Format duration in seconds to M:SS (rounded to nearest second)."""
    if seconds is None:
        return "0:00"

    total_seconds = max(0, int(seconds + 0.5))
    minutes = total_seconds // 60
    remaining_seconds = total_seconds % 60
    return f"{minutes}:{remaining_seconds:02d}"


def write_bytes_atomic(path: Path, data: bytes) -> None:
    """Write bytes to a file via temp file + atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(data)
        tmp_file.flush()
    tmp_path.replace(path)


def save_json_atomic(path: Path, data: dict[str, Any], *, indent: int = 2) -> None:
    """Write JSON via temp file + atomic replace to avoid partial writes."""
    parent_dir = path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=parent_dir,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        json.dump(data, tmp_file, indent=indent)
        tmp_file.write("\n")

    tmp_path.replace(path)


def save_yaml_atomic(path: Path, data: dict[str, Any]) -> None:
    """Write YAML via temp file + atomic replace to avoid partial writes."""
    parent_dir = path.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        delete=False,
        dir=parent_dir,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as tmp_file:
        tmp_path = Path(tmp_file.name)
        yaml.safe_dump(
            data,
            tmp_file,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    tmp_path.replace(path)


class ConfigError(Exception):
    """Raised when a config file can't be read or has unexpected structure."""


def load_yaml_dict(path: Path) -> dict[str, Any]:
    """Load a YAML file and require the root to be a dict."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"Error reading YAML file: {path}: {e}") from e

    if not isinstance(data, dict):
        raise ConfigError(f"YAML root must be a mapping/dict: {path}")

    return cast(dict[str, Any], data)


def require_list_field(
    data: dict[str, Any],
    key: str,
    *,
    context: str = "config",
) -> list[Any]:
    """Return `data[key]` if it is a list; otherwise raise ConfigError."""
    value = data.get(key)
    if not isinstance(value, list):
        raise ConfigError(f"{context}: '{key}' must be a list")
    return value


def get_mp3_duration(mp3_file_path: Path) -> float | None:
    """Return MP3 duration in seconds, or None if it can't be determined."""
    try:
        audio_file = File(mp3_file_path)
        if audio_file is not None and hasattr(audio_file, "info"):
            return float(audio_file.info.length)
        return None
    except (MutagenError, OSError, ValueError):
        return None
