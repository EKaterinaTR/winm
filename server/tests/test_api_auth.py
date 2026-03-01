"""Tests for auth API: token issue and JWT protection."""
import pytest
from unittest.mock import patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.auth import get_current_user, create_access_token


async def _mock_get_current_user():
    return {"sub": "test"}


@pytest.mark.asyncio
async def test_get_token_success():
    """POST /api/auth/token with valid credentials returns JWT."""
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.api_username = "api"
        mock_settings.api_password = "api"
        app.dependency_overrides[get_current_user] = _mock_get_current_user
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.post(
                    "/api/auth/token",
                    json={"username": "api", "password": "api"},
                )
            assert r.status_code == 200
            data = r.json()
            assert data["token_type"] == "bearer"
            assert "access_token" in data
            assert len(data["access_token"]) > 0
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_token_invalid_password():
    """POST /api/auth/token with wrong password returns 401."""
    with patch("app.api.auth.settings") as mock_settings:
        mock_settings.api_username = "api"
        mock_settings.api_password = "secret"
        app.dependency_overrides[get_current_user] = _mock_get_current_user
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.post(
                    "/api/auth/token",
                    json={"username": "api", "password": "wrong"},
                )
            assert r.status_code == 401
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_returns_401():
    """Without auth override, /api/locations without Bearer token returns 401."""
    app.dependency_overrides.clear()
    try:
        with patch("app.auth.settings") as mock_settings:
            mock_settings.auth_disabled = False
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get("/api/locations")
            assert r.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = _mock_get_current_user


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(mock_run_read_query):
    """With valid Bearer token, /api/locations returns 200."""
    mock_run_read_query.return_value = []
    with patch("app.api.base_resource.run_read_query", mock_run_read_query):
        token = create_access_token(sub="api")
        app.dependency_overrides.clear()
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                r = await client.get(
                    "/api/locations",
                    headers={"Authorization": f"Bearer {token}"},
                )
            assert r.status_code == 200
        finally:
            app.dependency_overrides[get_current_user] = _mock_get_current_user
