"""Story (scenes) API."""
import uuid

from fastapi import APIRouter, HTTPException

from app.core.graph import run_read_query
from app.core.broker import publish_event
from app.core.validation import normalize_name
from app.metrics import events_published_total
from app.models.schemas import SceneCreate, SceneUpdate, SceneRead
from shared.events import EventType

router = APIRouter(prefix="/story", tags=["story"])


@router.post("/scenes", status_code=202)
async def create_scene(body: SceneCreate) -> dict:
    """Create scene (publish event, consumer writes to graph). Title unique (case/whitespace insensitive)."""
    title_norm = normalize_name(body.title)
    if not title_norm:
        raise HTTPException(status_code=400, detail="Title cannot be empty after trimming")
    existing = await run_read_query(
        "MATCH (s:Scene) WHERE toLower(trim(s.title)) = $title_norm RETURN s.id AS id LIMIT 1",
        {"title_norm": title_norm},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Scene with this title already exists")
    payload = {
        "id": str(uuid.uuid4()),
        "title": body.title.strip(),
        "description": body.description,
        "location_id": body.location_id,
        "character_ids": body.character_ids,
    }
    publish_event(EventType.SCENE_CREATE, payload)
    events_published_total.labels(event_type=EventType.SCENE_CREATE.value).inc()
    return {"status": "accepted", "payload": payload}


@router.get("/scenes", response_model=list[SceneRead])
async def list_scenes() -> list[SceneRead]:
    """List all scenes from graph."""
    records = await run_read_query("""
        MATCH (s:Scene)-[:TAKES_PLACE_IN]->(l:Location)
        OPTIONAL MATCH (s)-[:FEATURES]->(c:Character)
        WITH s, l, collect(c.id) AS char_ids
        RETURN s.id AS id, s.title AS title, s.description AS description,
               l.id AS location_id, char_ids AS character_ids
    """)
    return [
        SceneRead(
            id=r["id"],
            title=r["title"],
            description=r.get("description") or "",
            location_id=r["location_id"],
            character_ids=[x for x in (r.get("character_ids") or []) if x],
        )
        for r in records
    ]


@router.get("/scenes/{scene_id}", response_model=SceneRead)
async def get_scene(scene_id: str) -> SceneRead:
    """Get scene by id."""
    records = await run_read_query("""
        MATCH (s:Scene {id: $id})-[:TAKES_PLACE_IN]->(l:Location)
        OPTIONAL MATCH (s)-[:FEATURES]->(c:Character)
        WITH s, l, collect(c.id) AS char_ids
        RETURN s.id AS id, s.title AS title, s.description AS description,
               l.id AS location_id, char_ids AS character_ids
    """, {"id": scene_id})
    if not records:
        raise HTTPException(status_code=404, detail="Scene not found")
    r = records[0]
    return SceneRead(
        id=r["id"],
        title=r["title"],
        description=r.get("description") or "",
        location_id=r["location_id"],
        character_ids=[x for x in (r.get("character_ids") or []) if x],
    )


@router.patch("/scenes/{scene_id}", status_code=202)
async def update_scene(scene_id: str, body: SceneUpdate) -> dict:
    """Update scene (publish event)."""
    payload = {"id": scene_id}
    if body.title is not None:
        payload["title"] = body.title
    if body.description is not None:
        payload["description"] = body.description
    if body.location_id is not None:
        payload["location_id"] = body.location_id
    if body.character_ids is not None:
        payload["character_ids"] = body.character_ids
    publish_event(EventType.SCENE_UPDATE, payload)
    events_published_total.labels(event_type=EventType.SCENE_UPDATE.value).inc()
    return {"status": "accepted", "payload": payload}
