"""
LLM microservice: два режима работы.

1) Вопросы по базе знаний (context передаётся снаружи): вызывающая сторона решает
   применять поиск до ~3 раз и передаёт накопленный context в каждом вызове /chat.
2) Генерация сущностей (локация, персонаж, понятие, сцена): ответ — JSON в формате
   сообщения для создания объекта (без сохранения в БД).
"""
import json
import re
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# --- Schemas ---

class ChatRequest(BaseModel):
    """Запрос к /chat (вопрос по базе знаний с уже подставленным context)."""
    prompt: str = Field(..., min_length=1)
    system: str | None = None


class ChatResponse(BaseModel):
    """Ответ /chat."""
    answer: str


class GenerateRequest(BaseModel):
    """Запрос на генерацию сущности (не сохраняется в БД)."""
    entity_type: Literal["location", "character", "concept", "scene"] = Field(...)
    prompt: str = Field(default="", description="Подсказка для генерации")


class GenerateResponse(BaseModel):
    """Ответ генерации: payload готов для отправки в API создания."""
    entity_type: Literal["location", "character", "concept", "scene"]
    payload: dict


# --- Entity schemas for LLM instructions ---

ENTITY_SCHEMAS = {
    "location": '{"name": "string", "description": "string"}',
    "character": '{"name": "string", "description": "string"}',
    "concept": '{"name": "string", "description": "string"}',
    "scene": '{"title": "string", "description": "string", "location_id": "string", "character_ids": ["string"]}',
}


def create_app() -> FastAPI:
    app = FastAPI(title="WinM LLM Service", version="0.2.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    def _call_giga(prompt: str, system: str | None = None) -> str:
        from app.config import settings
        if not settings.gigachat_credentials:
            return "[LLM не настроен] Задайте GIGACHAT_CREDENTIALS."
        from gigachat import GigaChat
        full = (f"{system}\n\n" if system else "") + prompt
        with GigaChat(credentials=settings.gigachat_credentials) as giga:
            response = giga.chat(full)
            return (response.choices[0].message.content if response.choices else "") or ""

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest) -> ChatResponse:
        """Один раунд диалога. Для вопросов по базе знаний вызывающая сторона сама решает применять поиск и передаёт context в prompt/system."""
        text = _call_giga(body.prompt, body.system)
        return ChatResponse(answer=text or "(пустой ответ модели)")

    @app.post("/generate", response_model=GenerateResponse)
    def generate(body: GenerateRequest) -> GenerateResponse:
        """Сгенерировать одну сущность. Ответ — JSON, готовый для тела запроса создания (POST /api/locations и т.д.). В БД не сохраняется."""
        from app.config import settings
        if not settings.gigachat_credentials:
            raise HTTPException(
                status_code=503,
                detail="LLM не настроен. Задайте GIGACHAT_CREDENTIALS.",
            )
        schema = ENTITY_SCHEMAS[body.entity_type]
        system = (
            "Ты помощник по созданию контента для визуальной новеллы. "
            "Отвечай только валидным JSON без markdown и пояснений."
        )
        prompt = (
            f"Сгенерируй один объект для сущности типа {body.entity_type}. "
            f"Схема: {schema}. "
        )
        if body.prompt:
            prompt += f"Подсказка: {body.prompt}. "
        prompt += "Верни только JSON объект с полями по схеме. Для location_id и character_ids используй существующие id или заглушки вроде \"loc-1\", \"char-1\" если не задано."

        text = _call_giga(prompt, system)
        if not text or "[LLM не настроен]" in text:
            raise HTTPException(status_code=503, detail=text or "Пустой ответ LLM")

        # Вытащить JSON из ответа (модель может обернуть в ```json ... ```)
        text_clean = text.strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text_clean)
        if m:
            text_clean = m.group(1).strip()
        try:
            payload = json.loads(text_clean)
        except json.JSONDecodeError:
            start = text_clean.find("{")
            if start != -1:
                end = text_clean.rfind("}") + 1
                if end > start:
                    try:
                        payload = json.loads(text_clean[start:end])
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=502, detail="LLM вернул невалидный JSON")
            else:
                raise HTTPException(status_code=502, detail="LLM вернул невалидный JSON")

        if body.entity_type == "scene":
            payload.setdefault("title", payload.get("name", "Сцена"))
            payload.setdefault("description", "")
            payload.setdefault("location_id", "")
            payload.setdefault("character_ids", [])
        else:
            payload.setdefault("name", "")
            payload.setdefault("description", "")

        return GenerateResponse(entity_type=body.entity_type, payload=payload)

    return app


app = create_app()
