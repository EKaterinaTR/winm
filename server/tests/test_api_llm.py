"""Tests for LLM stub API."""
import pytest
from unittest.mock import patch, AsyncMock

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_llm_answer_stub(mock_run_read_query):
    mock_run_read_query.return_value = [{"c": 0}]
    with patch("app.api.llm.run_read_query", mock_run_read_query):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/llm/answer",
                json={"question": "What happened?", "role": "narrator"},
            )
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "Stub" in data["answer"]
    assert data["role"] == "narrator"
