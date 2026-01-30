"""Tests for consumer graph writes."""
from unittest.mock import patch, MagicMock

import pytest

from app.graph import (
    ensure_id,
    create_location,
    update_location,
    create_character,
    update_character,
    create_scene,
    update_scene,
    create_concept,
    update_concept,
)


def test_ensure_id_with_id():
    assert ensure_id({"id": "custom-1"}) == "custom-1"


def test_ensure_id_without_id():
    uid = ensure_id({"name": "x"})
    assert uid is not None
    assert len(uid) == 36  # uuid4 hex


@patch("app.graph.get_driver")
def test_create_location(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = create_location({"id": "loc-1", "name": "Tavern", "description": "A tavern"})
    assert uid == "loc-1"
    mock_session.run.assert_called()


@patch("app.graph.get_driver")
def test_update_location(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = update_location({"id": "loc-1", "name": "New Tavern"})
    assert uid == "loc-1"
    mock_session.run.assert_called()


@patch("app.graph.get_driver")
def test_create_character(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = create_character({"id": "c1", "name": "Alice", "description": ""})
    assert uid == "c1"


@patch("app.graph.get_driver")
def test_create_scene(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = create_scene({
        "id": "s1",
        "title": "Meet",
        "description": "",
        "location_id": "loc-1",
        "character_ids": ["c1"],
    })
    assert uid == "s1"


@patch("app.graph.get_driver")
def test_create_concept(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = create_concept({"id": "concept-1", "name": "Magic", "description": ""})
    assert uid == "concept-1"


@patch("app.graph.get_driver")
def test_update_character(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = update_character({"id": "c1", "name": "Alice Updated"})
    assert uid == "c1"


@patch("app.graph.get_driver")
def test_update_scene(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = update_scene({"id": "s1", "title": "Updated Scene"})
    assert uid == "s1"


@patch("app.graph.get_driver")
def test_update_concept(mock_get_driver):
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = lambda self: mock_session
    mock_driver.session.return_value.__exit__ = lambda *a: None
    mock_get_driver.return_value = mock_driver
    uid = update_concept({"id": "concept-1", "description": "Updated"})
    assert uid == "concept-1"
