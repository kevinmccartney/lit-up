"""
Lambda handler for POST /config endpoint.
Writes playlist config to DynamoDB.
"""

import importlib
import json
import logging
import os
import uuid
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError
from pydantic import ValidationError

if TYPE_CHECKING:
    from models.config import AppConfig
else:
    AppConfig = importlib.import_module("models.config").AppConfig  # type: ignore[attr-defined]

# CloudWatch captures stdout/stderr; Python logging uses stderr by default.
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())

# Initialize DynamoDB client
#
# Local development note:
# - Set DYNAMODB_ENDPOINT_URL to point at DynamoDB Local / LocalStack, e.g.
#   http://host.docker.internal:8000
# - Keep it unset in AWS so boto3 uses the real AWS endpoint.
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
CONFIG_PK_VALUE = "CONFIG"

# Common response headers
JSON_HEADERS = {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
}


def _config_key(config_id: str) -> dict[str, str]:
    """Build the composite key for a config item."""
    return {"PK": CONFIG_PK_VALUE, "SK": f"CONFIG#{config_id}"}


def _create_response(
    status_code: int,
    body: dict[str, Any] | list[Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create an API Gateway proxy response.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON encoded)
        headers: Optional additional headers (merged with JSON_HEADERS)

    Returns:
        API Gateway proxy response format
    """
    response_headers = {**JSON_HEADERS, **(headers or {})}
    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json.dumps(body),
    }


def _parse_request_body(event: dict[str, Any]) -> dict[str, Any]:
    """
    Parse the request body from API Gateway event.

    Args:
        event: API Gateway event

    Returns:
        Parsed request body as dict

    Raises:
        ValueError: If body is missing or invalid JSON
    """
    body = event.get("body")
    if not body:
        raise ValueError("Request body is required")

    # API Gateway may base64 encode the body, but for JSON it's usually plain text
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in request body: {e}") from e

    if isinstance(body, dict):
        return body

    raise ValueError("Request body must be valid JSON")


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """
    Lambda handler for API Gateway proxy integration.
    Writes config to DynamoDB.

    Args:
        event: API Gateway event
        context: Lambda context (unused)

    Returns:
        API Gateway proxy response format
    """
    try:
        # Parse request body
        try:
            body_data = _parse_request_body(event)
        except ValueError as e:
            logger.warning("Bad request: %s", e)
            return _create_response(
                400,
                {
                    "error": "Bad request",
                    "message": str(e),
                },
            )

        # Validate with Pydantic
        try:
            config = AppConfig.model_validate(body_data)
        except ValidationError as e:
            logger.warning("Validation error: %s", e)
            return _create_response(
                400,
                {
                    "error": "Validation error",
                    "message": "Invalid config structure",
                    "details": e.errors(),
                },
            )

        # Generate a unique ID for this config record
        config_id = str(uuid.uuid4())

        # Convert Pydantic model to dict for DynamoDB storage
        # Use model_dump() to keep Decimals (required by DynamoDB)
        config_dict = config.model_dump()

        # Write config to DynamoDB
        table = dynamodb.Table(MUSIC_TABLE_NAME)
        item = {
            **_config_key(config_id),
            "id": config_id,
            "type": "CONFIG",
            "config": config_dict,  # Store as JSON dict (DynamoDB will handle it)
        }
        table.put_item(Item=item)

        logger.info("Saved config id=%s table=%s", config_id, MUSIC_TABLE_NAME)

        # Convert back to JSON-serializable format (floats) for response
        # Use model_dump(mode='json') to apply field serializers (Decimal -> float)
        config_dict_json = config.model_dump(mode="json")
        response_item = {
            "id": config_id,
            "config": config_dict_json,
        }

        # Return the saved item with the database ID (version)
        return _create_response(
            200,
            response_item,
        )

    except ClientError:
        logger.exception("DynamoDB error while saving config")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                "message": "Failed to write config to database",
            },
        )
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.exception("Unexpected error while saving config")
        return _create_response(
            500,
            {
                "error": "Internal server error",
                # Don't leak internals to clients; stack trace is in logs.
                "message": "Unexpected error",
            },
        )
