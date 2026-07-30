"""LangChain tools: the concrete actions the LangGraph agent can take. Each tool is deliberately narrow and
named after one shopper intent (search, detail lookup, comparison, alternatives, recommendation) rather
than one do-everything tool - narrow, well-described tools are what let a tool-calling model pick the
right action reliably; a single vague "query_catalog" tool with a free-form instruction string is exactly
what these models are worst at using well.
"""
from uuid import UUID
from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.infrastructure.web_search import search_web
from app.models import Product, ProductSpecification
from app.services.assistant import vector_store
from app.services.assistant.currency import to_inr


def _session() -> Session:
    return SessionLocal()


def _format_product(product: Product, specs: list[ProductSpecification]) -> str:
    lines = [
        f"Title: {product.title}",
        f"Brand: {product.brand or 'unknown'}",
        f"Category: {product.category or 'unknown'}",
        f"Price: {to_inr(product.current_price_minor, product.currency)}",
        f"Retailer: {product.retailer}",
        f"Rating: {product.average_rating}/5 from {product.review_count} reviews" if product.average_rating is not None else "Rating: no reviews yet",
        f"Product ID: {product.id}",
    ]
    if specs:
        lines.append("Specifications:")
        lines.extend(f"  - {spec.name}: {spec.value}" for spec in specs)
    return "\n".join(lines)


def _format_search_hits(results: list[tuple]) -> str:
    return "\n\n".join(f"[relevance {score:.2f}] {doc.page_content} (product_id={doc.metadata['product_id']})" for doc, score in results)


@tool
def search_products(query: str, max_results: int = 5) -> str:
    """Semantically search the product catalog for items matching a description, e.g. 'noise cancelling headphones under $300'. Returns matching products with their product_id, price, and rating."""
    results = vector_store.search(query, doc_type="product", k=max_results)
    return _format_search_hits(results) if results else "No matching products found."


@tool
def get_product_details(product_id: str) -> str:
    """Look up full details and specifications for one product by its exact product_id (obtained from search_products, compare_products, or find_alternatives). Use this to explain specifications."""
    db = _session()
    try:
        product = db.get(Product, UUID(product_id))
        if not product:
            return f"No product found with id {product_id}."
        specs = list(db.scalars(select(ProductSpecification).where(ProductSpecification.product_id == product.id)))
        return _format_product(product, specs)
    finally:
        db.close()


@tool
def search_reviews(query: str, product_id: str = "", max_results: int = 5) -> str:
    """Semantically search buyer reviews for opinions matching a topic, e.g. 'battery complaints' or 'is it comfortable'. Pass product_id to scope to one product, or leave it blank to search all reviews."""
    results = vector_store.search(query, doc_type="review", product_id=product_id or None, k=max_results)
    return _format_search_hits(results) if results else "No matching reviews found."


@tool
def compare_products(product_ids: list[str]) -> str:
    """Fetch full details and specifications for two or more products side by side, for comparison. Pass exact product_ids from search_products."""
    if len(product_ids) < 2:
        return "Provide at least two product_ids to compare."
    db = _session()
    try:
        blocks = []
        for product_id in product_ids:
            product = db.get(Product, UUID(product_id))
            if not product:
                blocks.append(f"No product found with id {product_id}.")
                continue
            specs = list(db.scalars(select(ProductSpecification).where(ProductSpecification.product_id == product.id)))
            blocks.append(_format_product(product, specs))
        return "\n\n---\n\n".join(blocks)
    finally:
        db.close()


@tool
def find_alternatives(product_id: str, max_results: int = 5) -> str:
    """Find other products in the same category as the given product_id - use this for 'what else should I consider' or 'anything cheaper' questions."""
    db = _session()
    try:
        product = db.get(Product, UUID(product_id))
        if not product:
            return f"No product found with id {product_id}."
        query = select(Product).where(Product.category == product.category, Product.id != product.id).order_by(Product.average_rating.desc().nulls_last()).limit(max_results)
        alternatives = list(db.scalars(query))
        if not alternatives:
            return f"No other products found in the '{product.category}' category."
        return "\n\n".join(_format_product(alt, []) for alt in alternatives)
    finally:
        db.close()


@tool
def recommend_products(preferences: str, max_results: int = 5) -> str:
    """Recommend products based on a shopper's stated needs, budget, or preferences, e.g. 'a lightweight fitness tracker under $150 with GPS'. Searches the full catalog semantically."""
    results = vector_store.search(preferences, doc_type="product", k=max_results)
    return _format_search_hits(results) if results else "No matching products found for those preferences."


@tool(response_format="content_and_artifact")
def web_search(query: str, max_results: int = 5) -> tuple[str, list[dict]]:
    """Search the live web for general product information, news, specs, or comparisons that go beyond
    Pricewise's own catalog - use this alongside the catalog tools to supplement or verify an answer, not
    only when the catalog has nothing."""
    results = search_web(query, max_results=max_results)
    if not results:
        return "No web results found (or web search is not configured).", []
    content = "\n\n".join(f"[{result.label}] {result.title} ({result.url})\n{result.snippet}" for result in results)
    # The artifact carries the real (title, url) pairs out to the API response for clickable citations,
    # separate from `content` (what the LLM reads) - LangGraph preserves both on the resulting ToolMessage.
    artifact = [{"label": result.label, "title": result.title, "url": result.url} for result in results]
    return content, artifact


ALL_TOOLS = [search_products, get_product_details, search_reviews, compare_products, find_alternatives, recommend_products, web_search]
