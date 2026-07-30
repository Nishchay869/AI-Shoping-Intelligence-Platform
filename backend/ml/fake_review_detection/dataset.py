"""Labeled dataset for fake-review detection.

There is no licensed, pre-labeled fake-review dataset bundled here, so this module ships a synthetic
generator that makes the whole pipeline runnable end-to-end. It's a probabilistic *mixture* model, not a
hard fake/genuine template switch: every review is built by sampling a handful of sentences from one shared
pool, where each sentence carries a "style weight" from -1 (nuanced, specific, genuine-leaning) to +1
(hyperbolic, generic, fake-leaning). A review's true label only shifts the sampling *probabilities* toward
one end of that pool - it doesn't determine the content deterministically. That's what makes the classes
genuinely overlap (a fake review can, by chance, read as measured; a genuine review can gush) rather than
being trivially separable by a couple of fixed phrases, which is closer to how real deceptive-review
detection behaves (Ott, Cardie & Hancock, 2011/2013, the academic benchmark this is loosely modeled on:
fake reviews *trend* toward more superlatives, more generic/first-person narrative, less concrete spatial
detail - a statistical tendency, not a hard rule).

For production, replace `generate_synthetic_dataset()` with `load_labeled_csv()` pointed at real labeled
data, e.g. the Deceptive Opinion Spam Corpus, or this platform's own `reviews` table hand-labeled via a
moderation queue or cross-referenced against verified-purchase status and abuse reports.
"""
import random
import numpy as np
import pandas as pd

FEATURES = ["battery", "stitching", "screen", "sound quality", "zipper", "strap", "packaging", "instructions", "charging port", "build quality", "fit", "material", "hinge", "cushioning"]
DURATIONS = ["a week", "a couple of weeks", "a month", "three months", "about six months"]

# (sentence template, style_weight): negative = genuine-leaning (specific, measured, mixed opinion),
# positive = fake-leaning (generic, hyperbolic, exclamation-heavy), near zero = shared/neutral filler
# that both genuine and fake reviewers plausibly write.
SENTENCE_POOL: list[tuple[str, float]] = [
    ("After using this for about {duration}, the {feature} has held up better than I expected.", -0.9),
    ("The {feature} started acting up after a few weeks, which was disappointing.", -0.7),
    ("I like that the {feature} feels sturdy, though it took some getting used to.", -0.75),
    ("Shipping took a few extra days but the item arrived undamaged.", -0.6),
    ("The {feature} is a clear step up from the budget version I had before.", -0.65),
    ("I noticed the {feature} isn't quite as advertised in the listing.", -0.55),
    ("The {feature} feels a bit cheap for the price, honestly.", -0.6),
    ("Overall I'm satisfied, though I'll see how it holds up long term.", -0.4),
    ("Not perfect, but it does the job for the price I paid.", -0.35),
    ("It's decent for everyday use.", -0.15),
    ("Works as described, nothing more, nothing less.", -0.05),
    ("Would consider buying from this brand again.", -0.1),
    ("Does what it's supposed to do so far.", 0.0),
    ("Pretty happy with this purchase overall.", 0.2),
    ("Really good value for what you pay.", 0.25),
    ("I'd recommend this to a friend.", 0.2),
    ("Everything about it is just perfect and I love it so much.", 0.7),
    ("Highly highly recommend to everyone, you will not regret it!", 0.75),
    ("This is hands down the BEST product I have EVER purchased!!!", 0.95),
    ("WOW just WOW, this exceeded every single expectation!!!", 0.9),
    ("Absolutely life changing, I can't believe how amazing this is!", 0.85),
    ("5 stars is not enough, this deserves 10 stars easily!!!", 0.95),
    ("I was skeptical at first but now I am a total believer!!", 0.7),
    ("This company clearly cares about quality and it shows.", 0.45),
    ("I tell all my friends and family to buy this immediately.", 0.65),
    ("Trust me on this one, best decision ever!!!", 0.8),
    ("Buy it now before the price goes up, you won't be disappointed!!!", 0.8),
    ("DO NOT BUY THIS, complete waste of money, TERRIBLE!!!", 0.85),
    ("Worst purchase of my life, stay far far away from this scam!!!", 0.85),
    ("This company is a joke, total garbage product, avoid at all costs!!!", 0.8),
]


def _fill(template: str, rng: random.Random) -> str:
    return template.format(duration=rng.choice(DURATIONS), feature=rng.choice(FEATURES))


def _sample_review(rng: random.Random, np_rng: np.random.Generator, label: int, temperature: float) -> tuple[str, int]:
    """Sample 2-4 sentences from the shared pool, biased (not forced) toward the label's end of the style spectrum."""
    bias = 0.8 if label == 1 else -0.8
    weights = np.array([weight for _, weight in SENTENCE_POOL])
    logits = (bias * weights) / temperature
    probs = np.exp(logits - logits.max())
    probs /= probs.sum()
    n_sentences = int(np_rng.integers(2, 5))
    indices = np_rng.choice(len(SENTENCE_POOL), size=n_sentences, replace=False, p=probs)
    chosen = [SENTENCE_POOL[i] for i in indices]
    rng.shuffle(chosen)
    text = " ".join(_fill(template, rng) for template, _ in chosen)
    avg_style = sum(weight for _, weight in chosen) / len(chosen)
    rating = int(np.clip(round(3 + avg_style * 2 + np_rng.normal(0, 0.8)), 1, 5))
    return text, rating


def generate_synthetic_dataset(n_samples: int = 1200, fake_ratio: float = 0.4, seed: int = 42, temperature: float = 1.0) -> pd.DataFrame:
    """Build a labeled DataFrame with columns [text, rating, label] (label: 1 = fake, 0 = genuine).

    `temperature` controls how much the two classes overlap: higher = noisier/harder to separate, lower =
    closer to a deterministic template switch. 1.0 is tuned (see module docstring) to keep this a real,
    non-trivial classification problem instead of one a model can solve perfectly by matching fixed phrases.
    """
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    labels = [1] * int(n_samples * fake_ratio) + [0] * (n_samples - int(n_samples * fake_ratio))
    rng.shuffle(labels)
    rows = [(*_sample_review(rng, np_rng, label, temperature), label) for label in labels]
    return pd.DataFrame(rows, columns=["text", "rating", "label"])


def load_labeled_csv(path: str) -> pd.DataFrame:
    """Load real labeled data for production use. Expected columns: text (str), label (0=genuine, 1=fake)."""
    frame = pd.read_csv(path)
    missing = {"text", "label"} - set(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")
    return frame
