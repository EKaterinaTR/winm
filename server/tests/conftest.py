"""Pytest fixtures: app, client, mocks."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Async HTTP client for FastAPI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_run_read_query():
    """Mock Neo4j run_read_query (use with patch in test)."""
    return AsyncMock()


@pytest.fixture
def mock_publish_event():
    """Mock RabbitMQ publish_event (use with patch in test)."""
    return MagicMock()
