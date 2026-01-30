"""Consumer: subscribe to RabbitMQ, process events, write to Neo4j."""
import json
import logging
import sys

import pika

from app.config import settings
from app.handlers import handle_event

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


def on_message(channel, method, properties, body):
    """Process one message: parse, handle, ack."""
    try:
        data = json.loads(body)
        event_type = data.get("type")
        payload = data.get("payload", {})
        if not event_type:
            logger.error("Missing type in message")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        handle_event(event_type, payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.exception("Failed to process message: %s", e)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    """Connect to RabbitMQ and consume."""
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="graph.tasks", durable=True)
    channel.basic_consume(queue="graph.tasks", on_message_callback=on_message)
    logger.info("Consumer started, waiting for messages")
    channel.start_consuming()


if __name__ == "__main__":
    main()
