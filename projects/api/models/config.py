"""
Shared config DTOs for Lit Up API.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_serializer


class Track(BaseModel):
    id: str
    src: str
    title: str
    artist: str
    duration: str
    cover: str
    isSecret: bool


class ConcatenatedPlaylistTrack(BaseModel):
    id: str
    title: str
    artist: str
    startTime: Decimal
    endTime: Decimal
    duration: Decimal

    @field_serializer("startTime", "endTime", "duration", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class ConcatenatedPlaylist(BaseModel):
    enabled: bool
    file: str
    tracks: list[ConcatenatedPlaylistTrack]
    totalDuration: Decimal

    @field_serializer("totalDuration", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)


class AppConfig(BaseModel):
    tracks: list[Track]
    headerMessage: Annotated[str, Field(min_length=0)]
    buildDatetime: str
    buildHash: str
    concatenatedPlaylist: ConcatenatedPlaylist
