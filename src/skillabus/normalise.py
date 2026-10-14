"""Map raw skill mentions to ESCO, then Lightcast, else tag as emerging. Owner: Quan.

For each mention, in order (first hit wins):
1. dictionary   our alias list (skills_seed_v2.csv) -> canonical name, ESCO link if Van Thong made one
2. esco_exact   the phrase (or its canonical name) equals an ESCO preferred or alternative label
3. esco_embed   nearest ESCO preferred label by sentence embedding, if cosine >= ESCO_MIN_SIM
   (a dictionary skill still unmatched here keeps vocab "seed", id seed:<slug>)
4. lightcast    Lightcast Open Skills search (needs LIGHTCAST_CLIENT_ID / _SECRET)
5. emerging     none of the above: kept, flagged, never dropped

Skills we already know ESCO lacks (generative AI, LLMs: no ESCO concept, checked 25 Sep) skip
steps 2-3, so the embedding cannot force them onto a loosely related concept.
Adds to each mention: skill_id, skill_label, vocab (data contract section 1) plus
canonical (dictionary name, for demand lookups), how (which step) and similarity.
"""

from __future__ import annotations

import difflib
import importlib.util
import json
import os
import pickle
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .text import read_csv_skipping_notes, slug

ROOT = Path(__file__).resolve().parents[2]
SEED_CSV = ROOT / "data/processed/skills_seed_v2.csv"
ESCO_LINKS_CSV = ROOT / "data/processed/skill_to_esco.csv"
# Van Thong's cleaned ESCO file is in git (data-eda/, PR #44); the raw download is only on his machine.
ESCO_CLEAN_CSV = ROOT / "data-eda/data/clean/esco_skills_clean.csv"
ESCO_SKILLS_CSV = ROOT / "data/raw/data-eda/data/raw/taxonomy_esco_v1.2.1/skills_en.csv"
INDEX_DIR = ROOT / "models" / "esco"
LIGHTCAST_CACHE = ROOT / "data" / "cache" / "lightcast"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ESCO_MIN_SIM = float(os.getenv("SKILLABUS_ESCO_MIN_SIM", "0.82"))  # tune on the labelled ads
NOT_IN_ESCO = {"Generative AI", "Large language models"}
# ESCO concepts that share a name with a data skill but mean something else. Checked by hand:
# "SPARK" is a Java web micro-framework, not Apache Spark (ESCO has no Apache Spark concept).
BLOCKED_ESCO = {"http://data.europa.eu/esco/skill/af7ae54f-4649-4c16-87c7-59ba41d4d57f"}


def key(s: str) -> str:
    """Comparison key: lower case, no brackets or punctuation, single spaces."""
    s = re.sub(r"\(.*?\)", " ", s.lower())
    return re.sub(r"[^a-z0-9+#]+", " ", s).strip()


# Filler around a skill name in ads and resumes: "problem-solving skills", "strong SQL",
# "hypothesis testing basics", "knowledge of statistics".
_FILLER = re.compile(r"^(?:strong|solid|good|basic|advanced|knowledge of|experience (?:with|in))\s+|"
                     r"\s+(?:skills?|basics|experience|knowledge|techniques?|capabilit(?:y|ies)|applications?)$")


def keys(s: str) -> list[str]:
    """The comparison key, then the key without filler words; used to look a mention up."""
    k = key(s)
    stripped = _FILLER.sub("", k).strip()
    return [k, stripped] if stripped and stripped != k else [k]


def lookup(table: dict, s: str):
    return next((table[k] for k in keys(s) if k in table), None)


# ---------------------------------------------------------------- 1. dictionary
@lru_cache(maxsize=1)
def _dictionary() -> tuple[dict, dict]:
    seed = read_csv_skipping_notes(SEED_CSV, dtype=str)
    alias_to_canon = {}
    for _, r in seed.iterrows():
        for a in [r.canonical] + [a for a in str(r.aliases).split("|") if a and a != "nan"]:
            alias_to_canon.setdefault(key(a), r.canonical)
    links = {}
    if ESCO_LINKS_CSV.exists():
        e = pd.read_csv(ESCO_LINKS_CSV, dtype=str).dropna(subset=["esco_uri"])
        links = {r.canonical: (r.esco_uri, r.esco_preferred_label) for _, r in e.iterrows()}
    return alias_to_canon, links


# ---------------------------------------------------------------- 2-3. ESCO
@lru_cache(maxsize=1)
def _esco_labels() -> tuple[dict, list[tuple[str, str]]]:
    """(label key -> (uri, preferred label), [(uri, preferred label)]). Empty if no ESCO file is present.

    Reads the clean file (alt labels joined by "|"), else the raw download (joined by newlines).
    """
    cache = INDEX_DIR / "labels.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    if ESCO_CLEAN_CSV.exists():
        e = pd.read_csv(ESCO_CLEAN_CSV, usecols=["concept_uri", "preferred_label", "alt_labels"], dtype=str)
        sep = "|"
    elif ESCO_SKILLS_CSV.exists():
        e = pd.read_csv(ESCO_SKILLS_CSV, usecols=["conceptUri", "preferredLabel", "altLabels"], dtype=str)
        e.columns = ["concept_uri", "preferred_label", "alt_labels"]
        sep = "\n"
    else:
        return {}, []
    exact, pref = {}, []
    for _, r in e.iterrows():
        pref.append((r.concept_uri, r.preferred_label))
        exact.setdefault(key(r.preferred_label), (r.concept_uri, r.preferred_label))
        for alt in str(r.alt_labels).split(sep) if isinstance(r.alt_labels, str) else []:
            exact.setdefault(key(alt), (r.concept_uri, r.preferred_label))
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps((exact, pref)))
    return exact, pref


