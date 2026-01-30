"""Tests for event handlers."""
from unittest.mock import patch

import pytest

from app.handlers import handle_event, export_to_file, _normalize_name
from shared.events import EventType


def test_handle_location_create(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_location") as mock_create:
            mock_create.return_value = "loc-1"
            handle_event(EventType.LOCATION_CREATE.value, {"id": "loc-1", "name": "Tavern", "description": ""})
            mock_create.assert_called_once_with({"id": "loc-1", "name": "Tavern", "description": ""})
    assert (tmp_path / "events.jsonl").exists()


def test_handle_location_create_normalizes_name(tmp_path):
    """Name is stripped before write (case/whitespace consistent with server)."""
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_location") as mock_create:
            handle_event(
                EventType.LOCATION_CREATE.value,
                {"id": "loc-1", "name": "  таверна  ", "description": "первое место"},
            )
            mock_create.assert_called_once()
            call_payload = mock_create.call_args[0][0]
            assert call_payload["name"] == "таверна"
            assert call_payload["description"] == "первое место"


def test_handle_character_create(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_character") as mock_create:
            mock_create.return_value = "c1"
            handle_event(EventType.CHARACTER_CREATE.value, {"id": "c1", "name": "Alice", "description": ""})
            mock_create.assert_called_once()


def test_handle_character_create_normalizes_name(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_character") as mock_create:
            handle_event(
                EventType.CHARACTER_CREATE.value,
                {"id": "c1", "name": "\t Alice \n", "description": ""},
            )
            call_payload = mock_create.call_args[0][0]
            assert call_payload["name"] == "Alice"


def test_handle_scene_create(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_scene") as mock_create:
            mock_create.return_value = "s1"
            handle_event(
                EventType.SCENE_CREATE.value,
                {"id": "s1", "title": "Meet", "description": "", "location_id": "loc-1", "character_ids": []},
            )
            mock_create.assert_called_once()


def test_handle_concept_create(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_concept") as mock_create:
            mock_create.return_value = "concept-1"
            handle_event(EventType.CONCEPT_CREATE.value, {"id": "concept-1", "name": "Magic", "description": ""})
            mock_create.assert_called_once()


def test_handle_concept_create_normalizes_name(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_concept") as mock_create:
            handle_event(
                EventType.CONCEPT_CREATE.value,
                {"id": "concept-1", "name": "  Magic  ", "description": ""},
            )
            call_payload = mock_create.call_args[0][0]
            assert call_payload["name"] == "Magic"


def test_handle_scene_create_normalizes_title(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.create_scene") as mock_create:
            handle_event(
                EventType.SCENE_CREATE.value,
                {"id": "s1", "title": "  Meet  ", "description": "", "location_id": "loc-1", "character_ids": []},
            )
            call_payload = mock_create.call_args[0][0]
            assert call_payload["title"] == "Meet"


def test_handle_location_update(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.update_location") as mock_update:
            mock_update.return_value = "loc-1"
            handle_event(EventType.LOCATION_UPDATE.value, {"id": "loc-1", "name": "New Tavern"})
            mock_update.assert_called_once()


def test_handle_character_update(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.update_character") as mock_update:
            mock_update.return_value = "c1"
            handle_event(EventType.CHARACTER_UPDATE.value, {"id": "c1", "description": "Updated"})
            mock_update.assert_called_once()


def test_handle_scene_update(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.update_scene") as mock_update:
            mock_update.return_value = "s1"
            handle_event(EventType.SCENE_UPDATE.value, {"id": "s1", "title": "Updated"})
            mock_update.assert_called_once()


def test_handle_concept_update(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        with patch("app.handlers.update_concept") as mock_update:
            mock_update.return_value = "concept-1"
            handle_event(EventType.CONCEPT_UPDATE.value, {"id": "concept-1", "description": "Updated"})
            mock_update.assert_called_once()


def test_handle_unknown_event():
    with pytest.raises(ValueError, match="Unknown event type"):
        handle_event("unknown.type", {})


def test_export_to_file(tmp_path):
    with patch("app.handlers.settings") as mock_settings:
        mock_settings.export_dir = str(tmp_path)
        export_to_file("location.create", {"id": "loc-1", "name": "Tavern"})
    p = tmp_path / "events.jsonl"
    assert p.exists()
    content = p.read_text()
    assert "location.create" in content
    assert "Tavern" in content


# --- _normalize_name (strip, consistent with server uniqueness) ---


def test_normalize_name_strip():
    assert _normalize_name("  таверна  ") == "таверна"
    assert _normalize_name("\tAlice\t") == "Alice"


def test_normalize_name_empty():
    assert _normalize_name("   ") == ""
    assert _normalize_name("") == ""
    assert _normalize_name(None) == ""
