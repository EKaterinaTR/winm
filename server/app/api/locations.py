"""Locations API."""
import uuid

from fastapi import APIRouter, HTTPException

from app.core.graph import run_read_query
from app.core.broker import publish_event
from app.core.validation import normalize_name
from app.metrics import events_published_total, neo4j_queries_total
from app.models.schemas import LocationCreate, LocationUpdate, LocationRead
from shared.events import EventType

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("", status_code=202)
async def create_location(body: LocationCreate) -> dict:
    """Create location (publish event, consumer writes to graph). Name unique (case/whitespace insensitive)."""
    name_norm = normalize_name(body.name)
    if not name_norm:
        raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
    existing = await run_read_query(
        "MATCH (n:Location) WHERE toLower(trim(n.name)) = $name_norm RETURN n.id AS id LIMIT 1",
        {"name_norm": name_norm},
    )
    if existing:
        raise HTTPException(status_code=409, detail="Location with this name already exists")
    payload = {"id": str(uuid.uuid4()), "name": body.name.strip(), "description": body.description}
    publish_event(EventType.LOCATION_CREATE, payload)
    events_published_total.labels(event_type=EventType.LOCATION_CREATE.value).inc()
    return {"status": "accepted", "payload": payload}


@router.get("", response_model=list[LocationRead])
async def list_locations() -> list[LocationRead]:
    """List all locations from graph."""
    neo4j_queries_total.labels(operation="list_locations").inc()
    records = await run_read_query("MATCH (n:Location) RETURN n.id AS id, n.name AS name, n.description AS description")
    return [LocationRead(id=r["id"], name=r["name"], description=r.get("description") or "") for r in records]


@router.get("/{location_id}", response_model=LocationRead)
async def get_location(location_id: str) -> LocationRead:
    """Get location by id."""
    neo4j_queries_total.labels(operation="get_location").inc()
    records = await run_read_query(
        "MATCH (n:Location {id: $id}) RETURN n.id AS id, n.name AS name, n.description AS description",
        {"id": location_id},
    )
    if not records:
        raise HTTPException(status_code=404, detail="Location not found")
    r = records[0]
    return LocationRead(id=r["id"], name=r["name"], description=r.get("description") or "")


@router.patch("/{location_id}", status_code=202)
async def update_location(location_id: str, body: LocationUpdate) -> dict:
    """Update location (publish event). New name must be unique (case/whitespace insensitive)."""
    payload = {"id": location_id}
    if body.name is not None:
        name_norm = normalize_name(body.name)
        if not name_norm:
            raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
        existing = await run_read_query(
            "MATCH (n:Location) WHERE toLower(trim(n.name)) = $name_norm AND n.id <> $id RETURN n.id AS id LIMIT 1",
            {"name_norm": name_norm, "id": location_id},
        )
        if existing:
            raise HTTPException(status_code=409, detail="Location with this name already exists")
        payload["name"] = body.name.strip()
    if body.description is not None:
        payload["description"] = body.description
    publish_event(EventType.LOCATION_UPDATE, payload)
    events_published_total.labels(event_type=EventType.LOCATION_UPDATE.value).inc()
    return {"status": "accepted", "payload": payload}
