"""RabbitMQ publisher (server)."""
import json

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.core.config import settings
from shared.events import EventType, build_event

QUEUE_GRAPH_TASKS = "graph.tasks"
QUEUE_LLM_TASKS = "llm.tasks"


def publish_event(event_type: EventType, payload: dict) -> None:
    """Publish event to RabbitMQ queue graph.tasks."""
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_GRAPH_TASKS, durable=True)
    body = json.dumps(build_event(event_type, payload))
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_GRAPH_TASKS,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


def publish_llm_task(payload: dict) -> None:
    """Publish LLM request to queue llm.tasks. payload: request_id, type (knowledge|generate), ..."""
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_LLM_TASKS, durable=True)
    body = json.dumps(payload)
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_LLM_TASKS,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()
