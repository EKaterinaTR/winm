"""Configuration for LLM (GigaChat) service."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings from environment."""

    gigachat_credentials: str | None = None  # Base64 key; if unset, /chat returns stub

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
