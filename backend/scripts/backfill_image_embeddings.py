"""One-off indexing job: download every product's photo and embed it with CLIP, so it becomes reachable by
image-based search (POST /products/image-search).

No API key required - CLIP runs locally via transformers. Run from backend/ with the venv active:
    python -m scripts.backfill_image_embeddings
"""
import httpx
from sqlalchemy import select
from app.db.session import SessionLocal
from app.infrastructure.clip_embeddings import embed_images
from app.models import Product

BATCH_SIZE = 16  # smaller than the text-embedding backfills - each item here is a full image download + CLIP forward pass


def _download(url: str) -> bytes | None:
    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        print(f"  skip (download failed): {url} ({exc})")
        return None


def backfill() -> None:
    db = SessionLocal()
    try:
        products = list(db.scalars(select(Product).where(Product.image_embedding.is_(None), Product.image_url.is_not(None))))
        print(f"Found {len(products)} products with an image_url but no image_embedding")

        done = 0
        for start in range(0, len(products), BATCH_SIZE):
            batch = products[start:start + BATCH_SIZE]
            downloaded = [(product, _download(product.image_url)) for product in batch]
            indexable = [(product, image_bytes) for product, image_bytes in downloaded if image_bytes is not None]
            if indexable:
                vectors = embed_images([image_bytes for _, image_bytes in indexable])
                for (product, _), vector in zip(indexable, vectors):
                    product.image_embedding = vector
                db.commit()
            done += len(batch)
            print(f"Processed {done}/{len(products)} ({len(indexable)}/{len(batch)} embedded in this batch)")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
