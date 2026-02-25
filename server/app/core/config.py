"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings from environment."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    gigachat_credentials: str | None = None  # Base64 key from GIGACHAT_CREDENTIALS; if unset, LLM returns stub
    llm_service_url: str | None = None  # If set, server calls this URL instead of GigaChat directly (e.g. http://winm-llm-service:8001)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
