"""Text similarity with two interchangeable backends. Owner: Phuong Nhi.

    similarity(queries, documents, method="tfidf")  ->  matrix [len(queries), len(documents)]

"tfidf"  the baseline: word and word-pair TF-IDF, cosine. Sees only shared words.
"embed"  the final method: sentence embeddings (all-MiniLM-L6-v2, the model normalise.py
         uses), cosine. Sees meaning, so "neural networks" is close to "deep learning".

Matching (match.py) and subject recommendation (recommend.py) both call this module, so the
two methods are compared on the same code path.
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
METHODS = ("tfidf", "embed")
# Keeps c++, c# and single letters; scikit-learn's default pattern drops them.
TOKEN = r"[a-z0-9]+[+#]*"


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def embeddings_available() -> bool:
    """False on a machine without the model (or with SKILLABUS_NO_EMBED set): use tfidf there.

    Checked once per session, so a missing model costs one failed load, not one per call.
    """
    if os.getenv("SKILLABUS_NO_EMBED"):
        return False
    try:
        _embedder()
        return True
    except Exception:
        return False


def best_method() -> str:
    return "embed" if embeddings_available() else "tfidf"


_vectors: dict[str, np.ndarray] = {}


def embed(texts: list[str]) -> np.ndarray:
    """One unit-length vector per text. Cached, so the subject rows are encoded once per session."""
    new = [t for t in dict.fromkeys(texts) if t not in _vectors]
    if new:
        encoded = _embedder().encode(new, batch_size=64, normalize_embeddings=True, show_progress_bar=False)
        _vectors.update(zip(new, np.asarray(encoded, dtype="float32")))
    return np.vstack([_vectors[t] for t in texts])


def embed_documents(documents: list[list[str]]) -> np.ndarray:
    """One vector per document, the mean of its sentence vectors.

    The model reads at most 256 word pieces, so a whole ad or resume would be cut off;
    averaging sentence vectors uses all of it.
    """
    flat = [s for sentences in documents for s in sentences]
    vectors = embed(flat) if flat else np.zeros((0, 1), dtype="float32")
    out, i = [], 0
    for sentences in documents:
        if not sentences:
            out.append(np.zeros(vectors.shape[1], dtype="float32"))
            continue
        mean = vectors[i:i + len(sentences)].mean(axis=0)
        out.append(mean / (np.linalg.norm(mean) or 1.0))
        i += len(sentences)
    return np.vstack(out)


def tfidf_similarity(queries: list[str], documents: list[str]) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectoriser = TfidfVectorizer(lowercase=True, token_pattern=TOKEN, ngram_range=(1, 2),
                                 sublinear_tf=True, stop_words="english")
    try:
        doc_matrix = vectoriser.fit_transform(documents)
    except ValueError:  # every document is empty or only stop words
        return np.zeros((len(queries), len(documents)))
    return (vectoriser.transform(queries) @ doc_matrix.T).toarray()


def similarity(queries: list[str], documents: list[str], method: str = "tfidf") -> np.ndarray:
    """Cosine similarity of every query to every document, in [0, 1] for tfidf and [-1, 1] for embed."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if not queries or not documents:
        return np.zeros((len(queries), len(documents)))
    if method == "embed":
        return embed(list(queries)) @ embed(list(documents)).T
    return tfidf_similarity(list(queries), list(documents))
