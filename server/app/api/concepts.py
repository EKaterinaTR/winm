"""Concepts API."""
import uuid

from fastapi import APIRouter, HTTPException

from app.core.graph import run_read_query
from app.core.broker import publish_event
from app.core.validation import normalize_name
from app.metrics import events_published_total
from app.models.schemas import ConceptCreate, ConceptUpdate, ConceptRead
from shared.events import EventType

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.post("", status_code=202)
async def create_concept(body: ConceptCreate) -> dict:
    """Create concept (publish event). Name unique (case/whitespace insensitive)."""
    name_norm = normalize_name(body.name)
    if not name_norm:
        raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
    existing = await run_read_query(
        "MATCH (n:Concept) WHERE toLower(trim(n.name)) = $name_norm RETURN n.id AS id LIMIT 1",
        {"name_norm": name_norm},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Concept with this name already exists")
    payload = {"id": str(uuid.uuid4()), "name": body.name.strip(), "description": body.description}
    publish_event(EventType.CONCEPT_CREATE, payload)
    events_published_total.labels(event_type=EventType.CONCEPT_CREATE.value).inc()
    return {"status": "accepted", "payload": payload}


@router.get("", response_model=list[ConceptRead])
async def list_concepts() -> list[ConceptRead]:
    """List all concepts from graph."""
    records = await run_read_query(
        "MATCH (n:Concept) RETURN n.id AS id, n.name AS name, n.description AS description"
    )
    return [ConceptRead(id=r["id"], name=r["name"], description=r.get("description") or "") for r in records]


@router.get("/{concept_id}", response_model=ConceptRead)
async def get_concept(concept_id: str) -> ConceptRead:
    """Get concept by id."""
    records = await run_read_query(
        "MATCH (n:Concept {id: $id}) RETURN n.id AS id, n.name AS name, n.description AS description",
        {"id": concept_id},
    )
    if not records:
        raise HTTPException(status_code=404, detail="Concept not found")
    r = records[0]
    return ConceptRead(id=r["id"], name=r["name"], description=r.get("description") or "")


@router.patch("/{concept_id}", status_code=202)
async def update_concept(concept_id: str, body: ConceptUpdate) -> dict:
    """Update concept (publish event). New name must be unique (case/whitespace insensitive)."""
    payload = {"id": concept_id}
    if body.name is not None:
        name_norm = normalize_name(body.name)
        if not name_norm:
            raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
        existing = await run_read_query(
            "MATCH (n:Concept) WHERE toLower(trim(n.name)) = $name_norm AND n.id <> $id RETURN n.id AS id LIMIT 1",
            {"name_norm": name_norm, "id": concept_id},
        )
        if existing:
            raise HTTPException(status_code=409, detail="Concept with this name already exists")
        payload["name"] = body.name.strip()
    if body.description is not None:
        payload["description"] = body.description
    publish_event(EventType.CONCEPT_UPDATE, payload)
    events_published_total.labels(event_type=EventType.CONCEPT_UPDATE.value).inc()
    return {"status": "accepted", "payload": payload}
