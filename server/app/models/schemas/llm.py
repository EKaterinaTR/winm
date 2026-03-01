"""LLM API schemas: очередь запросов, результат по request_id."""
from typing import Literal

from pydantic import BaseModel, Field


class LLMAnswerRequest(BaseModel):
    """Запрос на ответ по базе знаний (ставится в очередь)."""
    question: str = Field(..., min_length=1)
    role: str | None = None  # character id или "narrator"


class LLMGenerateRequest(BaseModel):
    """Запрос на генерацию сущности (ставится в очередь, в БД не сохраняется)."""
    entity_type: Literal["location", "character", "concept", "scene"] = Field(...)
    prompt: str = Field(default="", description="Подсказка для генерации")


class LLMTaskAccepted(BaseModel):
    """Ответ 202: задача принята в очередь."""
    request_id: str


class LLMResultPending(BaseModel):
    """Результат ещё не готов."""
    status: Literal["pending"] = "pending"
    request_id: str


class LLMResultAnswer(BaseModel):
    """Готовый ответ на вопрос по базе знаний."""
    status: Literal["done"] = "done"
    request_id: str
    type: Literal["knowledge"] = "knowledge"
    answer: str
    role: str | None = None


class LLMResultGenerate(BaseModel):
    """Готовый результат генерации (payload для создания объекта)."""
    status: Literal["done"] = "done"
    request_id: str
    type: Literal["generate"] = "generate"
    entity_type: Literal["location", "character", "concept", "scene"]
    payload: dict


class LLMResultError(BaseModel):
    """Ошибка выполнения задачи LLM."""
    status: Literal["error"] = "error"
    request_id: str
    error: str
