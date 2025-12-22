"""
Lambda handler for PATCH /songs/{id} endpoint.
Updates allowed song fields in the DynamoDB music table.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
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

# Fields that can be updated via PATCH
ALLOWED_FIELDS = {
    "audio_origin_url": "audioOriginUrl",
    "album_art_origin_url": "albumArtOriginUrl",
    "artist": "artist",
    "title": "title",
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
    """Patch allowed fields of a song."""
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

        raw_body = event.get("body")
        if raw_body in (None, ""):
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

        if not isinstance(body, dict):
            return _create_response(
                400,
                {"error": "Bad request", "message": "Payload must be an object"},
            )

        update_fields: dict[str, Any] = {}
        for api_name, db_name in ALLOWED_FIELDS.items():
            if api_name in body:
                update_fields[db_name] = body[api_name]

        if not update_fields:
            return _create_response(
                400,
                {
                    "error": "Bad request",
                    "message": "No patchable fields provided",
                    "allowed_fields": list(ALLOWED_FIELDS.keys()),
                },
            )

        now_iso = datetime.now(timezone.utc).isoformat()

        table = dynamodb.Table(MUSIC_TABLE_NAME)
        # Ensure item exists
        existing = table.get_item(Key=_song_key(song_id)).get("Item")
        if not existing:
            return _create_response(
                404,
                {"error": "Not found", "message": "Song not found", "id": song_id},
            )

        # Build update expression
        expr_names = {"#updatedAt": "updatedAt"}
        expr_values = {":updatedAt": now_iso}
        set_clauses = ["#updatedAt = :updatedAt"]

        for idx, (db_name, value) in enumerate(update_fields.items()):
            name_key = f"#f{idx}"
            value_key = f":v{idx}"
            expr_names[name_key] = db_name
            expr_values[value_key] = value
            set_clauses.append(f"{name_key} = {value_key}")

        update_expr = "SET " + ", ".join(set_clauses)

        resp = table.update_item(
            Key=_song_key(song_id),
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=expr_values,
            ReturnValues="ALL_NEW",
        )

        updated_item = resp.get("Attributes", {})
        updated_json = _to_jsonable(updated_item)
        return _create_response(
            200,
            {
                "id": song_id,
                "song": {
                    k: v
                    for k, v in updated_json.items()
                    if k not in {"PK", "SK", "type"}
                },
            },
        )

    except ClientError:
        logger.exception("DynamoDB error while patching song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to update song in database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while patching song")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Unexpected error",
            },
        )
