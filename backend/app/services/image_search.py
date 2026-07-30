"""Image-based product search: embed the uploaded photo with CLIP, then run pgvector cosine search over
Product.image_embedding - the same retrieve-by-vector pattern used elsewhere in this app (recommendations,
RAG), just with an image query instead of a text one.
"""
from PIL import UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.exceptions import ServiceUnavailableError
from app.infrastructure.clip_embeddings import embed_image
from app.models import Product

MIN_SIMILARITY = 0.15  # below this, a "match" is closer to noise than a genuine visual match


def search_by_image(db: Session, image_bytes: bytes, top_k: int = 10) -> list[tuple[Product, float]]:
    """Return products whose photo is visually similar to the uploaded image, most similar first."""
    try:
        query_embedding = embed_image(image_bytes)
    except UnidentifiedImageError as exc:
        raise ValueError("The uploaded file is not a readable image") from exc
    except Exception as exc:
        raise ServiceUnavailableError("Could not process the uploaded image") from exc

    query = (
        select(Product, (1 - Product.image_embedding.cosine_distance(query_embedding)).label("similarity"))
        .where(Product.image_embedding.is_not(None))
        .order_by(Product.image_embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    rows = db.execute(query).all()
    return [(product, float(similarity)) for product, similarity in rows if similarity >= MIN_SIMILARITY]
