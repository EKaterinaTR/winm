"""LLM API: запросы в очередь llm.tasks, результат по GET /api/llm/result/:request_id."""
import uuid

from fastapi import APIRouter, HTTPException

from app.core.broker import publish_llm_task
from app.llm_results import get_result, start_llm_results_consumer
from app.models.schemas import (
    LLMAnswerRequest,
    LLMGenerateRequest,
    LLMTaskAccepted,
    LLMResultPending,
    LLMResultAnswer,
    LLMResultGenerate,
    LLMResultError,
)

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/answer", status_code=202, response_model=LLMTaskAccepted)
def answer_task(body: LLMAnswerRequest) -> LLMTaskAccepted:
    """
    Вопрос по базе знаний. Запрос ставится в очередь; ответ не моментальный.
    Получить результат: GET /api/llm/result/{request_id}.
    """
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "type": "knowledge",
        "question": body.question,
        "role": body.role or "narrator",
    }
    publish_llm_task(payload)
    return LLMTaskAccepted(request_id=request_id)


@router.post("/generate", status_code=202, response_model=LLMTaskAccepted)
def generate_task(body: LLMGenerateRequest) -> LLMTaskAccepted:
    """
    Генерация локации/персонажа/понятия/сцены. Не сохраняется в БД.
    Ответ — payload для POST создания. Результат: GET /api/llm/result/{request_id}.
    """
    request_id = str(uuid.uuid4())
    payload = {
        "request_id": request_id,
        "type": "generate",
        "entity_type": body.entity_type,
        "prompt": body.prompt,
    }
    publish_llm_task(payload)
    return LLMTaskAccepted(request_id=request_id)


@router.get(
    "/result/{request_id}",
    response_model=LLMResultPending | LLMResultAnswer | LLMResultGenerate | LLMResultError,
    status_code=200,
)
def get_llm_result(request_id: str):
    """
    Результат задачи LLM по request_id из POST /answer или POST /generate.
    200 — результат готов (answer или generate payload), 200 с status=pending — ещё в обработке.
    """
    data = get_result(request_id)
    if data is None:
        return LLMResultPending(request_id=request_id)

    if data.get("status") == "error" or data.get("error"):
        return LLMResultError(
            request_id=request_id,
            error=data.get("error", "Unknown error"),
        )
    if data.get("type") == "knowledge":
        return LLMResultAnswer(
            request_id=request_id,
            answer=data.get("answer", ""),
            role=data.get("role"),
        )
    if data.get("type") == "generate":
        return LLMResultGenerate(
            request_id=request_id,
            entity_type=data["entity_type"],
            payload=data.get("payload", {}),
        )
    return LLMResultError(request_id=request_id, error="Unknown result type")
