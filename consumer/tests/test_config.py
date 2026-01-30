"""Tests for consumer config."""
from app.config import Settings, settings


def test_settings_defaults():
    s = Settings()
    assert s.neo4j_uri == "bolt://localhost:7687"
    assert s.rabbitmq_url.startswith("amqp://")


def test_settings_instance():
    assert settings is not None
