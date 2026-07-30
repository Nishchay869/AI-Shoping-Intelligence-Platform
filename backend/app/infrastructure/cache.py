"""Small Redis JSON cache that fails open for read availability."""
import hashlib
import json
import logging
from typing import Any
from redis import Redis
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def product_search_key(parameters: dict[str, Any]) -> str:
    """Create a fixed-size deterministic key; sorted JSON prevents equivalent cache misses."""
    digest = hashlib.sha256(json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return f"product-search:v1:{digest}"


def review_summary_key(product_id: Any, review_count: int) -> str:
    """Key the AI review summary by product and the exact review count analyzed, so new reviews naturally bust the cache."""
    return f"review-summary:v1:{product_id}:{review_count}"


def get_json(key: str) -> dict[str, Any] | None:
    """Return parsed JSON when Redis is available; search remains available on cache failure."""
    try:
        value = Redis.from_url(get_settings().redis_url, decode_responses=True).get(key)
        return json.loads(value) if value else None
    except Exception: logger.warning("cache_read_failed", exc_info=True); return None


def set_json(key: str, value: dict[str, Any], ttl_seconds: int = 60) -> None:
    """Store short-lived public search output without making Redis a correctness dependency."""
    try: Redis.from_url(get_settings().redis_url, decode_responses=True).setex(key, ttl_seconds, json.dumps(value))
    except Exception: logger.warning("cache_write_failed", exc_info=True)
