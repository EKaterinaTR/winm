"""GigaChat LLM microservice: single /chat endpoint."""
from fastapi import FastAPI
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for /chat."""
    prompt: str
    system: str | None = None


class ChatResponse(BaseModel):
    """Response from /chat."""
    answer: str


def create_app() -> FastAPI:
    app = FastAPI(title="WinM LLM Service (GigaChat)", version="0.1.0")

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    def chat(body: ChatRequest) -> ChatResponse:
        from app.config import settings
        if not settings.gigachat_credentials:
            return ChatResponse(
                answer="[LLM не настроен] Задайте GIGACHAT_CREDENTIALS."
            )
        from gigachat import GigaChat
        with GigaChat(credentials=settings.gigachat_credentials) as giga:
            full = (f"{body.system}\n\n" if body.system else "") + body.prompt
            response = giga.chat(full)
            text = (response.choices[0].message.content if response.choices else "") or ""
            return ChatResponse(answer=text or "(пустой ответ модели)")

    return app


app = create_app()
