"""RabbitMQ publisher (server)."""
import json

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.core.config import settings
from shared.events import EventType, build_event


def publish_event(event_type: EventType, payload: dict) -> None:
    """Publish event to RabbitMQ queue graph.tasks."""
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="graph.tasks", durable=True)
    body = json.dumps(build_event(event_type, payload))
    channel.basic_publish(
        exchange="",
        routing_key="graph.tasks",
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()
