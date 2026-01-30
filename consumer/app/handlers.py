"""Event handlers: dispatch to graph writes and optional export."""
import json
from pathlib import Path

from shared.events import EventType

from app.config import settings
from app.graph import (
    create_location,
    update_location,
    create_character,
    update_character,
    create_scene,
    update_scene,
    create_concept,
    update_concept,
)


def _normalize_name(name: str) -> str:
    """Strip leading/trailing whitespace (consistent with server uniqueness)."""
    return name.strip() if name else ""


def handle_event(event_type: str, payload: dict) -> None:
    """Dispatch event to graph write and export. Normalizes name/title (strip) before write."""
    if event_type == EventType.LOCATION_CREATE.value:
        payload = {**payload, "name": _normalize_name(payload.get("name", ""))}
        create_location(payload)
    elif event_type == EventType.LOCATION_UPDATE.value:
        if "name" in payload:
            payload = {**payload, "name": _normalize_name(payload["name"])}
        update_location(payload)
    elif event_type == EventType.CHARACTER_CREATE.value:
        payload = {**payload, "name": _normalize_name(payload.get("name", ""))}
        create_character(payload)
    elif event_type == EventType.CHARACTER_UPDATE.value:
        if "name" in payload:
            payload = {**payload, "name": _normalize_name(payload["name"])}
        update_character(payload)
    elif event_type == EventType.SCENE_CREATE.value:
        payload = {**payload, "title": _normalize_name(payload.get("title", ""))}
        create_scene(payload)
    elif event_type == EventType.SCENE_UPDATE.value:
        if "title" in payload:
            payload = {**payload, "title": _normalize_name(payload["title"])}
        update_scene(payload)
    elif event_type == EventType.CONCEPT_CREATE.value:
        payload = {**payload, "name": _normalize_name(payload.get("name", ""))}
        create_concept(payload)
    elif event_type == EventType.CONCEPT_UPDATE.value:
        if "name" in payload:
            payload = {**payload, "name": _normalize_name(payload["name"])}
        update_concept(payload)
    else:
        raise ValueError(f"Unknown event type: {event_type}")
    export_to_file(event_type, payload)


def export_to_file(event_type: str, payload: dict) -> None:
    """Append event to export file for Git (optional)."""
    path = Path(settings.export_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "events.jsonl"
    line = json.dumps({"type": event_type, "payload": payload}) + "\n"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line)
