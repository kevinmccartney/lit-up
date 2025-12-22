"""E2E tests for /configs endpoints."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
class TestConfigsE2E:
    """End-to-end tests for config CRUD operations."""

    def test_post_config_creates_new_config(
        self,
        api_client: httpx.Client,
        sample_config: dict,
        config_cleanup: list[str],
    ) -> None:
        """Test POST /configs creates a new config and returns an ID."""
        response = api_client.post("/configs", json=sample_config)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Response should include 'id'"
        assert isinstance(data["id"], str), "ID should be a string"
        assert len(data["id"]) > 0, "ID should not be empty"
        assert "config" in data, "Response should include 'config'"
        assert data["config"] == sample_config, "Returned config should match request"
        config_cleanup.append(data["id"])

    def test_get_config_retrieves_existing_config(
        self, api_client: httpx.Client, created_config_id: str, sample_config: dict
    ) -> None:
        """Test GET /configs/{id} retrieves an existing config."""
        response = api_client.get(f"/configs/{created_config_id}")

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == created_config_id, "Returned ID should match"
        assert "config" in data, "Response should include 'config'"
        assert data["config"] == sample_config, "Returned config should match original"

    def test_get_config_returns_404_for_nonexistent_id(
        self, api_client: httpx.Client
    ) -> None:
        """Test GET /configs/{id} returns 404 for non-existent config."""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"/configs/{nonexistent_id}")

        assert (
            response.status_code == 404
        ), f"Expected 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "error" in data, "Error response should include 'error'"
        assert data["error"] == "Not found", "Error message should indicate not found"

    def test_patch_config_updates_existing_config(
        self, api_client: httpx.Client, created_config_id: str
    ) -> None:
        """Test PATCH /configs/{id} updates an existing config."""
        updated_config = {
            "headerMessage": "Updated via PATCH",
            "tracks": [],
        }

        response = api_client.patch(
            f"/configs/{created_config_id}", json=updated_config
        )

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["id"] == created_config_id, "Returned ID should match"
        assert "config" in data, "Response should include 'config'"
        assert (
            data["config"]["headerMessage"] == "Updated via PATCH"
        ), "Config should be updated"

        # Verify update persisted
        get_response = api_client.get(f"/configs/{created_config_id}")
        assert get_response.status_code == 200
        assert get_response.json()["config"]["headerMessage"] == "Updated via PATCH"

    def test_patch_config_returns_404_for_nonexistent_id(
        self, api_client: httpx.Client
    ) -> None:
        """Test PATCH /configs/{id} returns 404 for non-existent config."""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.patch(
            f"/configs/{nonexistent_id}", json={"headerMessage": "test"}
        )

        assert (
            response.status_code == 404
        ), f"Expected 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "error" in data, "Error response should include 'error'"
        assert data["error"] == "Not found", "Error message should indicate not found"

    def test_delete_config_removes_existing_config(
        self, api_client: httpx.Client, sample_config: dict
    ) -> None:
        """Test DELETE /configs/{id} removes an existing config."""
        # Create a config to delete
        create_response = api_client.post("/configs", json=sample_config)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"/configs/{config_id}")

        assert (
            delete_response.status_code == 200
        ), f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        data = delete_response.json()
        assert data["id"] == config_id, "Returned ID should match"
        assert data.get("deleted") is True, "Response should indicate deletion"
        assert "config" in data, "Response should include deleted config"

        # Verify it's gone
        get_response = api_client.get(f"/configs/{config_id}")
        assert get_response.status_code == 404, "Config should no longer exist"

    def test_delete_config_returns_404_for_nonexistent_id(
        self, api_client: httpx.Client
    ) -> None:
        """Test DELETE /configs/{id} returns 404 for non-existent config."""
        nonexistent_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.delete(f"/configs/{nonexistent_id}")

        assert (
            response.status_code == 404
        ), f"Expected 404, got {response.status_code}: {response.text}"
        data = response.json()
        assert "error" in data, "Error response should include 'error'"
        assert data["error"] == "Not found", "Error message should indicate not found"

    def test_list_configs_returns_list_with_created_configs(
        self, api_client: httpx.Client, sample_config: dict
    ) -> None:
        """Test GET /configs returns a list that includes configs we create."""
        # Create a couple of configs
        create1 = api_client.post("/configs", json=sample_config)
        assert create1.status_code == 200
        config_id1 = create1.json()["id"]

        sample_config2 = {**sample_config, "headerMessage": "Second Config"}
        create2 = api_client.post("/configs", json=sample_config2)
        assert create2.status_code == 200
        config_id2 = create2.json()["id"]

        try:
            # List all configs (may include other configs from other tests/users)
            list_response = api_client.get("/configs")

            assert (
                list_response.status_code == 200
            ), f"Expected 200, got {list_response.status_code}: {list_response.text}"
            data = list_response.json()
            assert isinstance(
                data, dict
            ), "Response should be a dict with 'count' and 'items'"
            assert "count" in data, "Response should have 'count' field"
            assert "items" in data, "Response should have 'items' field"
            assert isinstance(data["items"], list), "Response 'items' should be a list"

            items = data["items"]
            # Verify our configs are in the list
            # (don't assume anything about other configs)
            config_ids = [item["id"] for item in items]
            assert config_id1 in config_ids, "First config we created should be in list"
            assert (
                config_id2 in config_ids
            ), "Second config we created should be in list"

            # Verify the structure of items in the list
            config1_item = next(item for item in items if item["id"] == config_id1)
            assert "id" in config1_item, "List items should have 'id'"
            assert "config" in config1_item, "List items should have 'config'"
            assert (
                config1_item["config"] == sample_config
            ), "List item config should match what we created"

        finally:
            # Cleanup
            api_client.delete(f"/configs/{config_id1}")
            api_client.delete(f"/configs/{config_id2}")

    def test_list_configs_returns_list_structure(
        self, api_client: httpx.Client
    ) -> None:
        """Test GET /configs returns a properly structured list."""
        # Don't assume anything about existing configs in the database
        # Just verify the endpoint works and returns the expected structure
        response = api_client.get("/configs")

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(
            data, dict
        ), "Response should be a dict with 'count' and 'items'"
        assert "count" in data, "Response should have 'count' field"
        assert "items" in data, "Response should have 'items' field"
        assert isinstance(data["items"], list), "Response 'items' should be a list"
        assert isinstance(data["count"], int), "Count should be an integer"
        assert data["count"] == len(data["items"]), "Count should match items length"

        # If there are any items, verify their structure
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "id" in item, "List items should have 'id' field"
            assert "config" in item, "List items should have 'config' field"
            assert isinstance(item["id"], str), "ID should be a string"
            assert isinstance(item["config"], dict), "Config should be a dict"

    def test_full_crud_workflow(
        self, api_client: httpx.Client, sample_config: dict
    ) -> None:
        """Test complete CRUD workflow: create, read, update, delete."""
        # CREATE
        create_response = api_client.post("/configs", json=sample_config)
        assert create_response.status_code == 200
        config_id = create_response.json()["id"]

        try:
            # READ
            get_response = api_client.get(f"/configs/{config_id}")
            assert get_response.status_code == 200
            assert get_response.json()["config"] == sample_config

            # UPDATE
            updated_config = {**sample_config, "headerMessage": "Updated"}
            patch_response = api_client.patch(
                f"/configs/{config_id}", json=updated_config
            )
            assert patch_response.status_code == 200

            # Verify update
            get_updated = api_client.get(f"/configs/{config_id}")
            assert get_updated.status_code == 200
            assert get_updated.json()["config"]["headerMessage"] == "Updated"

        finally:
            # DELETE
            delete_response = api_client.delete(f"/configs/{config_id}")
            assert delete_response.status_code == 200

            # Verify deletion
            get_deleted = api_client.get(f"/configs/{config_id}")
            assert get_deleted.status_code == 404
