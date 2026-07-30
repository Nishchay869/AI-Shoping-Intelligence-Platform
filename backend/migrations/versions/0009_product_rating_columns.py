"""Add products.average_rating and products.review_count - columns the Product ORM model and
services/reviews.py's recompute_rating() have always referenced, but which no earlier migration actually
created. Caught by running the full migration chain and a real review submission against a real database
for the first time (see backend/tests/integration/test_reviews_service.py) - every prior verification of
review submission in this project used a mocked DB session, which happily accepts writes to columns that
don't really exist.

Revision ID: 0009_product_rating_columns
Revises: 0008_personalization
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_product_rating_columns"
down_revision = "0008_personalization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("average_rating", sa.Numeric(2, 1), nullable=True))
    op.add_column("products", sa.Column("review_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("products", "review_count")
    op.drop_column("products", "average_rating")
