"""Retriever: the "R" in RAG. Embeds the shopper's question once, then runs two pgvector similarity
searches - one over indexed products, one over indexed reviews - and returns a unified, score-ranked set
of source chunks. This is deliberately different from the recommendation engine's retrieval (which filters
by hard budget/brand constraints and only searches products): a RAG retriever's job is to find whatever
text - product facts or review snippets - best answers an arbitrary free-form question, so both indexes are
searched every time and left to compete on relevance score alone, with no hard filters beyond an optional
single product scope.
"""
from dataclasses import dataclass, replace
from typing import Literal
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.infrastructure.embeddings import embed_query
from app.models import Product, Review

DEFAULT_TOP_K_PRODUCTS = 4
DEFAULT_TOP_K_REVIEWS = 6
MIN_SIMILARITY = 0.2  # below this a "match" is closer to noise than signal - better to admit no context than force one


@dataclass(frozen=True)
class RetrievedChunk:
    label: str                                    # "P1", "R3", ... - what the prompt and the LLM cite back
    source_type: Literal["product", "review"]
    source_id: UUID
    product_id: UUID
    text: str
    similarity: float                             # 1 - cosine_distance; 1.0 = identical, 0.0 = unrelated


def _product_text(product: Product) -> str:
    parts = [product.title]
    if product.brand: parts.append(f"Brand: {product.brand}")
    if product.category: parts.append(f"Category: {product.category}")
    parts.append(f"Price: {product.current_price_minor / 100:.2f} {product.currency}")
    if product.average_rating is not None: parts.append(f"Rating: {product.average_rating}/5 from {product.review_count} reviews")
    parts.append(f"Retailer: {product.retailer}")
    return ". ".join(parts)


def _review_text(review: Review) -> str:
    title = f'"{review.title}" - ' if review.title else ""
    return f"{review.rating}/5 stars. {title}{review.body or ''}".strip()


def _retrieve_products(db: Session, query_embedding: list[float], product_id: UUID | None, top_k: int) -> list[tuple[Product, float]]:
    query = select(Product, (1 - Product.embedding.cosine_distance(query_embedding)).label("similarity")).where(Product.embedding.is_not(None))
    if product_id is not None:
        query = query.where(Product.id == product_id)
    query = query.order_by(Product.embedding.cosine_distance(query_embedding)).limit(top_k)
    return [(row[0], float(row[1])) for row in db.execute(query).all()]


def _retrieve_reviews(db: Session, query_embedding: list[float], product_id: UUID | None, top_k: int) -> list[tuple[Review, float]]:
    query = select(Review, (1 - Review.embedding.cosine_distance(query_embedding)).label("similarity")).where(Review.embedding.is_not(None), Review.is_visible.is_(True))
    if product_id is not None:
        query = query.where(Review.product_id == product_id)
    query = query.order_by(Review.embedding.cosine_distance(query_embedding)).limit(top_k)
    return [(row[0], float(row[1])) for row in db.execute(query).all()]


def retrieve(db: Session, question: str, product_id: UUID | None = None, top_k_products: int = DEFAULT_TOP_K_PRODUCTS, top_k_reviews: int = DEFAULT_TOP_K_REVIEWS) -> list[RetrievedChunk]:
    """Embed once, search both indexes, merge and rank by similarity. `product_id` scopes both searches to
    one product (an "ask about this product" widget); omit it for a catalog-wide shopping assistant."""
    query_embedding = embed_query(question)
    products = _retrieve_products(db, query_embedding, product_id, top_k_products)
    reviews = _retrieve_reviews(db, query_embedding, product_id, top_k_reviews)

    chunks = [
        RetrievedChunk(label="", source_type="product", source_id=product.id, product_id=product.id, text=_product_text(product), similarity=similarity)
        for product, similarity in products
    ] + [
        RetrievedChunk(label="", source_type="review", source_id=review.id, product_id=review.product_id, text=_review_text(review), similarity=similarity)
        for review, similarity in reviews
    ]
    chunks = sorted((chunk for chunk in chunks if chunk.similarity >= MIN_SIMILARITY), key=lambda chunk: chunk.similarity, reverse=True)

    counters = {"product": 0, "review": 0}
    labeled: list[RetrievedChunk] = []
    for chunk in chunks:
        counters[chunk.source_type] += 1
        prefix = "P" if chunk.source_type == "product" else "R"
        labeled.append(replace(chunk, label=f"{prefix}{counters[chunk.source_type]}"))
    return labeled
