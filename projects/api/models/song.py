"""
Shared song DTOs for Lit Up API.
"""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, Field


class SongCreate(BaseModel):
    """Fields accepted on song creation (POST /songs)."""

    audio_origin_url: Annotated[str, Field(min_length=1)]
    album_art_origin_url: Annotated[str, Field(min_length=1)]
    artist: Annotated[str, Field(min_length=1)]
    title: Annotated[str, Field(min_length=1)]


class SongPatch(BaseModel):
    """Fields accepted on song patch (PATCH /songs/{id})."""

    audio_origin_url: Annotated[str | None, Field(min_length=1)] = None
    album_art_origin_url: Annotated[str | None, Field(min_length=1)] = None
    artist: Annotated[str | None, Field(min_length=1)] = None
    title: Annotated[str | None, Field(min_length=1)] = None

    def to_update_map(self) -> dict[str, Any]:
        """Return only provided fields with DB key names."""
        field_map = {
            "audio_origin_url": "audioOriginUrl",
            "album_art_origin_url": "albumArtOriginUrl",
            "artist": "artist",
            "title": "title",
        }
        updates: dict[str, Any] = {}
        for field, db_key in field_map.items():
            value = getattr(self, field)
            if value is not None:
                updates[db_key] = value
        return updates


class SongRecord(BaseModel):
    """Canonical representation of a song as stored/returned."""

    id: str
    audioOriginUrl: str
    audioUrl: str | None
    length: str | None
    lengthSeconds: float | None
    artist: str
    title: str
    albumArtUrl: str | None
    albumArtOriginUrl: str
    status: str
    createdAt: str
    updatedAt: str
