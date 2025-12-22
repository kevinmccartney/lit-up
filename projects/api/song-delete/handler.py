"""
Lambda handler for DELETE /songs/{id} endpoint.
Deletes a song record from the DynamoDB music table.
"""

from __future__ import annotations

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

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
    """Delete a song by id."""
    try:
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        song_id = path_params.get("id") or query_params.get("id")

        if not song_id:
            return _create_response(
                400,
                {
                    "error": "Bad request",
                    "message": "Song id is required (path /songs/{id} or query param ?id=...)",  # noqa: E501 pylint: disable=line-too-long
                },
            )

        table = dynamodb.Table(MUSIC_TABLE_NAME)
        resp = table.delete_item(
            Key=_song_key(song_id),
            ReturnValues="ALL_OLD",
        )
        deleted_item = resp.get("Attributes")

        if not deleted_item:
            return _create_response(
                404,
                {
                    "error": "Not found",
                    "message": "Song not found",
                    "id": song_id,
                },
            )

        deleted_song = _to_jsonable(
            {k: v for k, v in deleted_item.items() if k not in {"PK", "SK", "type"}}
        )
        return _create_response(
            200,
            {
                "id": song_id,
                "deleted": True,
                "song": deleted_song,
            },
        )

    except ClientError:
        logger.exception("DynamoDB error while deleting song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to delete song from database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while deleting song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Unexpected error",
            },
        )
