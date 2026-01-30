"""Tests for metrics module."""
from app.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    events_published_total,
    neo4j_queries_total,
)


def test_metrics_exist():
    assert http_requests_total._name == "http_server_requests_total"
    assert http_request_duration_seconds._name == "http_server_request_duration_seconds"
    assert events_published_total._name == "events_published_total"
    assert neo4j_queries_total._name == "neo4j_queries_total"
