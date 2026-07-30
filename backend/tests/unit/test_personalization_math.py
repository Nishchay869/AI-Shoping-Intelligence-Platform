"""Unit tests for the personalized recommendation engine's pure vector arithmetic - no DB, no embedding API,
just the math that turns weighted signals into a taste vector and back into an explanation."""
import math
from datetime import datetime, timedelta, timezone

import pytest

from app.services import personalization as p


def test_weighted_average_leans_toward_the_heavier_signal() -> None:
    result = p._weighted_average([[1.0, 0.0], [0.0, 1.0]], [3.0, 1.0])
    assert result == [0.75, 0.25]


def test_weighted_average_equal_weights_is_a_plain_mean() -> None:
    result = p._weighted_average([[1.0, 0.0], [0.0, 1.0]], [1.0, 1.0])
    assert result == [0.5, 0.5]


def test_l2_normalize_produces_a_unit_vector() -> None:
    normed = p._l2_normalize([3.0, 4.0])
    assert normed == pytest.approx([0.6, 0.8])
    assert math.sqrt(sum(x * x for x in normed)) == pytest.approx(1.0)


def test_l2_normalize_zero_vector_is_returned_unchanged() -> None:
    """Guards against a division by zero if every signal somehow cancels out."""
    assert p._l2_normalize([0.0, 0.0]) == [0.0, 0.0]


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ([1.0, 0.0], [1.0, 0.0], 1.0),
        ([1.0, 0.0], [0.0, 1.0], 0.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
    ],
)
def test_cosine_similarity_known_angles(a, b, expected) -> None:
    assert p._cosine_similarity(a, b) == pytest.approx(expected)


def test_cosine_similarity_zero_vector_does_not_divide_by_zero() -> None:
    assert p._cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_recency_weight_is_one_at_zero_age() -> None:
    assert p._recency_weight(datetime.now(timezone.utc)) == pytest.approx(1.0, abs=1e-6)


def test_recency_weight_is_half_at_one_half_life() -> None:
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=p.RECENCY_HALF_LIFE_DAYS)
    assert p._recency_weight(thirty_days_ago) == pytest.approx(0.5, abs=1e-6)


def test_recency_weight_decays_toward_zero_but_never_negative() -> None:
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    weight = p._recency_weight(one_year_ago)
    assert 0 < weight < 0.01


def test_profile_vector_is_a_unit_vector_leaning_toward_the_stronger_signal() -> None:
    signals = [
        p.Signal(vector=[1.0, 0.0], weight=5.0, kind="purchase", label="Headphones", product_id=None),
        p.Signal(vector=[0.0, 1.0], weight=1.0, kind="click", label="Speaker", product_id=None),
    ]
    profile = p._profile_vector(signals)
    assert profile[0] > profile[1]
    assert math.sqrt(sum(x * x for x in profile)) == pytest.approx(1.0)


def test_nearest_signal_picks_highest_cosine_similarity_not_highest_weight() -> None:
    """A low-weight signal that's a near-perfect directional match should still "win" the explanation over a
    high-weight signal that's a worse directional match - weight shapes the profile vector, not the citation."""
    candidate = [0.0, 1.0]
    signals = [
        p.Signal(vector=[1.0, 0.0], weight=100.0, kind="purchase", label="Unrelated Big-Weight Purchase", product_id=None),
        p.Signal(vector=[0.01, 0.9999], weight=1.0, kind="click", label="Actually Similar Click", product_id=None),
    ]
    nearest = p._nearest_signal(candidate, signals)
    assert nearest.label == "Actually Similar Click"


@pytest.mark.parametrize(
    ("kind", "label", "expected"),
    [
        ("search", "wireless earbuds", 'Because you searched for "wireless earbuds"'),
        ("wishlist", "Noise Cancelling Headphones", "Because you wishlisted Noise Cancelling Headphones"),
        ("purchase", "Bluetooth Speaker", "Because you purchased Bluetooth Speaker"),
        ("click", "Phone Case", "Because you viewed Phone Case"),
    ],
)
def test_explain_renders_the_correct_sentence_per_signal_kind(kind, label, expected) -> None:
    signal = p.Signal(vector=[1.0], weight=1.0, kind=kind, label=label, product_id=None)
    assert p._explain(signal) == expected
