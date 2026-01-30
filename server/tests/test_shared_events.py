"""Tests for shared events."""
from shared.events import EventType, build_event


def test_event_type_values():
    assert EventType.LOCATION_CREATE.value == "location.create"
    assert EventType.SCENE_CREATE.value == "scene.create"


def test_build_event():
    ev = build_event(EventType.CHARACTER_CREATE, {"name": "Alice"})
    assert ev["type"] == "character.create"
    assert ev["payload"]["name"] == "Alice"
