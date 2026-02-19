"""LLM API schemas (stub)."""
from pydantic import BaseModel, Field


class LLMAnswerRequest(BaseModel):
    """Request for LLM answer (stub)."""
    question: str = Field(..., min_length=1)
    role: str | None = None  # character id or "narrator"


class LLMAnswerResponse(BaseModel):
    """LLM answer (stub)."""
    answer: str
    role: str | None = None
