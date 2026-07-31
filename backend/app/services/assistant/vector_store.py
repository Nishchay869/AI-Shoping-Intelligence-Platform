"""Builds and queries a Chroma vector store for the shopping assistant's semantic-search tools, using Gemini
embeddings. Deliberately separate from the RAG chat system built earlier in this project (pgvector, also
Gemini-backed but via a different model/output_dimensionality): even same-provider embeddings aren't
comparable across models or dimensionalities, so this assistant needs its own index rather than reusing
Product.embedding/Review.embedding.
"""
import threading
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.currency import to_inr
from app.models import Product, Review

PERSIST_DIR = Path(__file__).resolve().parent / "storage" / "chroma"
COLLECTION_NAME = "shopping_assistant"
_store: Chroma | None = None
_store_lock = threading.Lock()


def _embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(model=settings.assistant_embedding_model, google_api_key=settings.gemini_api_key)


def get_store() -> Chroma:
    """Explicit double-checked locking, not @lru_cache: lru_cache's internal lock only protects its cache
    dict, not the "call the wrapped function" step - concurrent callers on a cold cache can still all invoke
    the function body at once. That's exactly what chromadb's own internal client registry
    (SharedSystemClient._identifier_to_system) isn't safe against either: concurrent first-time construction
    of the same PersistentClient path reproduced both a KeyError inside chromadb's own bookkeeping and, in
    another run, an AttributeError tearing down a half-initialized Rust binding - two symptoms of the same
    race, not two separate bugs. An explicit lock around the whole check-and-construct sequence is what
    actually guarantees single construction."""
    global _store
    if _store is not None:
        return _store
    with _store_lock:
        if _store is None:
            _store = Chroma(collection_name=COLLECTION_NAME, embedding_function=_embeddings(), persist_directory=str(PERSIST_DIR))
        return _store


def _product_text(product: Product) -> str:
    parts = [product.title]
    if product.brand: parts.append(f"Brand: {product.brand}")
    if product.category: parts.append(f"Category: {product.category}")
    parts.append(f"Price: {to_inr(product.current_price_minor, product.currency)}")
    if product.average_rating is not None: parts.append(f"Rating: {product.average_rating}/5 from {product.review_count} reviews")
    return ". ".join(parts)


def _review_text(review: Review) -> str:
    title = f'"{review.title}" - ' if review.title else ""
    return f"{review.rating}/5 stars. {title}{review.body or ''}".strip()


def reindex(db: Session) -> int:
    """Rebuild the collection from the current Postgres data. Unlike the RAG system's write-time embedding,
    this demo reindexes in one batch - call it after catalog/review changes, or on a schedule."""
    global _store
    with _store_lock:
        _store = None
    store = get_store()
    try:
        store.delete_collection()
    except Exception:
        pass
    with _store_lock:
        _store = None
    store = get_store()

    documents = [Document(id=f"product:{product.id}", page_content=_product_text(product), metadata={"type": "product", "product_id": str(product.id)}) for product in db.scalars(select(Product))]
    documents += [Document(id=f"review:{review.id}", page_content=_review_text(review), metadata={"type": "review", "product_id": str(review.product_id)}) for review in db.scalars(select(Review).where(Review.is_visible.is_(True)))]
    if documents:
        store.add_documents(documents, ids=[doc.id for doc in documents])
    return len(documents)


def search(query: str, doc_type: str | None = None, product_id: str | None = None, k: int = 5) -> list[tuple[Document, float]]:
    """Semantic similarity search, optionally filtered by document type and/or product."""
    conditions = [{key: value} for key, value in {"type": doc_type, "product_id": product_id}.items() if value]
    filter_dict = None
    if len(conditions) == 1:
        filter_dict = conditions[0]
    elif len(conditions) > 1:
        filter_dict = {"$and": conditions}
    return get_store().similarity_search_with_relevance_scores(query, k=k, filter=filter_dict)
