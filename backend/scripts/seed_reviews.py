"""Dev-only utility: generate synthetic reviews for one product so the AI review summarizer has data to work with.

Real review submission goes through POST /api/v1/products/{id}/reviews as an authenticated shopper. This
script exists only because a fresh catalog has zero reviews and manually creating thousands of accounts to
demo "summarize 5000 reviews" isn't practical - it bypasses the API and writes directly to the database.

Usage (from backend/, with the venv active and a real Postgres configured):
    python -m scripts.seed_reviews <product_id> --count 5000
"""
import argparse
import random
from uuid import UUID, uuid4
from app.db.session import SessionLocal
from app.models import Product, Review, User
from app.services.reviews import recompute_rating

POSITIVE_FRAGMENTS = [
    "Exceeded my expectations, works flawlessly every day.",
    "Build quality feels premium and the battery easily lasts a full day.",
    "Setup took two minutes and it's been rock solid since.",
    "Great value for the price, would buy again without hesitation.",
    "Customer support was responsive the one time I had a question.",
]
NEGATIVE_FRAGMENTS = [
    "Battery life dropped noticeably after about three months of use.",
    "Arrived with a scratch on the casing, had to request a replacement.",
    "The companion app crashes constantly on my phone.",
    "Feels overpriced compared to similar options I've tried.",
    "Customer support took over a week to respond to my ticket.",
]
NEUTRAL_FRAGMENTS = [
    "Does what it says, nothing more, nothing less.",
    "Decent for the price but the competition has caught up recently.",
]
RATING_WEIGHTS = [5, 15, 15, 35, 30]  # skewed positive, matching a typical real catalog


def _body_for(rating: int) -> str:
    if rating >= 4: return random.choice(POSITIVE_FRAGMENTS)
    if rating <= 2: return random.choice(NEGATIVE_FRAGMENTS)
    return random.choice(NEUTRAL_FRAGMENTS)


def seed(product_id: UUID, count: int) -> None:
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product: raise SystemExit(f"No product with id {product_id}")
        for batch_start in range(0, count, 500):
            batch_end = min(batch_start + 500, count)
            rows = []
            for i in range(batch_start, batch_end):
                rating = random.choices([1, 2, 3, 4, 5], weights=RATING_WEIGHTS)[0]
                user = User(id=uuid4(), email=f"demo-reviewer-{product_id}-{i}@example.internal", display_name=f"Demo Reviewer {i}", is_active=True)
                db.add(user)
                rows.append((user, rating))
            db.flush()
            for user, rating in rows:
                db.add(Review(id=uuid4(), user_id=user.id, product_id=product.id, rating=rating, title=None, body=_body_for(rating), is_verified_purchase=random.random() < 0.7))
            db.commit()
            print(f"Seeded {batch_end}/{count}")
        recompute_rating(db, product)
        db.commit()
        print(f"Done. {product.title}: average_rating={product.average_rating}, review_count={product.review_count}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product_id", type=UUID)
    parser.add_argument("--count", type=int, default=5000)
    args = parser.parse_args()
    seed(args.product_id, args.count)
