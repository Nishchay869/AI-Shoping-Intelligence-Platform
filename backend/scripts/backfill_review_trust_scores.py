"""One-off scoring job: run the fake-review-detection ensemble over every review missing a trust_score, so
both newly-created reviews (this feature's best-effort write-time path can still miss, e.g. an infrastructure
hiccup during the ensemble's first load) and pre-existing reviews (everything seeded by scripts/seed_reviews.py
and scripts/seed_trust_demo_reviews.py before this feature existed) get scored.

No scheduler exists in this backend - wire this to cron alongside scripts/backfill_embeddings.py and
scripts/send_warranty_alerts.py, e.g.:
    0 3 * * * cd /path/to/backend && .venv/bin/python -m scripts.backfill_review_trust_scores

Usage (from backend/, with the venv active and a real Postgres configured):
    python -m scripts.backfill_review_trust_scores
"""
from sqlalchemy import select
from app.db.session import SessionLocal
from app.infrastructure.fake_review_detection import score_texts
from app.models import Review
from app.services.review_nlp import review_document_text

BATCH_SIZE = 32  # small: each batch runs a real BERT + Sentence-Transformer forward pass on CPU


def backfill() -> None:
    db = SessionLocal()
    try:
        reviews = list(db.scalars(select(Review).where(Review.trust_score.is_(None))))
        print(f"Found {len(reviews)} reviews without a trust score")
        done = 0
        for start in range(0, len(reviews), BATCH_SIZE):
            batch = reviews[start:start + BATCH_SIZE]
            scorable = [(review, review_document_text(review)) for review in batch]
            scorable = [(review, text) for review, text in scorable if text.strip()]
            if scorable:
                scores = score_texts([text for _, text in scorable])
                for (review, _), score in zip(scorable, scores):
                    review.trust_score = score
            done += len(batch)
            db.commit()
            print(f"Scored {done}/{len(reviews)}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
