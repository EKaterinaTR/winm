"""Pytest fixtures: app, client, mocks."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.auth import get_current_user


async def _mock_get_current_user():
    """В тестах не проверяем JWT — подставляем пользователя."""
    return {"sub": "test"}


@pytest.fixture(autouse=True)
def override_auth():
    """Все тесты API выполняются с «подставным» пользователем (JWT не требуется)."""
    app.dependency_overrides[get_current_user] = _mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_llm_results_consumer():
    """Не запускать поток потребления llm.results в тестах."""
    from unittest.mock import patch
    with patch("app.main.start_llm_results_consumer"):
        yield


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
