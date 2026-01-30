"""Search API (query graph)."""
from fastapi import APIRouter, Query

from app.core.graph import run_read_query
from app.metrics import neo4j_queries_total
from app.models.schemas import SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResult])
async def search(q: str = Query(..., min_length=1)) -> list[SearchResult]:
    """Search locations, characters, scenes, concepts by name/description."""
    neo4j_queries_total.labels(operation="search").inc()
    pattern = f"(?i).*{q.replace(' ', '.*')}.*"
    params = {"pattern": pattern}
    records = await run_read_query("""
        MATCH (n)
        WHERE n:Location OR n:Character OR n:Scene OR n:Concept
        AND (n.name =~ $pattern OR (n.description IS NOT NULL AND n.description =~ $pattern))
        RETURN labels(n)[0] AS type, n.id AS id, n.name AS name,
               COALESCE(n.description, n.title, '') AS snippet
        LIMIT 50
    """, params)
    return [
        SearchResult(type=r["type"], id=r["id"], name=r["name"], snippet=r.get("snippet") or "")
        for r in records
    ]
