"""Characters API."""
import uuid

from fastapi import APIRouter, HTTPException

from app.core.graph import run_read_query
from app.core.broker import publish_event
from app.core.validation import normalize_name
from app.metrics import events_published_total
from app.models.schemas import CharacterCreate, CharacterUpdate, CharacterRead
from shared.events import EventType

router = APIRouter(prefix="/characters", tags=["characters"])


@router.post("", status_code=202)
async def create_character(body: CharacterCreate) -> dict:
    """Create character (publish event). Name unique (case/whitespace insensitive)."""
    name_norm = normalize_name(body.name)
    if not name_norm:
        raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
    existing = await run_read_query(
        "MATCH (n:Character) WHERE toLower(trim(n.name)) = $name_norm RETURN n.id AS id LIMIT 1",
        {"name_norm": name_norm},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Character with this name already exists")
    payload = {"id": str(uuid.uuid4()), "name": body.name.strip(), "description": body.description}
    publish_event(EventType.CHARACTER_CREATE, payload)
    events_published_total.labels(event_type=EventType.CHARACTER_CREATE.value).inc()
    return {"status": "accepted", "payload": payload}


@router.get("", response_model=list[CharacterRead])
async def list_characters() -> list[CharacterRead]:
    """List all characters from graph."""
    records = await run_read_query(
        "MATCH (n:Character) RETURN n.id AS id, n.name AS name, n.description AS description"
    )
    return [CharacterRead(id=r["id"], name=r["name"], description=r.get("description") or "") for r in records]


@router.get("/{character_id}", response_model=CharacterRead)
async def get_character(character_id: str) -> CharacterRead:
    """Get character by id."""
    records = await run_read_query(
        "MATCH (n:Character {id: $id}) RETURN n.id AS id, n.name AS name, n.description AS description",
        {"id": character_id},
    )
    if not records:
        raise HTTPException(status_code=404, detail="Character not found")
    r = records[0]
    return CharacterRead(id=r["id"], name=r["name"], description=r.get("description") or "")


@router.patch("/{character_id}", status_code=202)
async def update_character(character_id: str, body: CharacterUpdate) -> dict:
    """Update character (publish event). New name must be unique (case/whitespace insensitive)."""
    payload = {"id": character_id}
    if body.name is not None:
        name_norm = normalize_name(body.name)
        if not name_norm:
            raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
        existing = await run_read_query(
            "MATCH (n:Character) WHERE toLower(trim(n.name)) = $name_norm AND n.id <> $id RETURN n.id AS id LIMIT 1",
            {"name_norm": name_norm, "id": character_id},
        )
        if existing:
            raise HTTPException(status_code=409, detail="Character with this name already exists")
        payload["name"] = body.name.strip()
    if body.description is not None:
        payload["description"] = body.description
    publish_event(EventType.CHARACTER_UPDATE, payload)
    events_published_total.labels(event_type=EventType.CHARACTER_UPDATE.value).inc()
    return {"status": "accepted", "payload": payload}
