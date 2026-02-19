"""Tests for concepts API."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_concept(mock_publish_event, mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.base_resource.run_read_query", mock_run_read_query), patch(
        "app.api.base_resource.publish_event", mock_publish_event
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/concepts", json={"name": "Magic", "description": "World concept"})
    assert r.status_code == 202
    assert "id" in r.json()["payload"]
    mock_publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_list_concepts(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "concept-1", "name": "Magic", "description": "World"}]
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/concepts")
    assert r.status_code == 200
    assert r.json()[0]["name"] == "Magic"


@pytest.mark.asyncio
async def test_get_concept_not_found(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/concepts/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_concept(mock_publish_event):
    with patch("app.api.base_resource.publish_event", mock_publish_event):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/concepts/concept-1", json={"description": "Updated"})
    assert r.status_code == 202
    assert r.json()["payload"]["id"] == "concept-1"
    mock_publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_update_concept_empty_body_400():
    """Update with neither name nor description returns 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.patch("/api/concepts/concept-1", json={})
    assert r.status_code == 400
    assert "at least one" in r.json()["detail"].lower()


# --- Uniqueness (case/whitespace insensitive) ---


@pytest.mark.asyncio
async def test_create_concept_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/concepts", json={"name": "Magic", "description": "Other"})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_concept_same_name_extra_spaces_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/concepts", json={"name": "  magic  ", "description": "x"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_concept_empty_name_400(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/concepts", json={"name": "  ", "description": "x"})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_concept_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "other-id"}]
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/concepts/concept-1", json={"name": "Existing"})
    assert r.status_code == 409
