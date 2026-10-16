"""Retrieval for the chat: find the subject text that answers a question. Owner: Van Thong.

Two backends with the same output:

  embed   sentence-transformers all-MiniLM-L6-v2 (the model normalise() already loads) and a
          FAISS inner-product index over unit vectors: the "FAISS RAG" on the poster. Used when
          both libraries are installed.
  tfidf   word and bigram TF-IDF with cosine similarity, scikit-learn only. It is the keyword
          baseline the evaluation compares against, and it is what the deployed app runs:
          app/requirements.txt leaves PyTorch out so Streamlit Cloud installs in a minute.

retrieve(question, k) returns up to k passages, best first:

    {"text", "score", "source", "url", "subject_code", "subject_name", "layer", "method"}

The first four are the keys app/chat.py already reads; `source` is formatted the way its
TF-IDF fallback formats it ("36118 Applied Natural Language Processing (topic)").

Corpus. data/1_knowledge/uts/subject_profiles.csv: one row per learning objective, weekly topic or
description sentence. With sources=("subjects", "ads") it also searches sentences from the
cleaned Seek ads that name a dictionary skill, for "what do employers say about X" questions;
that is off by default because the chat answers from the Handbook.

Index. data/runtime/ is gitignored, so the embedding index is built on first use and the
vectors cached in data/runtime/cache/rag/ (rebuilt automatically when the corpus changes).
`python -m skillabus.rag build` builds it ahead of time.

Four things on top of plain similarity search:
  * a skill named by an alias is written out in full in the question ("LLMs" -> "Large
    language models"), because the embedding model does not know the acronyms;
  * a subject code in the question ("what does 36118 teach?") restricts results to that
    subject, because neither backend matches five-digit codes reliably;
  * each passage is indexed with its subject's name and layer, so "deep learning subject"
    finds 94691 Deep Learning even where the sentence itself only says "neural networks";
  * passages below a minimum score are dropped, so an off-topic question returns nothing
    and the chat says it does not know, instead of quoting the least-bad sentence.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
from functools import lru_cache

import numpy as np
import pandas as pd

from . import paths

PROFILES_CSV = paths.SUBJECT_PROFILES
SEEK_CSV = paths.SEEK_ADS
CACHE_DIR = paths.RAG_INDEX

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"     # same as normalise.py
MIN_SCORE = {"embed": 0.30, "tfidf": 0.05}
LAYER_NAME = {"learning_objective": "learning objective", "assessment": "assessment",
              "weekly_topic": "topic", "description": "description", "ad": "ad"}
SUBJECT_CODE = re.compile(r"(?<!\d)(\d{5})(?!\d)")
# Words every question and many passages share without saying what they are about. Left in,
# "Which subject teaches deep learning?" matches every sentence containing "subject", and an
# off-topic "best pizza recipe" matches "Ethical best practices in NLP". "learning" stays: it
# carries "machine learning" and "deep learning".
DOMAIN_STOP_WORDS = ["subject", "subjects", "course", "courses", "unit", "units", "uts",
                     "teach", "teaches", "teaching", "taught", "learn", "student", "students",
                     "best", "good", "help", "know", "want", "need", "cover", "covers", "covered"]
SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+|\s*•\s*")


# ------------------------------------------------------------------------------- corpus
@lru_cache(maxsize=1)
def _skill_pattern() -> re.Pattern:
    """Any alias the extractor looks for (the vocabulary's detection rows, extract.load_dictionary()),
    as one pattern: case-insensitive, except the strict rows (R, SAS), which match as written. As in
    extract(), only aliases count: a canonical such as "Go" or "Oracle" is a display name."""
    from .extract import load_dictionary
    loose, strict = set(), set()
    for s in load_dictionary():
        (strict if s["strict"] else loose).update(s["aliases"])

    def alt(words):
        return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))

    parts = [p for p in (f"(?i:{alt(loose)})" if loose else "", alt(strict)) if p]
    return re.compile(rf"(?<![A-Za-z0-9+#_])(?:{'|'.join(parts)})(?![A-Za-z0-9+#_])")


@lru_cache(maxsize=1)
def _skill_names() -> dict[str, str]:
    """Lower-cased alias -> the skill's display name ("llms" -> "Large language models")."""
    from .extract import load_dictionary
    names: dict[str, str] = {}
    for s in load_dictionary():
        for a in s["aliases"]:
            names.setdefault(a.lower(), s["canonical"])
    return names


def spell_out(question: str) -> str:
    """The question with each skill it names by an alias written out in full ("LLMs" -> "Large
    language models"). all-MiniLM reads "LLMs" as "LMS" and ranks a "Timed LMS exam" first; an alias
    left next to the full name still pulls that exam into the top five, so it is replaced."""
    def full(m: re.Match) -> str:
        name = _skill_names().get(m.group(0).lower())
        return name if name and name.lower() != m.group(0).lower() else m.group(0)
    return _skill_pattern().sub(full, question)


def _subject_passages() -> pd.DataFrame:
    if not PROFILES_CSV.exists():
        raise FileNotFoundError(f"{PROFILES_CSV} not found; build it with "
                                "data-eda/src/build_subject_profiles.py")
    p = pd.read_csv(PROFILES_CSV, dtype=str).fillna("")
    layer = p.layer.map(LAYER_NAME).fillna(p.layer)
    return pd.DataFrame({
        "text": p.text,
        "doc": p.subject_code + " " + p.subject_name + " (" + layer + "): " + p.text,
        "source": p.subject_code + " " + p.subject_name + " (" + layer + ")",
        "url": p.source_url,
        "subject_code": p.subject_code,
        "subject_name": p.subject_name,
        "layer": p.layer,
    })


def _ad_passages() -> pd.DataFrame:
    """Sentences from the unique Seek ads that name at least one skill the extractor knows."""
    ads = pd.read_csv(SEEK_CSV, dtype=str).fillna("").drop_duplicates("description")
    skill = _skill_pattern()
    rows = []
    for ad in ads.itertuples(index=False):
        year = ad.listingDate[:4]
        who = ad.company or ad.advertiser
        for sent in SENTENCE.split(ad.description):
            sent = sent.strip(" -")
            if 30 <= len(sent) <= 400 and skill.search(sent):
                src = f"Seek ad: {ad.title}, {who}, {year}"
                rows.append((sent, f"{ad.title}: {sent}", src, "", "", "", "ad"))
    out = pd.DataFrame(rows, columns=["text", "doc", "source", "url", "subject_code", "subject_name", "layer"])
    return out.drop_duplicates("text").reset_index(drop=True)


@lru_cache(maxsize=4)
def passages(sources: tuple[str, ...] = ("subjects",)) -> pd.DataFrame:
    """Everything retrieve() can return, for the given sources."""
    parts = []
    if "subjects" in sources:
        parts.append(_subject_passages())
    if "ads" in sources:
        parts.append(_ad_passages())
    if not parts:
        raise ValueError(f"unknown sources {sources}; use 'subjects' and/or 'ads'")
    return pd.concat(parts, ignore_index=True)


# ------------------------------------------------------------------------------- backends
def embeddings_available() -> bool:
    """True if sentence-transformers and faiss are installed. Checks without importing them:
    importing sentence-transformers pulls in PyTorch, which took 80 seconds on a test laptop,
    and the chat calls this before its first answer."""
    from importlib.util import find_spec
    return find_spec("sentence_transformers") is not None and find_spec("faiss") is not None


def default_method() -> str:
    forced = os.getenv("SKILLABUS_RAG_METHOD")
    if forced in ("embed", "tfidf"):
        return forced
    return "embed" if embeddings_available() else "tfidf"


@lru_cache(maxsize=4)
def _tfidf(sources: tuple[str, ...]):
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
    docs = passages(sources).doc.tolist()
    stop = sorted(ENGLISH_STOP_WORDS | set(DOMAIN_STOP_WORDS))
    vec = TfidfVectorizer(stop_words=stop, ngram_range=(1, 2), sublinear_tf=True)
    return vec, vec.fit_transform(docs)


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=4)
def _faiss(sources: tuple[str, ...]):
    """FAISS index over the passages; vectors cached on disk, keyed by corpus content."""
    import faiss
    docs = passages(sources).doc.tolist()
    key = hashlib.sha1(("\n".join(docs) + EMBED_MODEL).encode("utf-8")).hexdigest()[:12]
    path = CACHE_DIR / f"{'-'.join(sources)}-{key}.npy"
    if path.exists():
        vecs = np.load(path)
    else:
        vecs = _model().encode(docs, batch_size=64, normalize_embeddings=True,
                               show_progress_bar=False).astype("float32")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.save(path, vecs)
    index = faiss.IndexFlatIP(vecs.shape[1])     # inner product on unit vectors = cosine
    index.add(vecs)
    return index


