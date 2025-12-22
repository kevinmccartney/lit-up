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
        path_params = event.get("pathParameters") or {}
        query_params = event.get("queryStringParameters") or {}
        config_id = path_params.get("id") or query_params.get("id")

        if not config_id:
            return _create_response(
                400,
                {
                    "error": "Bad request",
                    "message": (
                        "Config id is required "
                        "(path /configs/{id} or query param ?id=...)"
                    ),
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
                {"error": "Bad request", "message": "Config payload must be an object"},
            )

        table = dynamodb.Table(CONFIG_TABLE_NAME)

        # Ensure item exists before updating
        existing = table.get_item(Key={"id": config_id}).get("Item")
        if not existing:
            return _create_response(
                404,
                {
                    "error": "Not found",
                    "message": "Config not found",
                    "id": config_id,
                },
            )

        # Replace the config with provided payload
        # (PATCH semantics: client sends fields to replace)
        update_resp = table.update_item(
            Key={"id": config_id},
            UpdateExpression="SET #c = :c",
            ExpressionAttributeNames={"#c": "config"},
            ExpressionAttributeValues={":c": body},
            ReturnValues="ALL_NEW",
        )

        updated_item = update_resp.get("Attributes", {})
        updated_config = _to_jsonable(updated_item.get("config"))

        return _create_response(
            200,
            {
                "id": config_id,
                "config": updated_config,
            },
        )

    except ClientError:
        logger.exception("DynamoDB error while patching config")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to update config in database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while patching config")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Unexpected error",
            },
        )
