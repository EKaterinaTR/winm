"""Tests for search API."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_search(mock_run_read_query):
    mock_run_read_query.return_value = [
        {"type": "Location", "id": "loc-1", "name": "Tavern", "snippet": "A cozy place"},
    ]
    with patch("app.api.search.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/search", params={"q": "tavern"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["type"] == "Location"
    assert r.json()[0]["name"] == "Tavern"


@pytest.mark.asyncio
async def test_search_case_insensitive_cyrillic(mock_run_read_query):
    """Search is case-insensitive for Cyrillic (e.g. 'Таверна' finds 'таверна')."""
    mock_run_read_query.return_value = [
        {"type": "Location", "id": "loc-1", "name": "таверна", "snippet": "первое место"},
    ]
    with patch("app.api.search.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/search", params={"q": "Таверна"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "таверна"


@pytest.mark.asyncio
async def test_search_empty_query():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/search", params={"q": ""})
    assert r.status_code == 422
