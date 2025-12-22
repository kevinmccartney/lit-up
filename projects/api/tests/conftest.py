"""Shared pytest fixtures for API E2E tests."""

from __future__ import annotations

import os
from collections.abc import Generator

import httpx
import pytest


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "e2e: End-to-end API tests")
    config.addinivalue_line(
        "markers", "local: Tests that run against local Flask server"
    )
    config.addinivalue_line(
        "markers", "deployed: Tests that run against deployed API Gateway"
    )


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Get the API base URL from environment variable.

    Defaults to local Flask server. Set API_BASE_URL env var to test against
    deployed API Gateway (e.g., https://api.example.com/dev).
    """
    return os.getenv("API_BASE_URL", "http://127.0.0.1:3000")


@pytest.fixture(scope="session")
def api_key() -> str | None:
    """
    Get API key from environment variable (required for deployed API Gateway).

    Not needed for local Flask server.
    """
    return os.getenv("API_KEY")


@pytest.fixture(scope="session")
def api_client(api_base_url: str, api_key: str | None) -> Generator[httpx.Client]:
    """
    HTTP client for API tests.

    Automatically includes API key header if provided (for deployed API Gateway).
    Verifies server connectivity before yielding.
    """
    headers: dict[str, str] = {}
    if api_key:
        headers["x-api-key"] = api_key

    with httpx.Client(
        base_url=api_base_url,
        headers=headers,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        # Verify server is reachable and returns JSON (not HTML 404)
        try:
            # Try a simple GET request to see if server responds with JSON
            # For local Flask, we'll get a 404 HTML page if routes aren't registered
            # For deployed API Gateway, we'll get a proper JSON error
            test_response = client.get("/configs", timeout=5.0)
            # If we get HTML, the server isn't properly configured
            content_type = test_response.headers.get("content-type", "")
            if "text/html" in content_type and test_response.status_code == 404:
                raise ConnectionError(
                    f"Server at {api_base_url} returned HTML 404. "
                    "This usually means:\n"
                    "  - For local testing: Flask server isn't running. "
                    "Run 'task up' first.\n"
                    "  - For deployed testing: API Gateway URL is incorrect "
                    "or routes aren't deployed."
                )
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to API server at {api_base_url}. "
                "Make sure the server is running.\n"
                f"  For local testing: Run 'task up' in another terminal.\n"
                f"  Original error: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise ConnectionError(
                f"Timeout connecting to API server at {api_base_url}. "
                "Server may be unreachable or slow.\n"
                f"  Original error: {e}"
            ) from e

        yield client


@pytest.fixture
def sample_config() -> dict:
    """Sample config payload for testing."""
    return {
        "tracks": [
            {
                "id": "t1",
                "src": "/songs/t1.mp3",
                "title": "Test Track 1",
                "artist": "Test Artist",
                "duration": "00:30",
                "cover": "/album_art/t1.jpg",
                "isSecret": False,
            }
        ],
        "headerMessage": "E2E Test Config",
        "buildDatetime": "2025-01-01T00:00:00Z",
        "buildHash": "test-hash",
        "concatenatedPlaylist": {
            "enabled": False,
            "file": "/playlist.mp3",
            "tracks": [],
            "totalDuration": 0,
        },
    }


@pytest.fixture
def created_config_id(api_client: httpx.Client, sample_config: dict) -> Generator[str]:
    """
    Create a test config and yield its ID, clean up after test.

    This fixture creates a config via POST /configs and yields the ID.
    After the test, it attempts to delete the config (best effort).
    """
    # Create config
    response = api_client.post("/configs", json=sample_config)
    assert response.status_code == 200, f"Failed to create config: {response.text}"
    config_id = response.json()["id"]
    assert config_id, "Config ID should not be empty"

    yield config_id

    # Cleanup: attempt to delete (ignore errors in case test already deleted it)
    try:
        api_client.delete(f"/configs/{config_id}")
    except Exception:  # noqa: BLE001
        pass  # Best effort cleanup


@pytest.fixture
def config_cleanup(api_client: httpx.Client) -> Generator[list[str], None, None]:
    """
    Collect config IDs created during a test and delete them afterwards.
    """
    created: list[str] = []
    try:
        yield created
    finally:
        for config_id in created:
            try:
                api_client.delete(f"/configs/{config_id}")
            except Exception:  # noqa: BLE001
                pass


@pytest.fixture
def sample_song_payload() -> dict[str, str]:
    """Sample song payload for creation."""
    return {
        "audio_origin_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "artist": "E2E Artist",
        "title": "E2E Title",
        "album_art_origin_url": "https://images.example.com/song-123.jpg",
    }


@pytest.fixture
def song_cleanup(api_client: httpx.Client) -> Generator[list[str], None, None]:
    """
    Collect song IDs created during a test and delete them afterwards.
    """
    created: list[str] = []
    try:
        yield created
    finally:
        for song_id in created:
            try:
                api_client.delete(f"/songs/{song_id}")
            except Exception:  # noqa: BLE001
                pass
