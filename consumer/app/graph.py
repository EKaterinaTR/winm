"""Neo4j write operations (consumer)."""
import uuid
from typing import Any

from neo4j import GraphDatabase

from app.config import settings

_driver = None


def get_driver():
    """Get or create Neo4j sync driver."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


def run_write(query: str, parameters: dict[str, Any] | None = None) -> None:
    """Execute write Cypher."""
    driver = get_driver()
    parameters = parameters or {}
    with driver.session() as session:
        session.run(query, parameters)


def run_read(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Execute read Cypher. Returns list of records (dict per row)."""
    driver = get_driver()
    parameters = parameters or {}
    with driver.session() as session:
        result = session.run(query, parameters)
        return [dict(record) for record in result]


def ensure_id(payload: dict) -> str:
    """Ensure payload has id; generate if missing."""
    if "id" in payload and payload["id"]:
        return payload["id"]
    return str(uuid.uuid4())


# --- Base node writer (Location, Character, Concept: id, name, description) ---


class NameNodeWriter:
    """Base class for graph nodes with id, name, description."""

    label: str = ""

    def create(self, payload: dict) -> str:
        uid = ensure_id(payload)
        run_write(
            f"MERGE (n:{self.label} {{id: $id}}) SET n.name = $name, n.description = $description",
            {"id": uid, "name": payload.get("name", ""), "description": payload.get("description", "")},
        )
        return uid

    def update(self, payload: dict) -> str:
        uid = payload["id"]
        updates = []
        params = {"id": uid}
        if "name" in payload:
            updates.append("n.name = $name")
            params["name"] = payload["name"]
        if "description" in payload:
            updates.append("n.description = $description")
            params["description"] = payload["description"]
        if updates:
            run_write(f"MATCH (n:{self.label} {{id: $id}}) SET {', '.join(updates)}", params)
        return uid


class LocationWriter(NameNodeWriter):
    label = "Location"


class CharacterWriter(NameNodeWriter):
    label = "Character"


class ConceptWriter(NameNodeWriter):
    label = "Concept"


_location_writer = LocationWriter()
_character_writer = CharacterWriter()
_concept_writer = ConceptWriter()


def create_location(payload: dict) -> str:
    return _location_writer.create(payload)


def update_location(payload: dict) -> str:
    return _location_writer.update(payload)


def create_character(payload: dict) -> str:
    return _character_writer.create(payload)


def update_character(payload: dict) -> str:
    return _character_writer.update(payload)


def create_concept(payload: dict) -> str:
    return _concept_writer.create(payload)


def update_concept(payload: dict) -> str:
    return _concept_writer.update(payload)


# --- Scene (custom logic: relationships) ---


def create_scene(payload: dict) -> str:
    """Create Scene node and relationships. Returns id."""
    uid = ensure_id(payload)
    title = payload.get("title", "")
    description = payload.get("description", "")
    location_id = payload.get("location_id", "")
    character_ids = payload.get("character_ids") or []
    run_write(
        """
        MERGE (s:Scene {id: $id}) SET s.title = $title, s.description = $description
        WITH s
        OPTIONAL MATCH (l:Location {id: $location_id})
        FOREACH (_ IN CASE WHEN l IS NOT NULL THEN [1] ELSE [] END |
            MERGE (s)-[:TAKES_PLACE_IN]->(l)
        )
        """,
        {"id": uid, "title": title, "description": description, "location_id": location_id},
    )
    for cid in character_ids:
        if not cid:
            continue
        run_write(
            """
            MATCH (s:Scene {id: $scene_id})
            MATCH (c:Character {id: $char_id})
            MERGE (s)-[:FEATURES]->(c)
            """,
            {"scene_id": uid, "char_id": cid},
        )
    return uid


def search_graph(q: str) -> list[dict[str, Any]]:
    """Поиск по графу (локации, персонажи, сцены, понятия). Как в server search API."""
    q_norm = (q or "").strip().lower().replace(" ", ".*")
    pattern = f".*{q_norm}.*" if q_norm else ".*"
    params = {"pattern": pattern}
    records = run_read("""
        MATCH (n)
        WHERE (n:Location OR n:Character OR n:Scene OR n:Concept)
        AND (
            (n.name IS NOT NULL AND toLower(trim(n.name)) =~ $pattern)
            OR (n.title IS NOT NULL AND toLower(trim(n.title)) =~ $pattern)
            OR (n.description IS NOT NULL AND toLower(trim(n.description)) =~ $pattern)
        )
        RETURN labels(n)[0] AS type, n.id AS id,
               COALESCE(n.name, n.title, '') AS name,
               COALESCE(n.description, n.title, '') AS snippet
        LIMIT 50
    """, params)
    return records


def update_scene(payload: dict) -> str:
    """Update Scene node and relationships. Returns id."""
    uid = payload["id"]
    params = {"id": uid}
    updates = []
    if "title" in payload:
        updates.append("s.title = $title")
        params["title"] = payload["title"]
    if "description" in payload:
        updates.append("s.description = $description")
        params["description"] = payload["description"]
    if updates:
        run_write(f"MATCH (s:Scene {{id: $id}}) SET {', '.join(updates)}", params)
    if "location_id" in payload:
        run_write(
            """
            MATCH (s:Scene {id: $id})
            OPTIONAL MATCH (s)-[r:TAKES_PLACE_IN]->()
            DELETE r
            WITH s
            MATCH (l:Location {id: $location_id})
            MERGE (s)-[:TAKES_PLACE_IN]->(l)
            """,
            {"id": uid, "location_id": payload["location_id"]},
        )
    if "character_ids" in payload:
        run_write("MATCH (s:Scene {id: $id}) OPTIONAL MATCH (s)-[r:FEATURES]->() DELETE r", {"id": uid})
        for cid in payload["character_ids"] or []:
            if not cid:
                continue
            run_write(
                """
                MATCH (s:Scene {id: $scene_id})
                MATCH (c:Character {id: $char_id})
                MERGE (s)-[:FEATURES]->(c)
                """,
                {"scene_id": uid, "char_id": cid},
            )
    return uid
