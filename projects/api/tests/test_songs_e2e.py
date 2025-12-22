"""E2E tests for /songs endpoints."""

from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
class TestSongsE2E:
    """End-to-end tests for song CRUD operations."""

    def test_post_song_creates_new_song(
        self,
        api_client: httpx.Client,
        sample_song_payload: dict,
        song_cleanup: list[str],
    ) -> None:
        response = api_client.post("/songs", json=sample_song_payload)

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        song_id = data["id"]
        song_cleanup.append(song_id)

        assert isinstance(song_id, str) and song_id
        assert data["audioOriginUrl"] == sample_song_payload["audio_origin_url"]
        assert data["audioUrl"] is None
        assert data["length"] is None
        assert data["lengthSeconds"] is None
        assert data["albumArtUrl"] is None
        assert data["albumArtOriginUrl"] == sample_song_payload["album_art_origin_url"]
        assert data["status"] == "new"
        assert "updatedAt" in data and "createdAt" in data

    def test_get_song_returns_existing_song(
        self,
        api_client: httpx.Client,
        sample_song_payload: dict,
        song_cleanup: list[str],
    ) -> None:
        create_resp = api_client.post("/songs", json=sample_song_payload)
        assert create_resp.status_code == 200
        song_id = create_resp.json()["id"]
        song_cleanup.append(song_id)

        get_resp = api_client.get(f"/songs/{song_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == song_id
        song = data["song"]
        assert song["audioOriginUrl"] == sample_song_payload["audio_origin_url"]
        assert song["audioUrl"] is None
        assert song["length"] is None
        assert song["lengthSeconds"] is None
        assert song["albumArtUrl"] is None
        assert song["albumArtOriginUrl"] == sample_song_payload["album_art_origin_url"]
        assert song["status"] == "new"
        assert "PK" not in song and "SK" not in song and "type" not in song

    def test_patch_song_updates_allowed_fields(
        self,
        api_client: httpx.Client,
        sample_song_payload: dict,
        song_cleanup: list[str],
    ) -> None:
        create_resp = api_client.post("/songs", json=sample_song_payload)
        assert create_resp.status_code == 200
        song_id = create_resp.json()["id"]
        song_cleanup.append(song_id)

        patch_payload = {
            "title": "E2E Title Updated",
            "artist": "E2E Artist Updated",
            "album_art_origin_url": "https://images.example.com/song-123-updated.jpg",
            "audio_origin_url": "https://youtube.com/watch?v=updated123",
        }
        patch_resp = api_client.patch(f"/songs/{song_id}", json=patch_payload)
        assert patch_resp.status_code == 200, f"PATCH failed: {patch_resp.text}"
        patched_song = patch_resp.json()["song"]

        assert patched_song["title"] == patch_payload["title"]
        assert patched_song["artist"] == patch_payload["artist"]
        assert (
            patched_song["albumArtOriginUrl"] == patch_payload["album_art_origin_url"]
        )
        assert patched_song["audioOriginUrl"] == patch_payload["audio_origin_url"]
        assert patched_song["audioUrl"] is None
        assert patched_song["status"] == "new"
        assert patched_song["length"] is None
        assert patched_song["lengthSeconds"] is None
        assert patched_song["albumArtUrl"] is None
        patched_updated_at = patched_song["updatedAt"]

        # GET reflects patch
        get_after_patch = api_client.get(f"/songs/{song_id}")
        assert get_after_patch.status_code == 200
        body = get_after_patch.json()["song"]
        assert body["title"] == patch_payload["title"]
        assert body["artist"] == patch_payload["artist"]
        assert body["albumArtOriginUrl"] == patch_payload["album_art_origin_url"]
        assert body["audioOriginUrl"] == patch_payload["audio_origin_url"]
        assert body["updatedAt"] == patched_updated_at
        assert body["audioUrl"] is None
        assert body["status"] == "new"
        assert body["length"] is None
        assert body["lengthSeconds"] is None
        assert body["albumArtUrl"] is None

    def test_delete_song_removes_existing_song(
        self, api_client: httpx.Client, sample_song_payload: dict
    ) -> None:
        create_resp = api_client.post("/songs", json=sample_song_payload)
        assert create_resp.status_code == 200
        song_id = create_resp.json()["id"]

        del_resp = api_client.delete(f"/songs/{song_id}")
        assert del_resp.status_code == 200, f"DELETE failed: {del_resp.text}"
        data = del_resp.json()
        assert data["id"] == song_id
        assert data.get("deleted") is True
        assert data["song"]["audioOriginUrl"] == sample_song_payload["audio_origin_url"]
        assert data["song"]["audioUrl"] is None
        assert data["song"]["length"] is None
        assert data["song"]["lengthSeconds"] is None
        assert data["song"]["albumArtUrl"] is None
        assert (
            data["song"]["albumArtOriginUrl"]
            == sample_song_payload["album_art_origin_url"]
        )
        assert data["song"]["status"] == "new"

        missing_resp = api_client.get(f"/songs/{song_id}")
        assert missing_resp.status_code == 404

    def test_list_songs_includes_created(
        self,
        api_client: httpx.Client,
        sample_song_payload: dict,
        song_cleanup: list[str],
    ) -> None:
        # Create two songs
        resp1 = api_client.post("/songs", json=sample_song_payload)
        assert resp1.status_code == 200
        song_id1 = resp1.json()["id"]
        song_cleanup.append(song_id1)

        resp2 = api_client.post(
            "/songs",
            json={
                **sample_song_payload,
                "title": "Another Song",
                "audio_origin_url": "https://youtube.com/watch?v=another123",
            },
        )
        assert resp2.status_code == 200
        song_id2 = resp2.json()["id"]
        song_cleanup.append(song_id2)

        list_resp = api_client.get("/songs")
        assert list_resp.status_code == 200, f"LIST failed: {list_resp.text}"
        data = list_resp.json()
        assert "items" in data and isinstance(data["items"], list)
        ids = {item["id"] for item in data["items"]}
        assert song_id1 in ids
        assert song_id2 in ids
