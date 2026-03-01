"""In-memory store for LLM results (consumed from llm.results queue) and background consumer thread."""
import json
import logging
import threading
import time

import pika

from app.core.config import settings

logger = logging.getLogger(__name__)
QUEUE_LLM_RESULTS = "llm.results"

# request_id -> { "status": "done" | "error", "answer"?, "entity_type"?, "payload"?, "error"? }
_results: dict[str, dict] = {}
_results_lock = threading.Lock()
# Храним результаты не более 1 часа
_RESULT_TTL_SEC = 3600
_result_timestamps: dict[str, float] = {}


def set_result(request_id: str, data: dict) -> None:
    with _results_lock:
        _results[request_id] = data
        _result_timestamps[request_id] = time.time()


def get_result(request_id: str) -> dict | None:
    with _results_lock:
        _prune_expired()
        return _results.get(request_id)


def _prune_expired() -> None:
    now = time.time()
    expired = [rid for rid, ts in _result_timestamps.items() if now - ts > _RESULT_TTL_SEC]
    for rid in expired:
        _results.pop(rid, None)
        _result_timestamps.pop(rid, None)


def _consume_loop() -> None:
    while True:
        try:
            params = pika.URLParameters(settings.rabbitmq_url)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_LLM_RESULTS, durable=True)

            def on_message(ch, method, props, body):
                try:
                    data = json.loads(body)
                    request_id = data.get("request_id")
                    if not request_id:
                        logger.warning("llm.results message without request_id")
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    set_result(request_id, data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.exception("Failed to process llm.results message: %s", e)
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            channel.basic_consume(queue=QUEUE_LLM_RESULTS, on_message_callback=on_message)
            logger.info("LLM results consumer started")
            channel.start_consuming()
        except Exception as e:
            logger.exception("LLM results consumer error: %s", e)
        time.sleep(5)


def start_llm_results_consumer() -> None:
    """Start background thread that consumes llm.results and fills _results."""
    t = threading.Thread(target=_consume_loop, daemon=True)
    t.start()
