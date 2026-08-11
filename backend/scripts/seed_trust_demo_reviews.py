"""Dev-only utility: seed a handful of obviously-fake and obviously-genuine review texts for one product -
distinct from scripts/seed_reviews.py's neutral, realistic fragments - so a demo of the fake-review trust
badge shows a believable spread of scores instead of everything landing in "uncertain". Bypasses the API and
writes directly to the database, same as seed_reviews.py. Inserts rows unscored (trust_score stays NULL) -
run scripts/backfill_review_trust_scores afterward to actually score them, the same path any real backfilled
review goes through.

Usage (from backend/, with the venv active and a real Postgres configured):
    python -m scripts.seed_trust_demo_reviews <product_id>
"""
import argparse
from uuid import UUID, uuid4
from app.db.session import SessionLocal
from app.models import Product, Review, User
from app.services.reviews import recompute_rating

OBVIOUSLY_FAKE = [
    "THIS IS HANDS DOWN THE BEST PRODUCT I HAVE EVER PURCHASED IN MY ENTIRE LIFE!!! BUY IT NOW BEFORE THE PRICE GOES UP, YOU WILL NOT REGRET IT!!!",
    "5 stars is NOT enough, this deserves 10 stars easily!!! Absolutely obsessed, life changing purchase, everyone needs this RIGHT NOW!!!",
    "WOW just WOW!!! Exceeded every single expectation, trust me on this one, best decision of my life!!! Highly highly recommend to EVERYONE!!!",
    "I was skeptical at first but now I am a TOTAL believer!!! This company clearly cares SO much, I tell all my friends and family to buy immediately!!!",
    "DO NOT waste your money anywhere else, this is the ONLY product you will EVER need!!! Perfect in every way, 100% PERFECT, no complaints whatsoever!!!",
    "Absolutely incredible, changed my whole life overnight!!! Already bought THREE more as gifts, everyone I know needs to buy this TODAY!!!",
]
OBVIOUSLY_GENUINE = [
    "After about six weeks of daily use, the hinge feels slightly looser than when I first got it, though it still closes fine. Shipping took four extra days because of a courier delay, but packaging kept everything undamaged. Reasonable buy for the price; curious how it holds up after a year.",
    "I compared this against two similar options first. Build quality is noticeably better - less flex in the casing - but the companion app is clunkier than the competitor's. Battery life is as advertised, roughly 9 hours at 70% brightness.",
    "Not perfect: the included cable is shorter than expected and the manual only covers the basics. That said, it's done what I needed for two months without issue, and support answered my warranty question within a day.",
    "The stitching on one seam was slightly uneven out of the box, but a message to support got a replacement shipped within a week, no argument. Fit is true to size and the material feels sturdy for the price.",
    "Works as described. Heavier than the photos suggested, which matters if you carry it daily, but the charging port has held up fine after regular use. Not exceptional, but a fair, honest purchase.",
    "Mixed feelings - screen quality is genuinely excellent, but a software update three weeks in introduced a bug where notifications sometimes duplicate. Reported it, still waiting to hear back. Would still recommend overall.",
]


def seed(product_id: UUID) -> None:
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product: raise SystemExit(f"No product with id {product_id}")
        for i, body in enumerate(OBVIOUSLY_FAKE):
            user = User(id=uuid4(), email=f"demo-trust-fake-{product_id}-{i}@example.internal", display_name=f"Demo Reviewer F{i}", is_active=True)
            db.add(user); db.flush()
            db.add(Review(id=uuid4(), user_id=user.id, product_id=product.id, rating=5, body=body, is_verified_purchase=False))
        for i, body in enumerate(OBVIOUSLY_GENUINE):
            user = User(id=uuid4(), email=f"demo-trust-genuine-{product_id}-{i}@example.internal", display_name=f"Demo Reviewer G{i}", is_active=True)
            db.add(user); db.flush()
            db.add(Review(id=uuid4(), user_id=user.id, product_id=product.id, rating=4, body=body, is_verified_purchase=True))
        db.commit()
        recompute_rating(db, product)
        db.commit()
        print(f"Seeded {len(OBVIOUSLY_FAKE)} obviously-fake + {len(OBVIOUSLY_GENUINE)} obviously-genuine reviews (unscored - run scripts.backfill_review_trust_scores next).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product_id", type=UUID)
    args = parser.parse_args()
    seed(args.product_id)
