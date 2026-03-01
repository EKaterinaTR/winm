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

    # JWT auth for /api (except /api/auth/token). If auth_disabled=true, all requests are allowed.
    auth_disabled: bool = False
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    api_username: str = "api"
    api_password: str = "api"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
