"""Prometheus metrics."""
from prometheus_client import Counter, Histogram

http_requests_total = Counter(
    "http_server_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
http_request_duration_seconds = Histogram(
    "http_server_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
events_published_total = Counter(
    "events_published_total",
    "Total events published to broker",
    ["event_type"],
)
neo4j_queries_total = Counter(
    "neo4j_queries_total",
    "Total Neo4j queries",
    ["operation"],
)
