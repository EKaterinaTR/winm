"""LLM answer API: context from graph + GigaChat (or stub if no credentials)."""
import asyncio
from fastapi import APIRouter

from app.core.config import settings
from app.models.schemas import LLMAnswerRequest, LLMAnswerResponse
from app.services.llm_context import get_llm_context

router = APIRouter(prefix="/llm", tags=["llm"])


def _call_gigachat(prompt: str) -> str:
    """Sync GigaChat call (run in thread)."""
    from gigachat import GigaChat
    with GigaChat(credentials=settings.gigachat_credentials) as giga:
        response = giga.chat(prompt)
        return (response.choices[0].message.content if response.choices else "") or ""


@router.post("/answer", response_model=LLMAnswerResponse)
async def answer_by_role(body: LLMAnswerRequest) -> LLMAnswerResponse:
    """
    Answer question in role: fetch context from graph, call GigaChat, return answer.
    If GIGACHAT_CREDENTIALS is not set, returns a stub message.
    """
    role = (body.role or "").strip() or "narrator"
    context = await get_llm_context(body.role)

    if not settings.gigachat_credentials:
        return LLMAnswerResponse(
            answer=f"[LLM не настроен] Вопрос: {body.question}. Роль: {role}. "
                   "Задайте GIGACHAT_CREDENTIALS для вызова GigaChat.",
            role=role,
        )

    if role.lower() == "narrator":
        system = "Ты рассказчик визуальной новеллы. Отвечай кратко, в стиле повествования."
    else:
        system = f"Ты отвечаешь от лица персонажа. Контекст персонажа из базы знаний: {context}"

    prompt = f"{system}\n\nКонтекст из графа: {context}\n\nВопрос: {body.question}\n\nОтвет:"
    answer = await asyncio.to_thread(_call_gigachat, prompt)
    return LLMAnswerResponse(answer=answer or "(пустой ответ модели)", role=role)
