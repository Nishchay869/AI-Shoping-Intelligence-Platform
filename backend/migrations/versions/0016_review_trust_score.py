"""Add reviews.trust_score - the fake-review-detection ensemble's fake-probability output (0=genuine-looking,
1=fake-looking), scored best-effort at review-create time (services/reviews.py) and backfilled for existing
rows by scripts/backfill_review_trust_scores.py. Nullable: rows are unscored until first scored, and a
scoring outage must never block a review write (mirrors reviews.embedding's own best-effort nullability).

The "trusted / uncertain / likely_fake" tier shown in the API is computed at read time in ReviewResponse
(schemas/reviews.py) via a threshold on this one number - not stored, so there's no second column that can
drift out of sync with the score it's derived from.

Revision ID: 0016_review_trust_score
Revises: 0015_receipt_image_hash
"""
from alembic import op
import sqlalchemy as sa

revision = "0016_review_trust_score"
down_revision = "0015_receipt_image_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reviews", sa.Column("trust_score", sa.Numeric(5, 4), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "trust_score")
