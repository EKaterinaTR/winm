"""
Обработка задач из очереди llm.tasks: вопросы по базе знаний (с поиском до ~3 раз) и генерация сущностей.
Результат публикуется в llm.results.
"""
import logging

import httpx

from app.config import settings
from app.graph import search_graph

logger = logging.getLogger(__name__)

MAX_SEARCH_ROUNDS = 3
SEARCH_PREFIX = "SEARCH:"
ANSWER_PREFIX = "ANSWER:"


def _call_llm_chat(prompt: str, system: str | None = None) -> str:
    """Один вызов LLM /chat."""
    url = f"{settings.llm_service_url.rstrip('/')}/chat"
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json={"prompt": prompt, "system": system})
        r.raise_for_status()
        return r.json().get("answer", "") or ""


def _call_llm_generate(entity_type: str, prompt: str) -> dict:
    """Вызов LLM /generate. Возвращает { entity_type, payload }."""
    url = f"{settings.llm_service_url.rstrip('/')}/generate"
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, json={"entity_type": entity_type, "prompt": prompt})
        r.raise_for_status()
        return r.json()


def _format_search_results(records: list[dict]) -> str:
    if not records:
        return "Поиск не нашёл совпадений."
    lines = []
    for r in records:
        t = r.get("type", "")
        name = r.get("name", "")
        snippet = (r.get("snippet") or "")[:200]
        lines.append(f"[{t}] {name}: {snippet}")
    return "\n".join(lines)


def handle_knowledge(request_id: str, question: str, role: str) -> dict:
    """
    Вопрос по базе знаний. До ~3 раундов: LLM может ответить SEARCH: <query>, тогда
    выполняем поиск по графу, добавляем в context и снова спрашиваем LLM.
    """
    system = (
        "Ты помощник по визуальной новелле с доступом к базе знаний. "
        "Если нужна информация из базы — ответь ровно одной строкой: SEARCH: <запрос>. "
        "Иначе ответь строкой: ANSWER: <твой ответ пользователю>."
    )
    context_parts = []
    for _ in range(MAX_SEARCH_ROUNDS + 1):
        context_str = "\n\n".join(context_parts) if context_parts else "Пока нет данных из поиска."
        prompt = (
            f"Контекст из базы знаний:\n{context_str}\n\n"
            f"Вопрос пользователя: {question}\n\n"
            "Ответь SEARCH: <запрос> или ANSWER: <твой ответ>."
        )
        try:
            raw = _call_llm_chat(prompt, system=system)
        except Exception as e:
            logger.exception("LLM chat error: %s", e)
            return {
                "request_id": request_id,
                "status": "error",
                "type": "knowledge",
                "error": str(e),
            }
        raw = (raw or "").strip()
        if raw.upper().startswith(ANSWER_PREFIX):
            answer = raw[len(ANSWER_PREFIX):].strip()
            return {
                "request_id": request_id,
                "status": "done",
                "type": "knowledge",
                "answer": answer or "(пустой ответ)",
                "role": role,
            }
        if raw.upper().startswith(SEARCH_PREFIX):
            query = raw[len(SEARCH_PREFIX):].strip()
            if not query:
                return {
                    "request_id": request_id,
                    "status": "done",
                    "type": "knowledge",
                    "answer": "(LLM запросил поиск без запроса)",
                    "role": role,
                }
            records = search_graph(query)
            formatted = _format_search_results(records)
            context_parts.append(f"Поиск по запросу «{query}»:\n{formatted}")
            continue
        return {
            "request_id": request_id,
            "status": "done",
            "type": "knowledge",
            "answer": raw or "(не удалось распознать ответ)",
            "role": role,
        }
    return {
        "request_id": request_id,
        "status": "done",
        "type": "knowledge",
        "answer": "(исчерпан лимит раундов поиска)",
        "role": role,
    }


def handle_generate(request_id: str, entity_type: str, prompt: str) -> dict:
    """Генерация сущности. Ответ — payload для создания, в БД не сохраняем."""
    try:
        data = _call_llm_generate(entity_type, prompt)
        return {
            "request_id": request_id,
            "status": "done",
            "type": "generate",
            "entity_type": data.get("entity_type", entity_type),
            "payload": data.get("payload", {}),
        }
    except Exception as e:
        logger.exception("LLM generate error: %s", e)
        return {
            "request_id": request_id,
            "status": "error",
            "type": "generate",
            "error": str(e),
        }


def handle_llm_task(body: dict) -> dict:
    """По request_id и type вызвать нужный обработчик и вернуть результат для публикации в llm.results."""
    request_id = body.get("request_id")
    task_type = body.get("type")
    if not request_id or not task_type:
        raise ValueError("request_id and type required")
    if task_type == "knowledge":
        return handle_knowledge(
            request_id,
            body.get("question", ""),
            body.get("role") or "narrator",
        )
    if task_type == "generate":
        return handle_generate(
            request_id,
            body.get("entity_type", "location"),
            body.get("prompt", ""),
        )
    return {
        "request_id": request_id,
        "status": "error",
        "error": f"Unknown task type: {task_type}",
    }
