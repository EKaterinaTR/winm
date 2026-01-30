"""Tests for consumer main (on_message)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from app.main import on_message


def test_on_message_success():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"type": "location.create", "payload": {"id": "loc-1", "name": "Tavern", "description": ""}})
    with patch("app.main.handle_event") as mock_handle:
        on_message(channel, method, properties=None, body=body.encode())
        mock_handle.assert_called_once_with("location.create", {"id": "loc-1", "name": "Tavern", "description": ""})
    channel.basic_ack.assert_called_once_with(delivery_tag=1)


def test_on_message_missing_type():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"payload": {}})
    on_message(channel, method, properties=None, body=body.encode())
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_on_message_invalid_json():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    with patch("app.main.handle_event"):
        on_message(channel, method, properties=None, body=b"not json")
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_on_message_handle_raises():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"type": "location.create", "payload": {"name": "x"}})
    with patch("app.main.handle_event", side_effect=ValueError("err")):
        on_message(channel, method, properties=None, body=body.encode())
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)
