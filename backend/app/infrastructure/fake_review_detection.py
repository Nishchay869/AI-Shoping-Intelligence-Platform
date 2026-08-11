"""Fake-review trust scoring: the pretrained ensemble from ml/fake_review_detection, wired into the live API.

Loads three things once per process, lazily, as module-level singletons (mirrors clip_embeddings.py's
_load()/global pattern for the same reason - these are heavy pretrained artifacts, not something to touch
at import time):
  1. fake_review_model.joblib - fitted TfidfVectorizer + TruncatedSVD + RandomForestClassifier + XGBClassifier
     (ml/fake_review_detection/train.py; trained on ml/fake_review_detection/dataset.py's synthetic corpus).
  2. BertEmbedder (bert-base-uncased) and SentenceEmbedder (all-MiniLM-L6-v2) from ml/fake_review_detection/
     features.py - the same two pretrained encoders assemble_features() was built around.

IMPORTANT - OMP_NUM_THREADS: this process already imports torch/transformers unconditionally at startup for
CLIP image search (app/infrastructure/clip_embeddings.py, pulled in by the products router). Verified
directly (not just suspected): calling joblib.load() on this artifact in a process where torch has already
been imported segfaults (SIGSEGV, exit 139) - a PyTorch-vs-scikit-learn/XGBoost OpenMP runtime double-init
conflict. A Python try/except cannot catch a native segfault, so this must be prevented, not handled.
Setting OMP_NUM_THREADS=1 before joblib.load() runs eliminates it (verified: works even set this late, after
torch is already resident). Set here, not only in the Dockerfile, so every entrypoint that imports this
module - the API server, scripts/backfill_review_trust_scores.py, and tests - is protected regardless of
import order.
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path
import joblib
from ml.fake_review_detection.features import BertEmbedder, SentenceEmbedder, assemble_features

ARTIFACT_PATH = Path(__file__).resolve().parent.parent.parent / "ml" / "fake_review_detection" / "artifacts" / "fake_review_model.joblib"

_artifact: dict | None = None
_bert: BertEmbedder | None = None
_sbert: SentenceEmbedder | None = None


def _load() -> tuple[dict, BertEmbedder, SentenceEmbedder]:
    global _artifact, _bert, _sbert
    if _artifact is None:
        _artifact = joblib.load(ARTIFACT_PATH)
    if _bert is None:
        _bert = BertEmbedder()
    if _sbert is None:
        _sbert = SentenceEmbedder()
    return _artifact, _bert, _sbert


def score_texts(texts: list[str]) -> list[float]:
    """Fake-probability (0 = genuine-looking, 1 = fake-looking) per text, batched through the same
    TF-IDF+SVD/BERT/Sentence-Transformer/stylometric feature pipeline the artifact was trained on, and
    averaged across the persisted RandomForest + XGBoost predict_proba - a simple two-model ensemble
    average, since both were trained on the identical feature matrix and labels."""
    if not texts:
        return []
    artifact, bert, sbert = _load()
    features = assemble_features(texts, artifact["tfidf_vectorizer"], artifact["svd"], bert, sbert)
    rf_proba = artifact["random_forest"].predict_proba(features)[:, 1]
    xgb_proba = artifact["xgboost"].predict_proba(features)[:, 1]
    return ((rf_proba + xgb_proba) / 2).tolist()
