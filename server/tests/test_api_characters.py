"""Tests for characters API."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_character(mock_publish_event, mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.characters.run_read_query", mock_run_read_query), patch(
        "app.api.characters.publish_event", mock_publish_event
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/characters", json={"name": "Alice", "description": "Hero"})
    assert r.status_code == 202
    data = r.json()
    assert "id" in data["payload"]
    assert data["payload"]["name"] == "Alice"
    mock_publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_list_characters(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "c1", "name": "Alice", "description": "Hero"}]
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/characters")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_get_character_not_found(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/characters/nonexistent")
    assert r.status_code == 404


# --- Uniqueness (case/whitespace insensitive) ---


@pytest.mark.asyncio
async def test_create_character_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/characters", json={"name": "Alice", "description": "Other"})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_character_same_name_different_case_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/characters", json={"name": "ALICE", "description": "Other"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_character_empty_name_400(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/characters", json={"name": "\t  \n", "description": "x"})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_character_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "other-id"}]
    with patch("app.api.characters.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/characters/c1", json={"name": "Bob"})
    assert r.status_code == 409
