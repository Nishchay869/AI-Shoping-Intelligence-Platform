"""Unit tests for the fake-review-detection inference path: real joblib artifact (committed to the repo),
BERT/SBERT mocked with fixed-shape dummy embedders so assemble_features' real concatenation logic and the
real classifiers' predict_proba run without needing network-downloaded pretrained weights."""
import numpy as np
import pytest
from unittest.mock import patch
from app.infrastructure import fake_review_detection as frd


class _DummyEmbedder:
    def __init__(self, dim): self.dim = dim
    def embed(self, texts, batch_size=None): return np.zeros((len(texts), self.dim), dtype=np.float32)


@pytest.fixture(autouse=True)
def _reset_singletons():
    frd._artifact = frd._bert = frd._sbert = None
    yield
    frd._artifact = frd._bert = frd._sbert = None


def test_score_texts_returns_a_probability_per_text() -> None:
    with patch("app.infrastructure.fake_review_detection.BertEmbedder", return_value=_DummyEmbedder(768)), \
         patch("app.infrastructure.fake_review_detection.SentenceEmbedder", return_value=_DummyEmbedder(384)):
        scores = frd.score_texts(["Great product, works well.", "BUY NOW BEST EVER!!!"])
    assert len(scores) == 2
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_score_texts_empty_list_returns_empty_list_without_loading_anything() -> None:
    assert frd.score_texts([]) == []
    assert frd._artifact is None


def test_artifact_is_loaded_once_and_cached() -> None:
    with patch("app.infrastructure.fake_review_detection.BertEmbedder", return_value=_DummyEmbedder(768)), \
         patch("app.infrastructure.fake_review_detection.SentenceEmbedder", return_value=_DummyEmbedder(384)), \
         patch("app.infrastructure.fake_review_detection.joblib.load", wraps=frd.joblib.load) as load_spy:
        frd.score_texts(["one"])
        frd.score_texts(["two"])
    assert load_spy.call_count == 1
