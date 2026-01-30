"""Tests for consumer main (on_message)."""
import json
from unittest.mock import patch, MagicMock

import pytest
import runpy

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


def test_main_connects_and_starts_consuming():
    """Covers main() lines 34-40: connect to RabbitMQ and start consuming."""
    from app.main import main

    mock_channel = MagicMock()
    mock_channel.start_consuming.return_value = None
    mock_connection = MagicMock()
    mock_connection.channel.return_value = mock_channel

    with patch("app.main.pika.URLParameters"):
        with patch("app.main.pika.BlockingConnection", return_value=mock_connection):
            main()
    mock_connection.channel.assert_called_once()
    mock_channel.queue_declare.assert_called_once_with(queue="graph.tasks", durable=True)
    mock_channel.basic_consume.assert_called_once()
    mock_channel.start_consuming.assert_called_once()


def test_main_entry_point():
    """Covers __name__ == '__main__' block (line 44)."""
    
    # Мокируем все зависимости RabbitMQ
    with patch("pika.BlockingConnection") as mock_conn, \
         patch("pika.ConnectionParameters") as mock_params, \
         patch("app.main.main") as mock_main:
        
        # Настраиваем моки
        mock_channel = MagicMock()
        mock_conn.return_value.channel.return_value = mock_channel
        
        runpy.run_module("app.main", run_name="__main__")
        mock_main.assert_called_once()