"""Consumer configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings from environment."""

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    export_dir: str = "./exports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
