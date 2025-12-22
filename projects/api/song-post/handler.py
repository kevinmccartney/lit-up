"""
Lambda handler for POST /songs endpoint.
Creates a song record in the DynamoDB music table.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Any

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

AWS_REGION = (
    os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
)
DYNAMODB_ENDPOINT_URL = os.environ.get("DYNAMODB_ENDPOINT_URL")
_boto_session = boto3.session.Session(region_name=AWS_REGION)
dynamodb = (
    _boto_session.resource("dynamodb", endpoint_url=DYNAMODB_ENDPOINT_URL)
    if DYNAMODB_ENDPOINT_URL
    else _boto_session.resource("dynamodb")
)
MUSIC_TABLE_NAME = os.environ.get("MUSIC_TABLE_NAME", "lit-up-dev-music")
SONG_PK_VALUE = "SONG"

JSON_HEADERS = {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
}


class SongCreate(BaseModel):
    """Song payload for creation (only user-supplied fields)."""

    audio_origin_url: Annotated[str, Field(min_length=1)]
    album_art_origin_url: Annotated[str, Field(min_length=1)]
    artist: Annotated[str, Field(min_length=1)]
    title: Annotated[str, Field(min_length=1)]


def _create_response(
    status_code: int,
    body: dict[str, Any] | list[Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response_headers = {**JSON_HEADERS, **(headers or {})}
    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json.dumps(body),
    }


def _to_jsonable(value: Any) -> Any:
    """Recursively convert DynamoDB Decimals to JSON-serializable numbers."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [_to_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


def _song_key(song_id: str) -> dict[str, str]:
    """Build the composite key for a song item."""
    return {"PK": SONG_PK_VALUE, "SK": f"SONG#{song_id}"}


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Create a song record."""
    try:
        raw_body = event.get("body")
        if not raw_body:
            return _create_response(
                400,
                {"error": "Bad request", "message": "Request body is required"},
            )

        try:
            body = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
        except json.JSONDecodeError:
            return _create_response(
                400,
                {"error": "Bad request", "message": "Request body must be JSON"},
            )

        try:
            song_payload = SongCreate.model_validate(body or {})
        except ValidationError as e:
            logger.warning("Validation error: %s", e)
            return _create_response(
                400,
                {
                    "error": "Validation error",
                    "message": "Invalid song structure",
                    "details": e.errors(),
                },
            )

        song_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        table = dynamodb.Table(MUSIC_TABLE_NAME)
        item = {
            **_song_key(song_id),
            "id": song_id,
            "type": "SONG",
            "audioOriginUrl": song_payload.audio_origin_url,
            "audioUrl": None,
            "length": None,
            "lengthSeconds": None,
            "artist": song_payload.artist,
            "title": song_payload.title,
            "albumArtOriginUrl": song_payload.album_art_origin_url,
            "albumArtUrl": None,
            "status": "new",
            "createdAt": now_iso,
            "updatedAt": now_iso,
        }

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(PK) AND attribute_not_exists(SK)",
        )

        response_item = _to_jsonable(item)
        return _create_response(200, response_item)

    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _create_response(
                409,
                {
                    "error": "Conflict",
                    "message": "Song with this id already exists",
                },
            )
        logger.exception("DynamoDB error while creating song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to create song in database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while creating song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Unexpected error",
            },
        )
