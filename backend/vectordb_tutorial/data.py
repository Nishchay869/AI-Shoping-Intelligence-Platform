"""Shared sample corpus and embedding function used by every vector database demo in this tutorial.

Held constant across ChromaDB/FAISS/Qdrant/Pinecone so the only variable between demos is the vector
database itself - same embedding model, same documents, same query. That's what makes the "same query,
different backend" comparison in compare.py meaningful: if the rankings agree, you're seeing that these
are genuinely interchangeable engines for the same underlying math, not that one is smarter than another.

Uses sentence-transformers (already-installed, local, no API key) rather than a paid embeddings API, so
every demo in this tutorial runs end-to-end offline.
"""
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Turn text into 384-dim dense vectors. Every demo in this tutorial embeds with this exact function,
    so the same sentence always lands at the same point in vector space regardless of which DB stores it."""
    return get_model().encode(list(texts), convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True).tolist()


@dataclass(frozen=True)
class Document:
    id: str
    type: str  # "product" | "review" | "specification"
    text: str
    metadata: dict


PRODUCTS = [
    {"id": "sony-wh1000xm5", "title": "Sony WH-1000XM5 Wireless Headphones", "brand": "Sony", "category": "Audio", "price_usd": 349.0},
    {"id": "apple-watch-se", "title": "Apple Watch SE GPS 40mm", "brand": "Apple", "category": "Wearables", "price_usd": 249.0},
    {"id": "nike-air-max-90", "title": "Nike Air Max 90 Running Shoes", "brand": "Nike", "category": "Fashion", "price_usd": 120.0},
    {"id": "kindle-paperwhite", "title": "Kindle Paperwhite 16GB", "brand": "Amazon", "category": "Electronics", "price_usd": 149.0},
    {"id": "bose-qc-earbuds", "title": "Bose QuietComfort Ultra Earbuds", "brand": "Bose", "category": "Audio", "price_usd": 299.0},
    {"id": "fitbit-charge-6", "title": "Fitbit Charge 6 Fitness Tracker", "brand": "Fitbit", "category": "Wearables", "price_usd": 159.0},
]

REVIEWS = [
    {"id": "rev-1", "product_id": "sony-wh1000xm5", "rating": 5, "text": "The noise cancellation is incredible, I can't hear my coworkers at all anymore. Battery easily lasts a full week of commuting."},
    {"id": "rev-2", "product_id": "sony-wh1000xm5", "rating": 2, "text": "Battery life dropped a lot after six months of daily use, now barely lasts a day."},
    {"id": "rev-3", "product_id": "apple-watch-se", "rating": 4, "text": "Great for tracking runs and swims, GPS locks on fast. Wish the battery lasted more than a day and a half."},
    {"id": "rev-4", "product_id": "apple-watch-se", "rating": 5, "text": "The sleep tracking and heart rate alerts have genuinely helped me catch an irregular heartbeat early."},
    {"id": "rev-5", "product_id": "nike-air-max-90", "rating": 4, "text": "Super comfortable for all-day wear but the cushioning compresses fast if you run more than a few miles a week."},
    {"id": "rev-6", "product_id": "kindle-paperwhite", "rating": 5, "text": "Reading by the pool is finally stress-free since it survived being dropped in the water twice."},
    {"id": "rev-7", "product_id": "bose-qc-earbuds", "rating": 3, "text": "Noise cancellation is good but not as strong as my old over-ear headphones. Comfortable for hours though."},
    {"id": "rev-8", "product_id": "fitbit-charge-6", "rating": 4, "text": "Heart rate accuracy during workouts is spot on, but the app notifications lag behind by a few minutes."},
]

SPECIFICATIONS = [
    {"id": "spec-1", "product_id": "sony-wh1000xm5", "name": "Battery life", "text": "Battery life: up to 30 hours with noise cancellation on, 40 hours with it off."},
    {"id": "spec-2", "product_id": "sony-wh1000xm5", "name": "Connectivity", "text": "Connectivity: Bluetooth 5.2 with multipoint pairing for two devices at once."},
    {"id": "spec-3", "product_id": "apple-watch-se", "name": "Water resistance", "text": "Water resistance: rated to 50 meters, suitable for shallow-water activities and swimming."},
    {"id": "spec-4", "product_id": "apple-watch-se", "name": "Battery life", "text": "Battery life: up to 18 hours of typical use per charge."},
    {"id": "spec-5", "product_id": "nike-air-max-90", "name": "Weight", "text": "Weight: approximately 340 grams per shoe in a men's size 10."},
    {"id": "spec-6", "product_id": "kindle-paperwhite", "name": "Water resistance", "text": "Water resistance: IPX8 rated, safe in fresh water up to 2 meters for 60 minutes."},
    {"id": "spec-7", "product_id": "bose-qc-earbuds", "name": "Battery life", "text": "Battery life: 6 hours per charge, 24 hours total including the charging case."},
    {"id": "spec-8", "product_id": "fitbit-charge-6", "name": "Sensors", "text": "Sensors: heart rate, SpO2, skin temperature, and built-in GPS."},
]


def _product_text(product: dict) -> str:
    return f"{product['title']}. Brand: {product['brand']}. Category: {product['category']}. Price: ${product['price_usd']:.2f}"


def all_documents() -> list[Document]:
    """Every product, review, and specification as one uniform list of embeddable (text, metadata) documents."""
    documents = []
    for product in PRODUCTS:
        documents.append(Document(id=f"product:{product['id']}", type="product", text=_product_text(product), metadata={"product_id": product["id"], "title": product["title"], "brand": product["brand"], "category": product["category"], "price_usd": product["price_usd"]}))
    for review in REVIEWS:
        documents.append(Document(id=f"review:{review['id']}", type="review", text=review["text"], metadata={"product_id": review["product_id"], "rating": review["rating"]}))
    for spec in SPECIFICATIONS:
        documents.append(Document(id=f"spec:{spec['id']}", type="specification", text=spec["text"], metadata={"product_id": spec["product_id"], "name": spec["name"]}))
    return documents
