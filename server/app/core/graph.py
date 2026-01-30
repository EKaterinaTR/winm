"""Neo4j graph client for read operations (server). Write operations go via consumer."""
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings


_driver: AsyncDriver | None = None


async def get_driver() -> AsyncDriver:
    """Get or create Neo4j async driver."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


async def close_driver() -> None:
    """Close Neo4j driver."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def run_read_query(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Execute read-only Cypher and return list of records as dicts."""
    driver = await get_driver()
    parameters = parameters or {}
    async with driver.session() as session:
        result = await session.run(query, parameters)
        records = await result.data()
    return records


async def run_write_query(query: str, parameters: dict[str, Any] | None = None) -> None:
    """Execute write Cypher (used only for idempotent/read-heavy writes from server if needed)."""
    driver = await get_driver()
    parameters = parameters or {}
    async with driver.session() as session:
        await session.run(query, parameters)
