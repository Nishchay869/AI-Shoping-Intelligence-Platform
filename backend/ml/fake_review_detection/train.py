"""Train and evaluate Random Forest and XGBoost fake-review classifiers.

Pipeline: load labeled reviews -> stratified train/test split -> fit TF-IDF+SVD on the training split only
-> encode all four feature blocks (TF-IDF/SVD, BERT, Sentence-Transformer, stylometric) for train and test
-> train Random Forest and XGBoost on the combined feature matrix -> evaluate both on the held-out test set.

Usage (from backend/, with `pip install -r ml/requirements.txt` in the venv):
    python -m ml.fake_review_detection.train                       # synthetic demo dataset, 1200 samples
    python -m ml.fake_review_detection.train --n-samples 4000       # larger synthetic run
    python -m ml.fake_review_detection.train --csv path/to/real.csv # real labeled data (columns: text,label)
"""
import argparse
import time
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from ml.fake_review_detection.dataset import generate_synthetic_dataset, load_labeled_csv
from ml.fake_review_detection.evaluate import evaluate
from ml.fake_review_detection.features import BERT_MODEL_NAME, SBERT_MODEL_NAME, BertEmbedder, SentenceEmbedder, assemble_features, fit_tfidf_svd

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


def train_and_evaluate(csv_path: str | None = None, n_samples: int = 1200, test_size: float = 0.2, seed: int = 42, save_artifacts: bool = True) -> dict:
    print("Loading data...")
    frame = load_labeled_csv(csv_path) if csv_path else generate_synthetic_dataset(n_samples=n_samples, seed=seed)
    print(f"  {len(frame)} reviews total - {frame['label'].mean():.1%} labeled fake")

    # Stratified split preserves the fake/genuine ratio in both splits - important since the classes aren't 50/50.
    train_frame, test_frame = train_test_split(frame, test_size=test_size, stratify=frame["label"], random_state=seed)
    train_texts, test_texts = train_frame["text"].tolist(), test_frame["text"].tolist()
    y_train, y_test = train_frame["label"].to_numpy(), test_frame["label"].to_numpy()
    print(f"  train: {len(train_texts)}  test: {len(test_texts)}")

    # Fit only on the training split - fitting TF-IDF/SVD on the full dataset would leak test-set vocabulary
    # and variance into the model selection, inflating the reported metrics.
    print("Fitting TF-IDF + SVD on the training split only...")
    tfidf_vectorizer, svd = fit_tfidf_svd(train_texts)

    print(f"Loading BERT ({BERT_MODEL_NAME}) and Sentence-Transformer ({SBERT_MODEL_NAME})...")
    bert = BertEmbedder()
    sbert = SentenceEmbedder()

    print("Encoding training features (TF-IDF/SVD + BERT + Sentence-Transformer + stylometric)...")
    t0 = time.time()
    X_train = assemble_features(train_texts, tfidf_vectorizer, svd, bert, sbert)
    print(f"  train feature matrix: {X_train.shape} ({time.time() - t0:.1f}s)")

    print("Encoding test features...")
    t0 = time.time()
    X_test = assemble_features(test_texts, tfidf_vectorizer, svd, bert, sbert)
    print(f"  test feature matrix: {X_test.shape} ({time.time() - t0:.1f}s)")

    print("Training Random Forest...")
    random_forest = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced", n_jobs=-1, random_state=seed)
    random_forest.fit(X_train, y_train)

    print("Training XGBoost...")
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)  # counteract class imbalance directly in the loss
    xgboost_model = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.9, colsample_bytree=0.9, scale_pos_weight=scale_pos_weight, eval_metric="logloss", random_state=seed, n_jobs=-1)
    xgboost_model.fit(X_train, y_train)

    results = {}
    for name, model in [("Random Forest", random_forest), ("XGBoost", xgboost_model)]:
        metrics = evaluate(name, y_test, model.predict(X_test))
        print("\n" + metrics.report())
        results[name] = metrics

    if save_artifacts:
        ARTIFACT_DIR.mkdir(exist_ok=True)
        artifact_path = ARTIFACT_DIR / "fake_review_model.joblib"
        joblib.dump({"tfidf_vectorizer": tfidf_vectorizer, "svd": svd, "random_forest": random_forest, "xgboost": xgboost_model}, artifact_path)
        print(f"\nSaved trained artifacts to {artifact_path}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=None, help="Path to a labeled CSV with text,label columns. Omit to use the synthetic demo dataset.")
    parser.add_argument("--n-samples", type=int, default=1200, help="Synthetic dataset size (ignored if --csv is given).")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    train_and_evaluate(csv_path=args.csv, n_samples=args.n_samples, test_size=args.test_size, seed=args.seed)
