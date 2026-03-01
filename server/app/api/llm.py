"""LLM answer API: context from graph + GigaChat (via LLM service or stub)."""
import asyncio
from fastapi import APIRouter
import httpx

from app.core.config import settings
from app.models.schemas import LLMAnswerRequest, LLMAnswerResponse
from app.services.llm_context import get_llm_context

router = APIRouter(prefix="/llm", tags=["llm"])


async def _call_llm_service(prompt: str, system: str | None = None) -> str:
    """Call LLM microservice POST /chat. Returns answer text or raises."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{settings.llm_service_url.rstrip('/')}/chat",
            json={"prompt": prompt, "system": system},
        )
        r.raise_for_status()
        data = r.json()
        return data.get("answer", "") or ""


def _call_gigachat_local(prompt: str) -> str:
    """Sync GigaChat call (run in thread). Used when llm_service_url is not set."""
    from gigachat import GigaChat
    with GigaChat(credentials=settings.gigachat_credentials) as giga:
        response = giga.chat(prompt)
        return (response.choices[0].message.content if response.choices else "") or ""


@router.post("/answer", response_model=LLMAnswerResponse)
async def answer_by_role(body: LLMAnswerRequest) -> LLMAnswerResponse:
    """
    Answer question in role: fetch context from graph, call GigaChat (via LLM service or local), return answer.
    If LLM_SERVICE_URL is set, calls the LLM microservice; else if GIGACHAT_CREDENTIALS is set, calls GigaChat in-process; else stub.
    """
    role = (body.role or "").strip() or "narrator"
    context = await get_llm_context(body.role)

    if not settings.llm_service_url and not settings.gigachat_credentials:
        return LLMAnswerResponse(
            answer=f"[LLM не настроен] Вопрос: {body.question}. Роль: {role}. "
                   "Задайте GIGACHAT_CREDENTIALS или LLM_SERVICE_URL для вызова GigaChat.",
            role=role,
        )

    if role.lower() == "narrator":
        system = "Ты рассказчик визуальной новеллы. Отвечай кратко, в стиле повествования."
    else:
        system = f"Ты отвечаешь от лица персонажа. Контекст персонажа из базы знаний: {context}"

    prompt = f"Контекст из графа: {context}\n\nВопрос: {body.question}\n\nОтвет:"
    if settings.llm_service_url:
        answer = await _call_llm_service(prompt, system=system)
    else:
        full_prompt = f"{system}\n\n{prompt}"
        answer = await asyncio.to_thread(_call_gigachat_local, full_prompt)
    return LLMAnswerResponse(answer=answer or "(пустой ответ модели)", role=role)
