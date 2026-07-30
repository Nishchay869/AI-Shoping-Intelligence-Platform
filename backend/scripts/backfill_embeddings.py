"""One-off indexing job: embed every product and review missing a vector, so both become reachable by the
recommendation engine's similarity search and the RAG retriever.

Run from backend/ with the venv active and GEMINI_API_KEY configured:
    python -m scripts.backfill_embeddings
"""
from sqlalchemy import select
from app.db.session import SessionLocal
from app.infrastructure.embeddings import embed_documents
from app.models import Product, Review
from app.services.review_nlp import review_document_text

BATCH_SIZE = 64


def _describe_product(product: Product) -> str:
    """Render one product as embeddable text using the same vocabulary the recommendation engine searches against."""
    parts = [product.title]
    if product.brand: parts.append(f"Brand: {product.brand}")
    if product.category: parts.append(f"Category: {product.category}")
    parts.append(f"Price: {product.current_price_minor / 100:.2f} {product.currency}")
    if product.average_rating is not None: parts.append(f"Rated {product.average_rating} from {product.review_count} reviews")
    return ". ".join(parts)


def _backfill(label: str, rows: list, describe) -> None:
    print(f"Found {len(rows)} {label} without embeddings")
    for start in range(0, len(rows), BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        texts = [describe(row) for row in batch]
        indexable = [(row, text) for row, text in zip(batch, texts) if text.strip()]
        if indexable:
            vectors = embed_documents([text for _, text in indexable])
            for (row, _), vector in zip(indexable, vectors):
                row.embedding = vector
        yield len(batch)


def backfill() -> None:
    db = SessionLocal()
    try:
        products = list(db.scalars(select(Product).where(Product.embedding.is_(None))))
        done = 0
        for count in _backfill("products", products, _describe_product):
            done += count
            db.commit()
            print(f"Embedded products {done}/{len(products)}")

        reviews = list(db.scalars(select(Review).where(Review.embedding.is_(None))))
        done = 0
        for count in _backfill("reviews", reviews, review_document_text):
            done += count
            db.commit()
            print(f"Embedded reviews {done}/{len(reviews)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