@lru_cache(maxsize=1)
def _embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBED_MODEL)


@lru_cache(maxsize=1)
def _esco_vectors():
    import numpy as np
    _, pref = _esco_labels()
    if not pref:
        return None
    path = INDEX_DIR / "pref_embeddings.npy"
    if path.exists():
        return np.load(path)
    vecs = _embedder().encode([p for _, p in pref], batch_size=256, normalize_embeddings=True,
                              show_progress_bar=False).astype("float32")
    np.save(path, vecs)
    return vecs


def esco_nearest(phrases: list[str]) -> list[tuple[str, str, float] | None]:
    """Nearest ESCO preferred label for each phrase as (uri, label, cosine), or None without the index.

    Skipped where sentence-transformers is not installed: the deployed app leaves PyTorch out
    (app/requirements.txt), and the other four steps still run there.
    """
    if os.getenv("SKILLABUS_NO_EMBED") or importlib.util.find_spec("sentence_transformers") is None:
        return [None] * len(phrases)
    vecs = _esco_vectors()
    if vecs is None or not phrases:
        return [None] * len(phrases)
    _, pref = _esco_labels()
    q = _embedder().encode(phrases, normalize_embeddings=True, show_progress_bar=False)
    sims = q @ vecs.T
    out = []
    for row in sims:
        i = int(row.argmax())
        out.append((pref[i][0], pref[i][1], float(row[i])))
    return out


# ---------------------------------------------------------------- 4. Lightcast
_token: dict = {}


def _lightcast_token() -> str | None:
    cid, secret = os.getenv("LIGHTCAST_CLIENT_ID"), os.getenv("LIGHTCAST_CLIENT_SECRET")
    if not (cid and secret):
        return None
    if "value" not in _token:
        import requests
        r = requests.post("https://auth.emsicloud.com/connect/token", timeout=20, data={
            "client_id": cid, "client_secret": secret, "grant_type": "client_credentials", "scope": "emsi_open"})
        r.raise_for_status()
        _token["value"] = r.json()["access_token"]
    return _token["value"]


def lightcast_lookup(phrase: str) -> tuple[str, str] | None:
    """(Lightcast id, name) for the closest skill, if it is close enough to the phrase. Cached on disk."""
    path = LIGHTCAST_CACHE / f"{slug(phrase)[:80]}.json"
    if path.exists():
        hit = json.loads(path.read_text(encoding="utf-8"))
    else:
        token = _lightcast_token()
        if token is None:
            return None
        import requests
        r = requests.get("https://emsiservices.com/skills/versions/latest/skills", timeout=20,
                         params={"q": phrase, "limit": 1}, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        data = r.json().get("data", [])
        hit = {"id": data[0]["id"], "name": data[0]["name"]} if data else {}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(hit), encoding="utf-8")
    if not hit:
        return None
    a, b = key(phrase), key(hit["name"])
    close = a in b or b in a or difflib.SequenceMatcher(None, a, b).ratio() >= 0.6
    return (hit["id"], hit["name"]) if close else None


# ---------------------------------------------------------------- main
def normalise(mentions: list[dict]) -> list[dict]:
    """Fill skill_id, skill_label and vocab on each mention (data contract section 1)."""
    alias_to_canon, links = _dictionary()
    exact, _ = _esco_labels()
    out: list[dict | None] = [None] * len(mentions)
    pending: list[int] = []

    for i, m in enumerate(mentions):
        text = m["text"].strip()
        # Keep the canonical extract() found: tier 2 matches forms the alias list lacks ("REST APIs").
        canon = m.get("canonical") or lookup(alias_to_canon, text)
        res = {**m, "canonical": canon, "similarity": None}
        if canon and canon in links:
            uri, label = links[canon]
            out[i] = {**res, "skill_id": f"esco:{uri}", "skill_label": label, "vocab": "esco", "how": "dictionary"}
            continue
        if canon not in NOT_IN_ESCO:
            hit = lookup(exact, text) or (exact.get(key(canon)) if canon else None)
            if hit and hit[0] not in BLOCKED_ESCO:
                out[i] = {**res, "skill_id": f"esco:{hit[0]}", "skill_label": hit[1], "vocab": "esco",
                          "how": "esco_exact"}
                continue
        out[i] = res
        pending.append(i)

    embed_idx = [i for i in pending if out[i]["canonical"] not in NOT_IN_ESCO]
    nearest = esco_nearest([out[i]["canonical"] or out[i]["text"] for i in embed_idx])
    for i, near in zip(embed_idx, nearest):
        if near and near[2] >= ESCO_MIN_SIM and near[0] not in BLOCKED_ESCO:
            out[i] |= {"skill_id": f"esco:{near[0]}", "skill_label": near[1], "vocab": "esco",
                       "how": "esco_embed", "similarity": round(near[2], 3)}

    for i in pending:
        if "skill_id" in out[i]:
            continue
        canon = out[i]["canonical"]
        if canon and canon not in NOT_IN_ESCO:
            # A skill we know (e.g. predictive modelling) that ESCO words differently: keep our id.
            out[i] |= {"skill_id": f"seed:{slug(canon)}", "skill_label": canon, "vocab": "seed", "how": "dictionary"}
            continue
        label = canon or out[i]["text"]
        try:
            lc = lightcast_lookup(label)
        except Exception:  # network or quota trouble must not stop the pipeline
            lc = None
        if lc:
            out[i] |= {"skill_id": f"lightcast:{lc[0]}", "skill_label": lc[1], "vocab": "lightcast", "how": "lightcast"}
        else:
            out[i] |= {"skill_id": f"emerging:{slug(label)}", "skill_label": label, "vocab": "emerging",
                       "how": "emerging"}
    return out
