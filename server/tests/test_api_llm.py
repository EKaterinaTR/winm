"""Tests for LLM API (stub when no credentials, GigaChat when configured)."""
import pytest
from unittest.mock import patch, AsyncMock

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_llm_answer_no_credentials(mock_run_read_query):
    """Without GIGACHAT_CREDENTIALS returns stub message."""
    mock_run_read_query.return_value = [{"type": "Location", "name": "Tavern"}]
    with patch("app.services.llm_context.run_read_query", mock_run_read_query):
        with patch("app.api.llm.settings") as mock_settings:
            mock_settings.gigachat_credentials = None
            mock_settings.llm_service_url = None
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.post(
                    "/api/llm/answer",
                    json={"question": "What happened?", "role": "narrator"},
                )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "LLM не настроен" in data["answer"]
    assert data["role"] == "narrator"


@pytest.mark.asyncio
async def test_llm_answer_with_gigachat(mock_run_read_query):
    """With credentials and mocked GigaChat returns model answer."""
    mock_run_read_query.return_value = [{"type": "Character", "name": "Hero"}]
    with patch("app.services.llm_context.run_read_query", mock_run_read_query):
        with patch("app.api.llm.settings") as mock_settings:
            mock_settings.gigachat_credentials = "test-key"
            mock_settings.llm_service_url = None
            with patch("app.api.llm._call_gigachat_local", return_value="Mocked GigaChat reply"):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    r = await client.post(
                        "/api/llm/answer",
                        json={"question": "Кто ты?", "role": "narrator"},
                    )
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Mocked GigaChat reply"
    assert data["role"] == "narrator"


@pytest.mark.asyncio
async def test_llm_answer_via_llm_service(mock_run_read_query):
    """When LLM_SERVICE_URL is set, calls LLM service and returns its answer."""
    mock_run_read_query.return_value = [{"type": "Character", "name": "Hero"}]
    with patch("app.services.llm_context.run_read_query", mock_run_read_query):
        with patch("app.api.llm.settings") as mock_settings:
            mock_settings.gigachat_credentials = None
            mock_settings.llm_service_url = "http://llm:8001"
            with patch("app.api.llm._call_llm_service", new_callable=AsyncMock, return_value="Reply from LLM service"):
                transport = ASGITransport(app=app)
                async with AsyncClient(transport=transport, base_url="http://test") as client:
                    r = await client.post(
                        "/api/llm/answer",
                        json={"question": "Кто ты?", "role": "narrator"},
                    )
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "Reply from LLM service"
    assert data["role"] == "narrator"


@pytest.mark.asyncio
async def test_llm_answer_character_role(mock_run_read_query):
    """Character role: context from graph (mocked), stub when no credentials."""
    # First call: character by id; second: scenes
    mock_run_read_query.side_effect = [
        [{"name": "Alice", "description": "Main character"}],
        [],
    ]
    with patch("app.services.llm_context.run_read_query", mock_run_read_query):
        with patch("app.api.llm.settings") as mock_settings:
            mock_settings.gigachat_credentials = None
            mock_settings.llm_service_url = None
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.post(
                    "/api/llm/answer",
                    json={"question": "Where are you?", "role": "char-uuid-123"},
                )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["role"] == "char-uuid-123"
