"""Tests for config."""
from app.core.config import Settings, settings


def test_settings_defaults():
    s = Settings()
    assert s.neo4j_uri == "bolt://localhost:7687"
    assert s.neo4j_user == "neo4j"
    assert s.rabbitmq_url.startswith("amqp://")


def test_settings_instance():
    assert settings is not None
    assert hasattr(settings, "neo4j_uri")
