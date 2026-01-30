"""Tests for story (scenes) API."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_scene(mock_publish_event):
    with patch("app.api.story.publish_event", mock_publish_event):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/story/scenes",
                json={
                    "title": "Meeting",
                    "description": "They meet.",
                    "location_id": "loc-1",
                    "character_ids": ["c1", "c2"],
                },
            )
    assert r.status_code == 202
    data = r.json()
    assert "id" in data["payload"]
    assert data["payload"]["title"] == "Meeting"
    assert data["payload"]["location_id"] == "loc-1"
    mock_publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_list_scenes(mock_run_read_query):
    mock_run_read_query.return_value = [
        {
            "id": "s1",
            "title": "Meeting",
            "description": "They meet.",
            "location_id": "loc-1",
            "character_ids": ["c1"],
        },
    ]
    with patch("app.api.story.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/story/scenes")
    assert r.status_code == 200
    assert r.json()[0]["title"] == "Meeting"


@pytest.mark.asyncio
async def test_get_scene_not_found(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.story.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/story/scenes/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_scene(mock_publish_event):
    with patch("app.api.story.publish_event", mock_publish_event):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch(
                "/api/story/scenes/s1",
                json={"title": "Updated", "location_id": "loc-2"},
            )
    assert r.status_code == 202
    assert r.json()["payload"]["id"] == "s1"
    mock_publish_event.assert_called_once()
