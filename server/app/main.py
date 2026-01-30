"""FastAPI app: REST API, metrics, lifespan."""
import time

from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api import locations, characters, story, concepts, search, llm
from app.core.graph import close_driver
from app.metrics import http_requests_total, http_request_duration_seconds


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(title="WinM API", version="0.1.0")

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await close_driver()

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        status = response.status_code
        http_requests_total.labels(method=method, endpoint=path, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
        return response

    @app.get("/health")
    def health() -> dict:
        """Health check for Docker."""
        return {"status": "ok"}

    @app.get("/metrics")
    def metrics() -> Response:
        """Prometheus scrape endpoint."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(locations.router, prefix="/api")
    app.include_router(characters.router, prefix="/api")
    app.include_router(story.router, prefix="/api")
    app.include_router(concepts.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(llm.router, prefix="/api")

    return app


app = create_app()
