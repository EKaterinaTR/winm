"""Shared event types and payloads for server <-> consumer."""
from enum import Enum
from typing import Any


class EventType(str, Enum):
    """Types of graph update events."""
    LOCATION_CREATE = "location.create"
    LOCATION_UPDATE = "location.update"
    CHARACTER_CREATE = "character.create"
    CHARACTER_UPDATE = "character.update"
    SCENE_CREATE = "scene.create"
    SCENE_UPDATE = "scene.update"
    CONCEPT_CREATE = "concept.create"
    CONCEPT_UPDATE = "concept.update"


def build_event(event_type: EventType, payload: dict[str, Any]) -> dict[str, Any]:
    """Build event dict for broker."""
    return {"type": event_type.value, "payload": payload}
