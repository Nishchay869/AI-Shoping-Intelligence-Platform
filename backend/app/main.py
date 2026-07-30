"""FastAPI application composition root for the backend modular monolith."""
import logging
import time
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError, DomainError, NotFoundError, ServiceUnavailableError
from app.core.logging import configure_logging
from app.infrastructure.metrics import CONTENT_TYPE_LATEST, REQUEST_COUNT, REQUEST_LATENCY, generate_latest

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/docs" if settings.app_env != "production" else None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Attach latency and request metadata to server logs (never bodies/headers, which can carry credentials
    or tokens) and record the same data as Prometheus counters/histograms for GET /metrics."""
    started = time.perf_counter()
    response = await call_next(request)
    duration_seconds = time.perf_counter() - started
    logger.info("request method=%s path=%s status=%s duration_ms=%.2f", request.method, request.url.path, response.status_code, duration_seconds * 1000)
    route = request.scope.get("route")
    route_path = route.path if route else "unmatched"  # route template, not the resolved URL - bounded label cardinality
    REQUEST_COUNT.labels(method=request.method, path=route_path, status=response.status_code).inc()
    REQUEST_LATENCY.labels(method=request.method, path=route_path).observe(duration_seconds)
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, error: DomainError) -> JSONResponse:
    """Map known business failures to stable, non-leaky API responses."""
    status_code = 404 if isinstance(error, NotFoundError) else 409 if isinstance(error, ConflictError) else 401 if isinstance(error, AuthenticationError) else 503 if isinstance(error, ServiceUnavailableError) else 400
    return JSONResponse(status_code=status_code, content={"error": error.__class__.__name__, "detail": str(error)})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return a consistent machine-readable validation error format."""
    return JSONResponse(status_code=422, content={"error": "VALIDATION_ERROR", "detail": error.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, error: Exception) -> JSONResponse:
    """Catch anything not already handled above (a bug, a third-party client raising something unexpected).

    Logs the full exception + traceback server-side for triage, but returns a generic message to the client -
    the client never learns the exception type, message, or stack, all of which can leak internals (file
    paths, library versions, sometimes fragments of a query or a secret) to an attacker probing for one.
    """
    logger.exception("unhandled_exception method=%s path=%s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "detail": "An unexpected error occurred"})


@app.get("/health", tags=["operational"])
def health() -> dict[str, str]:
    """Liveness endpoint safe for load balancers and deployment checks."""
    return {"status": "ok", "environment": settings.app_env}


@app.get("/metrics", tags=["operational"])
def metrics() -> Response:
    """Prometheus scrape target. Not exposed to the internet: production nginx only proxies to the frontend,
    so this is reachable only from inside the private compose network."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(api_router, prefix=settings.api_v1_prefix)