def _scores(question: str, method: str, sources: tuple[str, ...]) -> np.ndarray:
    """Similarity of the question to every passage, in passage order."""
    if method == "tfidf":
        from sklearn.metrics.pairwise import cosine_similarity
        vec, mat = _tfidf(sources)
        return cosine_similarity(vec.transform([question]), mat).ravel()
    if method == "embed":
        index = _faiss(sources)
        q = _model().encode([question], normalize_embeddings=True).astype("float32")
        sims, ids = index.search(q, index.ntotal)   # exact search; the corpus is small
        out = np.zeros(index.ntotal, dtype="float32")
        out[ids[0]] = sims[0]
        return out
    raise ValueError(f"unknown method {method!r}; use 'embed' or 'tfidf'")


# ------------------------------------------------------------------------------- public
def retrieve(question: str, k: int = 5, method: str | None = None,
             sources: tuple[str, ...] = ("subjects",)) -> list[dict]:
    """Return up to k passages that answer the question, best first (see module docstring)."""
    question = (question or "").strip()
    if not question or k <= 0:
        return []
    method = method or default_method()
    corpus = passages(tuple(sources))
    scores = _scores(spell_out(question), method, tuple(sources))

    codes = set(SUBJECT_CODE.findall(question)) & set(corpus.subject_code)
    if codes:
        scores = np.where(corpus.subject_code.isin(codes), scores, -1.0)

    out, seen = [], set()
    for i in np.argsort(-scores):
        if scores[i] < MIN_SCORE[method] and not (codes and scores[i] > -1.0):
            break
        if scores[i] <= -1.0:
            break
        row = corpus.iloc[i]
        dedupe = (row.subject_code, row.text)
        if dedupe in seen:
            continue
        seen.add(dedupe)
        out.append({"text": row.text, "score": round(float(scores[i]), 4), "source": row.source,
                    "url": row.url or None, "subject_code": row.subject_code or None,
                    "subject_name": row.subject_name or None, "layer": row.layer, "method": method})
        if len(out) == k:
            break
    return out


