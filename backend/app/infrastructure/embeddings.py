"""Gemini embeddings client: turns product and query text into vectors for pgvector similarity search.
Reuses llm.py's cached google-genai client rather than opening a second one - see that module's docstring
for why the client itself must be cached (a live SDK issue with per-call instances)."""
import logging
from google.genai import types
from app.core.config import get_settings
from app.core.exceptions import ServiceUnavailableError
from app.infrastructure.llm import _client

logger = logging.getLogger(__name__)


def embed_query(text: str) -> list[float]:
    """Embed one shopper-facing query string for similarity search against indexed product vectors."""
    settings = get_settings()
    try:
        response = _client().models.embed_content(
            model=settings.embedding_model,
            contents=[text],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=settings.embedding_dimensions),
        )
    except Exception as exc:
        logger.exception("embedding_query_failed")
        raise ServiceUnavailableError("Failed to embed the search query") from exc
    return response.embeddings[0].values


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed a batch of product descriptions for indexing; task_type differs from query embeddings on purpose."""
    settings = get_settings()
    try:
        response = _client().models.embed_content(
            model=settings.embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=settings.embedding_dimensions),
        )
    except Exception as exc:
        logger.exception("embedding_documents_failed")
        raise ServiceUnavailableError("Failed to embed product batch") from exc
    return [embedding.values for embedding in response.embeddings]
