"""Concepts API (name-unique resource)."""
from app.api.base_resource import NameResourceRouter
from app.models.schemas import ConceptCreate, ConceptUpdate, ConceptRead
from shared.events import EventType


class ConceptsRouter(NameResourceRouter[ConceptCreate, ConceptUpdate, ConceptRead]):
    label = "Concept"
    prefix = "/concepts"
    path_id_param = "concept_id"
    create_schema = ConceptCreate
    update_schema = ConceptUpdate
    read_schema = ConceptRead
    event_create = EventType.CONCEPT_CREATE
    event_update = EventType.CONCEPT_UPDATE
    entity_name = "Concept"


_router = ConceptsRouter()
router = _router.router
