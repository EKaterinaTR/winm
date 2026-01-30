"""Tests for broker (publish_event)."""
import json
from unittest.mock import patch, MagicMock

import pika
import pytest

from app.core.broker import publish_event
from shared.events import EventType


def test_publish_event():
    with patch("app.core.broker.pika.BlockingConnection") as mock_conn:
        mock_channel = MagicMock()
        mock_conn.return_value.__enter__ = lambda self: self
        mock_conn.return_value.__exit__ = lambda *a: None
        mock_conn.return_value.channel.return_value = mock_channel
        mock_conn.return_value.close = MagicMock()
        with patch("app.core.broker.pika.URLParameters"):
            publish_event(EventType.LOCATION_CREATE, {"name": "Tavern", "description": ""})
        mock_channel.queue_declare.assert_called_once_with(queue="graph.tasks", durable=True)
        mock_channel.basic_publish.assert_called_once()
        call_args = mock_channel.basic_publish.call_args
        body = json.loads(call_args[1]["body"])
        assert body["type"] == EventType.LOCATION_CREATE.value
        assert body["payload"]["name"] == "Tavern"
