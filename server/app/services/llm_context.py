"""Build LLM context from graph (by role: character id or narrator)."""
from app.core.graph import run_read_query


async def get_llm_context(role: str | None) -> str:
    """
    Fetch context from Neo4j for the given role.
    - If role is a character id: character name, description, scenes and locations they appear in.
    - If role is "narrator" or empty: short world summary (locations, characters, concepts).
    """
    role = (role or "").strip() or "narrator"
    if role.lower() == "narrator":
        return await _narrator_context()
    return await _character_context(role)


async def _narrator_context() -> str:
    """World overview: counts and names of locations, characters, concepts."""
    records = await run_read_query("""
        MATCH (n)
        WHERE n:Location OR n:Character OR n:Concept
        RETURN labels(n)[0] AS type, COALESCE(n.name, n.title, n.id) AS name
        LIMIT 50
    """)
    if not records:
        return "Мир пока пуст (нет локаций, персонажей и понятий в графе)."
    by_type: dict[str, list[str]] = {}
    for r in records:
        t = r.get("type") or "Node"
        name = r.get("name") or ""
        by_type.setdefault(t, []).append(name)
    parts = []
    for t in ("Location", "Character", "Concept"):
        if t in by_type:
            parts.append(f"{t}: {', '.join(by_type[t][:15])}" + (" ..." if len(by_type[t]) > 15 else ""))
    return "Контекст мира (граф): " + "; ".join(parts) if parts else "Нет данных."


async def _character_context(character_id: str) -> str:
    """Character profile and related scenes/locations."""
    char_records = await run_read_query(
        "MATCH (c:Character {id: $id}) RETURN c.name AS name, c.description AS description",
        {"id": character_id},
    )
    if not char_records:
        return f"Персонаж с id '{character_id}' не найден в графе."
    c = char_records[0]
    name = c.get("name") or character_id
    desc = c.get("description") or ""
    lines = [f"Персонаж: {name}.", desc] if desc else [f"Персонаж: {name}."]
    scene_records = await run_read_query("""
        MATCH (c:Character {id: $id})<-[:FEATURES]-(s:Scene)
        OPTIONAL MATCH (s)-[:TAKES_PLACE_IN]->(l:Location)
        RETURN s.title AS scene_title, s.description AS scene_desc, l.name AS location_name
        LIMIT 10
    """, {"id": character_id})
    if scene_records:
        scene_parts = []
        for r in scene_records:
            title = r.get("scene_title") or "Сцена"
            loc = r.get("location_name")
            scene_parts.append(f"{title}" + (f" (локация: {loc})" if loc else ""))
        lines.append("Участвует в сценах: " + "; ".join(scene_parts))
    return " ".join(lines)
