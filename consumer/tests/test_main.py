"""Tests for consumer main (on_graph_message для graph.tasks)."""
import json
from unittest.mock import patch, MagicMock

import pytest

from app.main import on_graph_message


def test_on_message_success():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"type": "location.create", "payload": {"id": "loc-1", "name": "Tavern", "description": ""}})
    with patch("app.main.handle_event") as mock_handle:
        on_graph_message(channel, method, properties=None, body=body.encode())
        mock_handle.assert_called_once_with("location.create", {"id": "loc-1", "name": "Tavern", "description": ""})
    channel.basic_ack.assert_called_once_with(delivery_tag=1)


def test_on_message_missing_type():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"payload": {}})
    on_graph_message(channel, method, properties=None, body=body.encode())
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_on_message_invalid_json():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    with patch("app.main.handle_event"):
        on_graph_message(channel, method, properties=None, body=b"not json")
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_on_message_handle_raises():
    channel = MagicMock()
    method = MagicMock()
    method.delivery_tag = 1
    body = json.dumps({"type": "location.create", "payload": {"name": "x"}})
    with patch("app.main.handle_event", side_effect=ValueError("err")):
        on_graph_message(channel, method, properties=None, body=body.encode())
    channel.basic_nack.assert_called_once_with(delivery_tag=1, requeue=False)


def test_main_starts_two_consumers():
    """main() запускает два потока: consume_graph_tasks и consume_llm_tasks."""
    from app.main import main

    with patch("app.main.consume_graph_tasks") as mock_graph:
        with patch("app.main.consume_llm_tasks") as mock_llm:
            mock_graph.side_effect = lambda: None
            mock_llm.side_effect = lambda: None
            main()
    mock_graph.assert_called_once()
    mock_llm.assert_called_once()