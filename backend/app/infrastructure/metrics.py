"""Prometheus metrics - scraped (pull-based), not pushed, so the app has zero dependency on any monitoring
backend being reachable to keep serving requests. Exposed at GET /metrics (see app/main.py); safe to leave
unauthenticated because the production nginx config (deploy/nginx) never proxies to the backend at all -
only the frontend is internet-reachable, so /metrics is already network-isolated by topology.

Label cardinality matters for Prometheus: request paths are labeled by *route template* (e.g.
/products/{id}), never the resolved URL - labeling by resolved URL would create a new, permanent time
series per UUID ever requested, which is the single most common way to accidentally overload a Prometheus
server from application code.
"""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency in seconds", ["method", "path"])
RATE_LIMIT_REJECTIONS = Counter("rate_limit_rejections_total", "Requests rejected by the rate limiter", ["path"])
AUTH_FAILURES = Counter("auth_failures_total", "Failed authentication attempts")

__all__ = ["CONTENT_TYPE_LATEST", "REQUEST_COUNT", "REQUEST_LATENCY", "RATE_LIMIT_REJECTIONS", "AUTH_FAILURES", "generate_latest"]
