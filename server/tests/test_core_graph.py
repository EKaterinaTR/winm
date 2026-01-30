"""Tests for core graph (Neo4j client)."""
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.core.graph import run_read_query, run_write_query, close_driver


@pytest.mark.asyncio
async def test_run_read_query():
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[{"n": 1}])
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_driver = MagicMock()
    mock_driver.session.return_value = mock_session
    with patch("app.core.graph.get_driver", new_callable=AsyncMock, return_value=mock_driver):
        result = await run_read_query("RETURN 1", {})
    assert result == [{"n": 1}]


@pytest.mark.asyncio
async def test_close_driver_no_driver():
    with patch("app.core.graph._driver", None):
        await close_driver()


@pytest.mark.asyncio
async def test_close_driver_with_driver():
    mock_driver = AsyncMock()
    with patch("app.core.graph._driver", mock_driver):
        await close_driver()
        mock_driver.close.assert_called_once()


@pytest.mark.asyncio
async def test_run_write_query():
    mock_session = MagicMock()
    mock_session.run = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_driver = MagicMock()
    mock_driver.session.return_value = mock_session
    with patch("app.core.graph.get_driver", new_callable=AsyncMock, return_value=mock_driver):
        await run_write_query("CREATE (n:Test {id: $id})", {"id": "1"})
    mock_session.run.assert_called_once()
