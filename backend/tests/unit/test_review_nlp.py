"""Unit tests for deterministic review NLP preprocessing - no DB, no LLM. Review objects are stood in for
with SimpleNamespace since these functions only ever read .title/.body/.rating attributes."""
from types import SimpleNamespace

from app.services.review_nlp import clean_text, compute_rating_breakdown, deduplicate, extract_top_keywords


def _review(title: str = "", body: str = "", rating: int = 5):
    return SimpleNamespace(title=title, body=body, rating=rating)


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("Great   product!\n\nWorks  well.") == "Great product! Works well."


def test_clean_text_handles_none_and_empty() -> None:
    assert clean_text(None) == ""
    assert clean_text("") == ""


def test_deduplicate_drops_exact_duplicate_bodies() -> None:
    reviews = [_review(body="Great product, works well."), _review(body="Great product, works well.")]
    result = deduplicate(reviews)
    assert len(result) == 1


def test_deduplicate_drops_near_duplicates_ignoring_case_and_punctuation() -> None:
    reviews = [_review(body="Great product!!"), _review(body="great product")]
    result = deduplicate(reviews)
    assert len(result) == 1


def test_deduplicate_keeps_genuinely_different_reviews() -> None:
    reviews = [_review(body="Great product, fast shipping."), _review(body="Terrible, broke after a week.")]
    result = deduplicate(reviews)
    assert len(result) == 2


def test_deduplicate_never_collapses_empty_bodies_together() -> None:
    """Two reviews that both have no body text at all are not "duplicates of each other" - only real
    repeated content should count."""
    reviews = [_review(body=""), _review(body=""), _review(body="")]
    assert len(deduplicate(reviews)) == 3


def test_rating_breakdown_average_and_percentages() -> None:
    reviews = [_review(rating=5), _review(rating=5), _review(rating=1)]
    breakdown = compute_rating_breakdown(reviews)
    assert breakdown.total_reviews == 3
    assert breakdown.average_rating == round((5 + 5 + 1) / 3, 2)
    assert breakdown.positive_pct == round(2 / 3 * 100, 1)
    assert breakdown.negative_pct == round(1 / 3 * 100, 1)
    assert breakdown.neutral_pct == 0.0


def test_rating_breakdown_empty_input_does_not_divide_by_zero() -> None:
    breakdown = compute_rating_breakdown([])
    assert breakdown.total_reviews == 0
    assert breakdown.average_rating is None
    assert breakdown.positive_pct == 0.0


def test_rating_breakdown_histogram_covers_all_five_buckets() -> None:
    breakdown = compute_rating_breakdown([_review(rating=3)])
    assert breakdown.histogram == {1: 0, 2: 0, 3: 1, 4: 0, 5: 0}


def test_extract_top_keywords_ignores_stopwords_and_short_words() -> None:
    reviews = [_review(title="Great battery life", body="The battery life is great and the battery lasts long")]
    keywords = extract_top_keywords(reviews)
    words = [k.keyword for k in keywords]
    assert "battery" in words
    assert "the" not in words  # stopword
    assert "is" not in words  # stopword
    top = next(k for k in keywords if k.keyword == "battery")
    assert top.mentions == 3  # "battery" appears once in the title, twice in the body


def test_extract_top_keywords_respects_top_n() -> None:
    """_WORD only matches runs of letters, so distinct alphabetic words are needed here - "word0".."word29"
    would all collapse to the single token "word" (digits aren't part of the match), proving less than intended."""
    body = " ".join(chr(ord("a") + i) * 3 for i in range(10))  # "aaa bbb ccc ... jjj" - 10 distinct 3-letter words
    keywords = extract_top_keywords([_review(body=body)], top_n=5)
    assert len(keywords) == 5
