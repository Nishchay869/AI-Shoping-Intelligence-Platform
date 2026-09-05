"""Feature engineering: four complementary representations of the same review text.

1. TF-IDF (+ SVD)      - lexical signal: which exact words/n-grams appear, IDF-weighted. Cheap, interpretable,
                         and very good at catching the repeated boilerplate phrasing real fake-review farms
                         reuse across many listings. Reduced to a dense 100-dim block via TruncatedSVD (i.e.
                         LSA) so it concatenates cleanly with the dense embedding blocks below and doesn't let
                         thousands of sparse n-gram columns dominate feature importance during tree splits.
2. BERT embeddings      - contextual semantic signal from a raw pretrained encoder (bert-base-uncased),
                         attention-mask-weighted mean pooling over the last hidden layer. Captures meaning
                         and context (negation, word order) that bag-of-words cannot.
3. Sentence-Transformer  - a second, distinct semantic signal. Raw BERT embeddings are notoriously poor at
   embeddings             representing *sentence-level* similarity when used off-the-shelf (Reimers & Gurevych,
                         2019, "Sentence-BERT") because BERT was never trained to make embedding distance
                         mean anything. Sentence-Transformer models are fine-tuned specifically for that
                         (siamese/triplet objectives on NLI + STS data), so this block is genuinely
                         complementary to (2), not a duplicate of it.
4. Stylometric features - a handful of cheap, dependency-free structural signals from the fake-review-
                         detection literature: length, punctuation/caps intensity, lexical diversity - all
                         computed directly from the raw text, no model required.

All four blocks are concatenated into one dense matrix. Tree-based models (Random Forest, XGBoost) are
scale-invariant per feature, so no additional normalization is needed before training.

torch/transformers/sentence-transformers/sklearn are deliberately imported inside the functions/methods below,
not at module level: this module is pulled into the API server at startup (services/reviews.py ->
fake_review_detection -> here), and those imports alone are slow enough on a CPU-constrained deployment (e.g.
Render's free tier) to blow past the platform's port-binding timeout. `from __future__ import annotations`
lets the type hints below still reference those libraries' classes without forcing an eager import just to
resolve them.
"""
from __future__ import annotations
import re
import numpy as np

BERT_MODEL_NAME = "bert-base-uncased"          # swap for "distilbert-base-uncased" for a faster, smaller model
SBERT_MODEL_NAME = "all-MiniLM-L6-v2"
TFIDF_MAX_FEATURES = 5000
SVD_COMPONENTS = 100
MAX_TOKEN_LENGTH = 256
_WORD = re.compile(r"[A-Za-z']+")


def _device():
    import torch
    if torch.cuda.is_available(): return torch.device("cuda")
    if torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")


# ---- 1. TF-IDF + SVD --------------------------------------------------------

def fit_tfidf_svd(train_texts: list[str], n_components: int = SVD_COMPONENTS):
    """Fit the TF-IDF vectorizer and SVD reducer on TRAINING text only, to avoid leaking test vocabulary/variance."""
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(max_features=TFIDF_MAX_FEATURES, ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(train_texts)
    n_components = min(n_components, tfidf_matrix.shape[1] - 1, tfidf_matrix.shape[0] - 1)
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    svd.fit(tfidf_matrix)
    return vectorizer, svd


def transform_tfidf_svd(texts: list[str], vectorizer: "TfidfVectorizer", svd: "TruncatedSVD") -> np.ndarray:
    return svd.transform(vectorizer.transform(texts)).astype(np.float32)


# ---- 2. Raw BERT mean-pooled embeddings -------------------------------------

class BertEmbedder:
    """Loads bert-base-uncased once and mean-pools its last hidden layer, ignoring padding via the attention mask."""

    def __init__(self, model_name: str = BERT_MODEL_NAME):
        from transformers import AutoModel, AutoTokenizer
        self.device = _device()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device).eval()

    def embed(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        import torch
        with torch.no_grad():
            vectors = []
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]
                encoded = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=MAX_TOKEN_LENGTH).to(self.device)
                hidden = self.model(**encoded).last_hidden_state
                mask = encoded["attention_mask"].unsqueeze(-1).float()
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
                vectors.append(pooled.cpu().numpy())
            return np.concatenate(vectors, axis=0).astype(np.float32)


# ---- 3. Sentence-Transformer embeddings -------------------------------------

class SentenceEmbedder:
    """A model fine-tuned so that embedding distance reflects semantic similarity - distinct from raw BERT above."""

    def __init__(self, model_name: str = SBERT_MODEL_NAME):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name, device=str(_device()))

    def embed(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True).astype(np.float32)


# ---- 4. Stylometric features (no model required) ----------------------------

def stylometric_features(texts: list[str]) -> np.ndarray:
    """Cheap structural signals: exaggeration and repetition are two of the more consistent fake-review markers."""
    rows = []
    for text in texts:
        chars = len(text) or 1
        words = _WORD.findall(text)
        n_words = len(words) or 1
        unique_ratio = len(set(word.lower() for word in words)) / n_words
        exclamations = text.count("!")
        caps_words = sum(1 for word in words if len(word) > 1 and word.isupper())
        punctuation = sum(1 for ch in text if ch in "!?.,;:")
        avg_word_len = sum(len(word) for word in words) / n_words
        rows.append([
            len(words),                       # word count
            chars,                            # character count
            avg_word_len,                     # average word length
            unique_ratio,                     # lexical diversity - low = repetitive/templated
            exclamations / n_words,            # exclamation density - fake reviews over-punctuate
            caps_words / n_words,              # ALL-CAPS word density
            punctuation / chars,               # overall punctuation density
        ])
    return np.array(rows, dtype=np.float32)


def assemble_features(texts: list[str], tfidf_vectorizer: TfidfVectorizer, svd: TruncatedSVD, bert: BertEmbedder, sbert: SentenceEmbedder) -> np.ndarray:
    """Concatenate all four feature blocks into one dense matrix, in a fixed, documented column order."""
    return np.concatenate([
        transform_tfidf_svd(texts, tfidf_vectorizer, svd),
        bert.embed(texts),
        sbert.embed(texts),
        stylometric_features(texts),
    ], axis=1)
