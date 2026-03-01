"""Tests for LLM API: 202 + request_id, GET /result/:id."""
import pytest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_llm_answer_returns_202_and_request_id():
    """POST /api/llm/answer returns 202 with request_id (task in queue)."""
    with patch("app.api.llm.publish_llm_task"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/llm/answer",
                json={"question": "What happened?", "role": "narrator"},
            )
    assert r.status_code == 202
    data = r.json()
    assert "request_id" in data
    assert len(data["request_id"]) > 0


@pytest.mark.asyncio
async def test_llm_generate_returns_202_and_request_id():
    """POST /api/llm/generate returns 202 with request_id."""
    with patch("app.api.llm.publish_llm_task"):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post(
                "/api/llm/generate",
                json={"entity_type": "location", "prompt": "таверна"},
            )
    assert r.status_code == 202
    data = r.json()
    assert "request_id" in data


@pytest.mark.asyncio
async def test_llm_result_pending():
    """GET /api/llm/result/:id returns pending when no result yet."""
    with patch("app.api.llm.get_result", return_value=None):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/llm/result/some-uuid")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "pending"
    assert data["request_id"] == "some-uuid"


@pytest.mark.asyncio
async def test_llm_result_done_knowledge():
    """GET /api/llm/result/:id returns answer when knowledge result ready."""
    with patch("app.api.llm.get_result", return_value={
        "request_id": "rid-1",
        "status": "done",
        "type": "knowledge",
        "answer": "Mocked answer",
        "role": "narrator",
    }):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/llm/result/rid-1")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "done"
    assert data["type"] == "knowledge"
    assert data["answer"] == "Mocked answer"


@pytest.mark.asyncio
async def test_llm_result_done_generate():
    """GET /api/llm/result/:id returns payload when generate result ready."""
    with patch("app.api.llm.get_result", return_value={
        "request_id": "rid-2",
        "status": "done",
        "type": "generate",
        "entity_type": "location",
        "payload": {"name": "Таверна", "description": "Уютная таверна"},
    }):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/llm/result/rid-2")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "done"
    assert data["type"] == "generate"
    assert data["entity_type"] == "location"
    assert data["payload"]["name"] == "Таверна"


@pytest.mark.asyncio
async def test_llm_result_error():
    """GET /api/llm/result/:id returns error when task failed."""
    with patch("app.api.llm.get_result", return_value={
        "request_id": "rid-3",
        "status": "error",
        "error": "LLM timeout",
    }):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/llm/result/rid-3")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "error"
    assert "timeout" in data["error"].lower()
