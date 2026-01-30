"""Tests for locations API."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_location(mock_publish_event, mock_run_read_query):
    mock_run_read_query.return_value = []  # no duplicate
    with patch("app.api.locations.run_read_query", mock_run_read_query), patch(
        "app.api.locations.publish_event", mock_publish_event
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/locations", json={"name": "Tavern", "description": "A cozy tavern"})
    assert r.status_code == 202
    data = r.json()
    assert data["status"] == "accepted"
    assert "id" in data["payload"]
    assert data["payload"]["name"] == "Tavern"
    assert data["payload"]["description"] == "A cozy tavern"
    mock_publish_event.assert_called_once()


@pytest.mark.asyncio
async def test_list_locations(mock_run_read_query):
    mock_run_read_query.return_value = [
        {"id": "loc-1", "name": "Tavern", "description": "A tavern"},
    ]
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/locations")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["id"] == "loc-1"
    assert r.json()[0]["name"] == "Tavern"


@pytest.mark.asyncio
async def test_get_location(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "loc-1", "name": "Tavern", "description": "A tavern"}]
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/locations/loc-1")
    assert r.status_code == 200
    assert r.json()["id"] == "loc-1"


@pytest.mark.asyncio
async def test_get_location_not_found(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/locations/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_location(mock_publish_event, mock_run_read_query):
    mock_run_read_query.return_value = []  # no other location with that name
    with patch("app.api.locations.run_read_query", mock_run_read_query), patch(
        "app.api.locations.publish_event", mock_publish_event
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/locations/loc-1", json={"name": "New Tavern"})
    assert r.status_code == 202
    assert r.json()["payload"]["id"] == "loc-1"
    assert r.json()["payload"]["name"] == "New Tavern"
    mock_publish_event.assert_called_once()


# --- Uniqueness (case/whitespace insensitive) ---


@pytest.mark.asyncio
async def test_create_location_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]  # duplicate exists
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/locations", json={"name": "таверна", "description": "First"})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_location_same_name_different_case_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]  # "Таверна" already exists
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/locations", json={"name": "Таверна", "description": "Other"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_location_same_name_extra_spaces_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "existing-id"}]
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/locations", json={"name": "  таверна  ", "description": "Other"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_create_location_empty_name_400(mock_run_read_query):
    mock_run_read_query.return_value = []
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/api/locations", json={"name": "   ", "description": "Empty"})
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_location_duplicate_name_409(mock_run_read_query):
    mock_run_read_query.return_value = [{"id": "other-id"}]  # other location has this name
    with patch("app.api.locations.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/locations/loc-1", json={"name": "Tavern"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_location_same_name_ok(mock_publish_event, mock_run_read_query):
    mock_run_read_query.return_value = []  # no OTHER location with that name (same id excluded in query)
    with patch("app.api.locations.run_read_query", mock_run_read_query), patch(
        "app.api.locations.publish_event", mock_publish_event
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.patch("/api/locations/loc-1", json={"name": "Same Name"})
    assert r.status_code == 202
    mock_publish_event.assert_called_once()
