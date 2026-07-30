"""Deterministic NLP preprocessing over raw reviews: cleaning, deduplication, rating statistics, keyword frequency.

These run entirely without an LLM call, so they're cheap to apply to all 5000 reviews up front - both to
improve what the LLM sees (clean, deduplicated text) and to give the final summary a numeric backbone
(rating distribution, keyword frequency) that the LLM's qualitative output is grounded against.
"""
import re
from collections import Counter
from app.models import Review
from app.schemas.reviews import KeywordFrequency, RatingBreakdown

_WHITESPACE = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WORD = re.compile(r"[a-z]{3,}")

STOPWORDS = frozenset(
    "a an the this that these those i you he she it we they my your his her its our their and or but if "
    "then so because as of to in on at for with without from by about into over under again further is are "
    "was were be been being have has had do does did will would should could can just not no nor too very "
    "s t don now product item bought buy purchase purchased".split()
)


def review_document_text(review: Review) -> str:
    """Canonical text representation of a review for embedding - shared by write-time embedding, the
    backfill script, and (implicitly) the RAG retriever, so a review is never embedded two different ways."""
    return clean_text(f"{review.title or ''} {review.body or ''}")


def clean_text(text: str | None) -> str:
    """Collapse whitespace and strip control characters without destroying meaning-bearing punctuation."""
    if not text: return ""
    return _WHITESPACE.sub(" ", text).strip()


def _dedup_key(text: str) -> str:
    """Normalize a review body to a comparable key so copy-pasted or duplicate-submitted reviews collapse together."""
    lowered = text.lower().strip()
    return _WHITESPACE.sub(" ", _NON_ALNUM.sub("", lowered))


def deduplicate(reviews: list[Review]) -> list[Review]:
    """Drop exact and near-exact duplicate review bodies (spam or accidental double-submits skew both stats and the LLM)."""
    seen: set[str] = set()
    unique: list[Review] = []
    for review in reviews:
        key = _dedup_key(review.body or "")
        if key and key in seen: continue
        if key: seen.add(key)
        unique.append(review)
    return unique


def compute_rating_breakdown(reviews: list[Review]) -> RatingBreakdown:
    """Pure statistics from star ratings - the numeric ground truth the LLM's qualitative sentiment is checked against."""
    total = len(reviews)
    histogram = {stars: 0 for stars in range(1, 6)}
    for review in reviews: histogram[review.rating] = histogram.get(review.rating, 0) + 1
    average = round(sum(review.rating for review in reviews) / total, 2) if total else None
    positive = histogram[4] + histogram[5]
    negative = histogram[1] + histogram[2]
    neutral = histogram[3]
    pct = lambda count: round((count / total) * 100, 1) if total else 0.0
    return RatingBreakdown(average_rating=average, total_reviews=total, histogram=histogram, positive_pct=pct(positive), neutral_pct=pct(neutral), negative_pct=pct(negative))


def extract_top_keywords(reviews: list[Review], top_n: int = 15) -> list[KeywordFrequency]:
    """Bag-of-words frequency analysis over review text, independent of the LLM - a classic NLP cross-check for what the summary claims."""
    counts: Counter[str] = Counter()
    for review in reviews:
        text = f"{review.title or ''} {review.body or ''}".lower()
        words = [word for word in _WORD.findall(text) if word not in STOPWORDS]
        counts.update(words)
    return [KeywordFrequency(keyword=word, mentions=count) for word, count in counts.most_common(top_n)]
