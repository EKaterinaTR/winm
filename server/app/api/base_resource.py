"""Base router for name-unique resources (Character, Location, Concept)."""
import uuid
from typing import Generic, TypeVar

from fastapi import APIRouter, HTTPException, Request

from app.core.graph import run_read_query
from app.core.broker import publish_event
from app.core.validation import normalize_name
from app.metrics import events_published_total, neo4j_queries_total
from shared.events import EventType

CreateT = TypeVar("CreateT")
UpdateT = TypeVar("UpdateT")
ReadT = TypeVar("ReadT")


class NameResourceRouter(Generic[CreateT, UpdateT, ReadT]):
    """Base class for CRUD API of a graph node with unique name (case/whitespace insensitive)."""

    label: str = ""  # Cypher label: Character, Location, Concept
    prefix: str = ""
    path_id_param: str = ""
    create_schema: type = None
    update_schema: type = None
    read_schema: type = None
    event_create: EventType = None
    event_update: EventType = None
    entity_name: str = ""  # for error messages: "Character", "Location", "Concept"

    def __init__(self) -> None:
        self.router = APIRouter(prefix=self.prefix, tags=[self.prefix.strip("/")])
        self._register_routes()

    def _register_routes(self) -> None:
        create_schema = self.create_schema
        update_schema = self.update_schema
        read_schema = self.read_schema

        async def create_endpoint(body: create_schema) -> dict:
            return await self._create_impl(body)

        async def update_endpoint(request: Request, body: update_schema) -> dict:
            return await self._update_impl(request, body)

        self.router.add_api_route(
            "",
            create_endpoint,
            methods=["POST"],
            status_code=202,
            response_model=dict,
        )
        self.router.add_api_route(
            "",
            self.list_all,
            methods=["GET"],
            response_model=list[read_schema],
        )
        self.router.add_api_route(
            f"/{{{self.path_id_param}}}",
            self.get_one,
            methods=["GET"],
            response_model=read_schema,
        )
        self.router.add_api_route(
            f"/{{{self.path_id_param}}}",
            update_endpoint,
            methods=["PATCH"],
            status_code=202,
            response_model=dict,
        )

    async def _create_impl(self, body: CreateT) -> dict:
        """Create resource (publish event). Name unique (case/whitespace insensitive)."""
        name_norm = normalize_name(body.name)
        if not name_norm:
            raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
        existing = await run_read_query(
            f"MATCH (n:{self.label}) WHERE toLower(trim(n.name)) = $name_norm RETURN n.id AS id LIMIT 1",
            {"name_norm": name_norm},
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"{self.entity_name} with this name already exists",
            )
        payload = {
            "id": str(uuid.uuid4()),
            "name": body.name.strip(),
            "description": body.description,
        }
        publish_event(self.event_create, payload)
        events_published_total.labels(event_type=self.event_create.value).inc()
        return {"status": "accepted", "payload": payload}

    async def list_all(self) -> list:
        neo4j_queries_total.labels(operation=f"list_{self.prefix.strip('/')}").inc()
        records = await run_read_query(
            f"MATCH (n:{self.label}) RETURN n.id AS id, n.name AS name, n.description AS description"
        )
        return [
            self.read_schema(id=r["id"], name=r["name"], description=r.get("description") or "")
            for r in records
        ]

    async def get_one(self, request: Request):
        resource_id = request.path_params[self.path_id_param]
        neo4j_queries_total.labels(operation=f"get_{self.prefix.strip('/')}").inc()
        records = await run_read_query(
            f"MATCH (n:{self.label} {{id: $id}}) RETURN n.id AS id, n.name AS name, n.description AS description",
            {"id": resource_id},
        )
        if not records:
            raise HTTPException(status_code=404, detail=f"{self.entity_name} not found")
        r = records[0]
        return self.read_schema(id=r["id"], name=r["name"], description=r.get("description") or "")

    async def _update_impl(self, request: Request, body: UpdateT) -> dict:
        resource_id = request.path_params[self.path_id_param]
        payload = {"id": resource_id}
        if body.name is not None:
            name_norm = normalize_name(body.name)
            if not name_norm:
                raise HTTPException(status_code=400, detail="Name cannot be empty after trimming")
            existing = await run_read_query(
                f"MATCH (n:{self.label}) WHERE toLower(trim(n.name)) = $name_norm AND n.id <> $id RETURN n.id AS id LIMIT 1",
                {"name_norm": name_norm, "id": resource_id},
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"{self.entity_name} with this name already exists",
                )
            payload["name"] = body.name.strip()
        if body.description is not None:
            payload["description"] = body.description
        if len(payload) == 1:
            raise HTTPException(
                status_code=400,
                detail="At least one of name or description must be provided",
            )
        publish_event(self.event_update, payload)
        events_published_total.labels(event_type=self.event_update.value).inc()
        return {"status": "accepted", "payload": payload}
