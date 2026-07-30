"""Catalog search use-case: validated filters, deterministic sorting, and cacheable output."""
from dataclasses import dataclass
from math import ceil
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from app.models import Product


@dataclass(frozen=True)
class ProductSearch:
    q: str | None
    category: str | None
    brand: str | None
    min_price_minor: int | None
    max_price_minor: int | None
    min_rating: float | None
    page: int
    page_size: int
    sort: str
    direction: str


def search_products(db: Session, filters: ProductSearch) -> tuple[list[Product], int]:
    """Execute one bounded, parameterized search plus an exact total count."""
    query: Select = select(Product)
    predicates = []
    if filters.q:
        term = filters.q.strip()
        predicates.append((Product.title.ilike(f"%{term}%")) | (Product.brand.ilike(f"%{term}%")))
    if filters.category: predicates.append(func.lower(Product.category) == filters.category.strip().lower())
    if filters.brand: predicates.append(func.lower(Product.brand) == filters.brand.strip().lower())
    if filters.min_price_minor is not None: predicates.append(Product.current_price_minor >= filters.min_price_minor)
    if filters.max_price_minor is not None: predicates.append(Product.current_price_minor <= filters.max_price_minor)
    if filters.min_rating is not None: predicates.append(Product.average_rating >= filters.min_rating)
    if predicates: query = query.where(*predicates)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    column = {"relevance": Product.created_at, "price": Product.current_price_minor, "rating": Product.average_rating, "newest": Product.created_at}[filters.sort]
    ordering = column.asc() if filters.direction == "asc" else column.desc()
    items = list(db.scalars(query.order_by(ordering, Product.id.asc()).offset((filters.page - 1) * filters.page_size).limit(filters.page_size)))
    return items, total


def page_count(total: int, page_size: int) -> int:
    """Calculate display page count while keeping an empty result set at one page."""
    return max(1, ceil(total / page_size))
