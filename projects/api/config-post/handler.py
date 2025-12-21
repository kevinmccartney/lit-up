"""
Lambda handler for POST /config endpoint.
Writes playlist config to DynamoDB.
"""

import json
import logging
import os
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, ValidationError, field_serializer

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
CONFIG_TABLE_NAME = os.environ.get("CONFIG_TABLE_NAME", "lit-up-dev-configs")

# Common response headers
JSON_HEADERS = {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
}


# Pydantic models for the config structure
class Track(BaseModel):
    """Track definition."""

    id: str
    src: str
    title: str
    artist: str
    duration: str
    cover: str
    isSecret: bool


class ConcatenatedPlaylistTrack(BaseModel):
    """Concatenated playlist track definition."""

    id: str
    title: str
    artist: str
    startTime: Decimal
    endTime: Decimal
    duration: Decimal

    @field_serializer("startTime", "endTime", "duration", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(value)


class ConcatenatedPlaylist(BaseModel):
    """Concatenated playlist definition."""

    enabled: bool
    file: str
    tracks: list[ConcatenatedPlaylistTrack]
    totalDuration: Decimal

    @field_serializer("totalDuration", when_used="json")
    def serialize_decimal(self, value: Decimal) -> float:
        """Serialize Decimal to float for JSON."""
        return float(value)


class AppConfig(BaseModel):
    """App configuration structure."""

    tracks: list[Track]
    headerMessage: str
    buildDatetime: str
    buildHash: str
    concatenatedPlaylist: ConcatenatedPlaylist


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


def _maybe_wait_for_debugger() -> None:
    """
    Optionally wait for a debugger to attach (local development only).

    Enable with env vars:
    - DEBUGPY_ENABLE=1
    - DEBUGPY_WAIT_FOR_CLIENT=1
    - DEBUGPY_HOST=0.0.0.0
    - DEBUGPY_PORT=5890
    """

    debug_enabled = os.environ.get("DEBUGPY_ENABLE") in {"1", "true", "TRUE", "True"}
    if not debug_enabled:
        return

    wait = os.environ.get("DEBUGPY_WAIT_FOR_CLIENT") in {"1", "true", "TRUE", "True"}
    # Use stderr so this shows up even when INFO logs are suppressed.
    debug_host = os.environ.get("DEBUGPY_HOST", "0.0.0.0")
    debug_port = os.environ.get("DEBUGPY_PORT", "5890")
    print(
        f"[debugpy] enabled wait_for_client={wait} host={debug_host} port={debug_port}",
        flush=True,
    )

    try:
        import importlib

        debugpy = importlib.import_module("debugpy")
    except Exception:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        logger.warning("DEBUGPY_ENABLE set but debugpy is not installed")
        return

    host = os.environ.get("DEBUGPY_HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("DEBUGPY_PORT", "5890"))
    except ValueError:
        port = 5890

    try:
        debugpy.listen((host, port))
    except OSError:
        # When SAM is run with `-d`, it may already have bound the debug port.
        # In that case, just proceed to wait_for_client below.
        logger.exception("debugpy failed to listen on %s:%s (continuing)", host, port)

    if wait:
        print("[debugpy] waiting for debugger attach...", flush=True)
        debugpy.wait_for_client()


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
    _maybe_wait_for_debugger()
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

        # Get version from query string or default to "v1"
        # Version handling is at infrastructure level, but we accept it as query param
        query_params = event.get("queryStringParameters") or {}
        version = query_params.get("version", "v1")

        # Convert Pydantic model to dict for DynamoDB storage
        # Use model_dump() to keep Decimals (required by DynamoDB)
        config_dict = config.model_dump()

        # Write config to DynamoDB
        table = dynamodb.Table(CONFIG_TABLE_NAME)
        item = {
            "version": version,
            "config": config_dict,  # Store as JSON dict (DynamoDB will handle it)
        }
        table.put_item(Item=item)

        logger.info("Saved config version=%s table=%s", version, CONFIG_TABLE_NAME)

        # Convert back to JSON-serializable format (floats) for response
        # Use model_dump(mode='json') to apply field serializers (Decimal -> float)
        config_dict_json = config.model_dump(mode="json")
        response_item = {
            "version": version,
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