def build(sources: tuple[str, ...] = ("subjects",), method: str | None = None) -> str:
    """Build (and cache) the index ahead of time; returns a one-line summary."""
    method = method or default_method()
    n = len(passages(sources))
    if method == "embed":
        _faiss(sources)
    else:
        _tfidf(sources)
    return f"{method} index over {n:,} passages from {', '.join(sources)}"


# Hand-picked questions whose right subject is not in doubt. A smoke test, not the
# evaluation: the 30 reference questions in data/4_evaluation/labels/chat_questions.csv are for that.
SANITY = [
    ("Which subject teaches deep learning?", {"94691"}),
    ("Where can I learn natural language processing?", {"36118"}),
    ("What does 36118 teach about large language models?", {"36118"}),
    ("Which subject covers machine learning algorithms?", {"36106", "36120"}),
    ("Is there a subject on data visualisation and storytelling?", {"36104", "32146"}),
    ("Where do I learn big data engineering?", {"94693"}),
    ("Which subject teaches statistical thinking for data science?", {"36103"}),
    ("Is there a subject about cloud computing?", {"42904", "41001", "69508"}),
]


def sanity_check(method: str, k: int = 5) -> pd.DataFrame:
    rows = []
    for q, want in SANITY:
        got = [r["subject_code"] for r in retrieve(q, k=k, method=method)]
        rows.append({"question": q, "expected": "/".join(sorted(want)),
                     "rank": next((i + 1 for i, c in enumerate(got) if c in want), None),
                     "top": got[0] if got else None})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or query the chat retrieval index.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="build and cache the index")
    b.add_argument("--sources", nargs="+", default=["subjects"], choices=["subjects", "ads"])
    b.add_argument("--method", choices=["embed", "tfidf"])
    a = sub.add_parser("ask", help="retrieve passages for one question")
    a.add_argument("question")
    a.add_argument("-k", type=int, default=5)
    a.add_argument("--method", choices=["embed", "tfidf"])
    a.add_argument("--sources", nargs="+", default=["subjects"], choices=["subjects", "ads"])
    sub.add_parser("check", help="run the sanity questions with every available backend")
    args = parser.parse_args()

    if args.cmd == "build":
        print(build(tuple(args.sources), args.method))
    elif args.cmd == "ask":
        for r in retrieve(args.question, args.k, args.method, tuple(args.sources)):
            print(f"{r['score']:.3f}  [{r['source']}]  {r['text'][:110]}")
    else:
        methods = ["tfidf"] + (["embed"] if embeddings_available() else [])
        for m in methods:
            t = sanity_check(m)
            hit1, hit5 = (t["rank"] == 1).sum(), t["rank"].notna().sum()
            print(f"\n{m}: right subject first in {hit1}/{len(t)}, in top 5 in {hit5}/{len(t)}")
            print(t.to_string(index=False))


if __name__ == "__main__":
    main()
