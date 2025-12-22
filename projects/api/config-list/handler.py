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
CONFIG_TABLE_NAME = os.environ.get("CONFIG_TABLE_NAME", "lit-up-dev-configs")

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


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    try:
        table = dynamodb.Table(CONFIG_TABLE_NAME)
        resp = table.scan()
        items = resp.get("Items", [])
        configs = [
            {"id": item.get("id"), "config": _to_jsonable(item.get("config"))}
            for item in items
        ]

        return _create_response(
            200,
            {
                "count": len(configs),
                "items": configs,
            },
        )

    except ClientError:
        logger.exception("DynamoDB error while listing configs")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to list configs from database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while listing configs")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Unexpected error",
            },
        )
