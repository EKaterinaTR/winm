"""Consumer: подписка на RabbitMQ — graph.tasks (запись в Neo4j) и llm.tasks (LLM, результат в llm.results)."""
import json
import logging
import sys
import threading
import time

import pika

from app.config import settings
from app.handlers import handle_event
from app.llm_task_handler import handle_llm_task

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

QUEUE_GRAPH_TASKS = "graph.tasks"
QUEUE_LLM_TASKS = "llm.tasks"
QUEUE_LLM_RESULTS = "llm.results"


def on_graph_message(channel, method, properties, body):
    """Обработка сообщения из graph.tasks."""
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


def publish_llm_result(result: dict) -> None:
    """Опубликовать результат LLM в очередь llm.results."""
    params = pika.URLParameters(settings.rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_LLM_RESULTS, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_LLM_RESULTS,
        body=json.dumps(result),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    connection.close()


def on_llm_message(channel, method, properties, body):
    """Обработка сообщения из llm.tasks: вызвать LLM, отправить результат в llm.results."""
    data = None
    try:
        data = json.loads(body)
        result = handle_llm_task(data)
        publish_llm_result(result)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logger.exception("Failed to process LLM task: %s", e)
        request_id = (data.get("request_id") if data else None) or "unknown"
        publish_llm_result({
            "request_id": request_id,
            "status": "error",
            "error": str(e),
        })
        try:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception:
            pass


def consume_graph_tasks():
    """Поток: потребление graph.tasks."""
    while True:
        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_GRAPH_TASKS, durable=True)
            channel.basic_consume(queue=QUEUE_GRAPH_TASKS, on_message_callback=on_graph_message)
            logger.info("Graph tasks consumer started")
            channel.start_consuming()
        except Exception as e:
            logger.exception("Graph consumer error: %s", e)
        time.sleep(5)


def consume_llm_tasks():
    """Поток: потребление llm.tasks."""
    while True:
        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_LLM_TASKS, durable=True)
            channel.basic_consume(queue=QUEUE_LLM_TASKS, on_message_callback=on_llm_message)
            logger.info("LLM tasks consumer started")
            channel.start_consuming()
        except Exception as e:
            logger.exception("LLM consumer error: %s", e)
        time.sleep(5)


def main():
    """Запуск двух потребителей в отдельных потоках."""
    t1 = threading.Thread(target=consume_graph_tasks, daemon=False)
    t2 = threading.Thread(target=consume_llm_tasks, daemon=False)
    t1.start()
    t2.start()
    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
