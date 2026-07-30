"""Tavily web search: LLM-ready live search results for questions the internal catalog/review index can't
cover on its own. Blended into every chat answer alongside catalog context (not just a fallback), so a
missing/failed search must degrade to "no web context" rather than a 500 - the catalog-only answer is still
a valid answer.
"""
import logging
from dataclasses import dataclass
from functools import lru_cache
from tavily import TavilyClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebResult:
    label: str
    title: str
    url: str
    snippet: str


@lru_cache
def _client() -> TavilyClient:
    settings = get_settings()
    return TavilyClient(api_key=settings.tavily_api_key)


def search_web(query: str, max_results: int = 5) -> list[WebResult]:
    """Live web search. Returns an empty list - not an error - when no key is configured or the call fails,
    so callers can treat "no web context" exactly like "no catalog matches" instead of a hard failure."""
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    try:
        response = _client().search(query, max_results=max_results)
    except Exception:
        logger.exception("web_search_failed")
        return []
    return [
        WebResult(label=f"W{i + 1}", title=item.get("title") or "Web result", url=item.get("url", ""), snippet=item.get("content", ""))
        for i, item in enumerate(response.get("results", []))
    ]
