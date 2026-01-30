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


def ensure_id(payload: dict) -> str:
    """Ensure payload has id; generate if missing."""
    if "id" in payload and payload["id"]:
        return payload["id"]
    return str(uuid.uuid4())


def create_location(payload: dict) -> str:
    """Create Location node. Returns id."""
    uid = ensure_id(payload)
    run_write(
        "MERGE (n:Location {id: $id}) SET n.name = $name, n.description = $description",
        {"id": uid, "name": payload.get("name", ""), "description": payload.get("description", "")},
    )
    return uid


def update_location(payload: dict) -> str:
    """Update Location node. Returns id."""
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
        run_write(f"MATCH (n:Location {{id: $id}}) SET {', '.join(updates)}", params)
    return uid


def create_character(payload: dict) -> str:
    """Create Character node. Returns id."""
    uid = ensure_id(payload)
    run_write(
        "MERGE (n:Character {id: $id}) SET n.name = $name, n.description = $description",
        {"id": uid, "name": payload.get("name", ""), "description": payload.get("description", "")},
    )
    return uid


def update_character(payload: dict) -> str:
    """Update Character node. Returns id."""
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
        run_write(f"MATCH (n:Character {{id: $id}}) SET {', '.join(updates)}", params)
    return uid


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


def create_concept(payload: dict) -> str:
    """Create Concept node. Returns id."""
    uid = ensure_id(payload)
    run_write(
        "MERGE (n:Concept {id: $id}) SET n.name = $name, n.description = $description",
        {"id": uid, "name": payload.get("name", ""), "description": payload.get("description", "")},
    )
    return uid


def update_concept(payload: dict) -> str:
    """Update Concept node. Returns id."""
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
        run_write(f"MATCH (n:Concept {{id: $id}}) SET {', '.join(updates)}", params)
    return uid
