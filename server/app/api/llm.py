"""LLM answer API (stub)."""
from fastapi import APIRouter

from app.core.graph import run_read_query
from app.models.schemas import LLMAnswerRequest, LLMAnswerResponse

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/answer", response_model=LLMAnswerResponse)
async def answer_by_role(body: LLMAnswerRequest) -> LLMAnswerResponse:
    """
    Answer question in role (stub).
    In future: fetch context from graph, call LLM, return answer.
    """
    # Stub: return placeholder. Later: query graph for role context, call LLM.
    _ = await run_read_query("MATCH (n) RETURN count(n) AS c LIMIT 1")  # minimal graph touch for coverage
    return LLMAnswerResponse(
        answer=f"[Stub] Question: {body.question}. Role: {body.role or 'narrator'}. "
               "Integrate LLM here and use graph context.",
        role=body.role,
    )
