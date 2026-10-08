"""Compare ad skills with resume skills: have / partial / missing. Owner: Phuong Nhi.

    match(ad_skills, resume_skills)  ->  the `skills` list of the gap result (data contract section 2)

Both inputs are skill mentions from extract(), with or without normalise().

have     the resume names the same skill (same dictionary name or same skill_id)
partial  the resume does not name it, but the ad asks for the umbrella skill of a dictionary
         category and the resume shows a part of it (ad "machine learning", resume "scikit-learn")
missing  neither

Substitute tools (ad "Tableau", resume "Power BI") are not counted as partial. We tried
embedding similarity between skill names (notebooks/pn_calibrate_matching.py, 8 Oct): true
substitutes scored lower than unrelated pairs (Tableau~Power BI 0.30, AWS~Azure 0.44, but
Airflow~MLflow 0.54, machine learning~artificial intelligence 0.70), so no threshold works.

Also here: soft_skills() for the skills left out of the gap list, role_profile() so a role
can be matched like an ad, and score_matrix() to rank ads for a resume (TF-IDF vs
embeddings vs our skill overlap), which is what the matching evaluation needs.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

from .extract import load_dictionary
from .similarity import embed_documents, tfidf_similarity

ROOT = Path(__file__).resolve().parents[2]
COUNTS_CSV = ROOT / "data" / "processed" / "skill_counts_v2.csv"
COUNTS_2026_CSV = ROOT / "data" / "processed" / "skill_counts_2026.csv"
TOP_CSV = ROOT / "data" / "processed" / "top_skills.csv"
N_ADS = 3204

SOFT_CATEGORIES = {"Professional"}        # real skills, but they do not map to subjects
# The skill that names its whole category: asking for it is met in part by any skill in it.
UMBRELLA = {
    "Machine learning": "Machine learning",
    "Deep learning": "Deep learning",
    "Natural language processing": "NLP",
    "Cloud platforms": "Cloud",
    "Statistics": "Statistics",
    "Data visualisation": "Visualisation",
    "Computer vision": "Computer vision",
}
# A programming language is a named requirement: knowing Java is not partly knowing Python.
NOT_TRANSFERABLE = {"Programming"} | SOFT_CATEGORIES
# Dictionary skills ESCO has no concept for (normalise.py keeps the same list).
EMERGING_SEED = {"Large language models", "Generative AI"}


# --------------------------------------------------------------------------- lookups

def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


@lru_cache(maxsize=1)
def _category() -> dict[str, str]:
    return {skill["canonical"]: skill["category"] for skill in load_dictionary()}


@lru_cache(maxsize=1)
def _demand() -> dict[str, float]:
    """Share of the 3,204 Seek ads 2019-22 naming each dictionary skill."""
    return {row["skill"]: float(row["pct_ads"]) for row in _rows(COUNTS_CSV)}


@lru_cache(maxsize=1)
def _demand_2026() -> dict[str, float]:
    """Same over the 2026 sample (Van Thong, skill_counts_2026.csv); empty until that file exists."""
    if not COUNTS_2026_CSV.exists():
        return {}
    return {row["skill"]: float(row["pct_2026"]) for row in _rows(COUNTS_2026_CSV) if row.get("pct_2026")}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _key(mention: dict) -> str:
    """What makes two mentions the same skill: dictionary name, else skill_id, else the words."""
    return mention.get("canonical") or mention.get("skill_id") or f"text:{slug(mention['text'])}"


def _group(mentions: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for mention in mentions:
        groups.setdefault(_key(mention), []).append(mention)
    return groups


def _evidence(mentions: list[dict]) -> str:
    """The sentence to show: the first full sentence, not a title line such as 'Data Scientist - Python, SQL'."""
    sentences = [m["sentence"] for m in mentions]
    return next((s for s in sentences if len(s.split()) >= 7), sentences[0])


def _is_soft(mention: dict) -> bool:
    return _category().get(mention.get("canonical")) in SOFT_CATEGORIES or mention.get("kind") == "soft"


# ----------------------------------------------------------------------------- match

def _related(skill: str, resume: dict[str, list[dict]]) -> str | None:
    """The resume skill that partly meets an umbrella skill (the most in-demand one), or None."""
    category = _category().get(skill)
    if category is None or category in NOT_TRANSFERABLE or UMBRELLA.get(skill) != category:
        return None
    parts = [k for k in resume if k != skill and _category().get(k) == category]
    return max(parts, key=lambda k: _demand().get(k, 0.0), default=None)


def match(ad_skills: list[dict], resume_skills: list[dict], include_soft: bool = False) -> list[dict]:
    """Return the `skills` list of the gap result (data contract section 2), most in-demand first."""
    resume = _group(resume_skills)
    resume_ids = {m["skill_id"]: key for key, ms in resume.items() for m in ms if m.get("skill_id")}
    out = []

    for key, mentions in _group(ad_skills).items():
        first = mentions[0]
        if not include_soft and _is_soft(first):
            continue
        canonical = first.get("canonical")
        label = canonical or first.get("skill_label") or first["text"]
        skill_id = first.get("skill_id") or (f"seed:{slug(canonical)}" if canonical
                                             else f"emerging:{slug(first['text'])}")
        vocab = first.get("vocab")
        emerging = vocab in ("emerging", "lightcast") if vocab else (canonical is None or canonical in EMERGING_SEED)

        same = key if key in resume else resume_ids.get(first.get("skill_id"))
        related = None if same else (_related(canonical, resume) if canonical else None)
        skill = {
            "skill_id": skill_id,
            "skill_label": label,
            "status": "have" if same else "partial" if related else "missing",
            "demand_pct": round(_demand().get(canonical, 0.0), 1),
            "demand_pct_2026": _demand_2026().get(canonical),
            "emerging": emerging,
            "ad_evidence": _evidence(mentions),
            "resume_evidence": _evidence(resume[same or related]) if (same or related) else None,
        }
        if related:
            skill["related_skill"] = related
        if all(m.get("method") == "llm" for m in mentions):
            skill["found_by"] = "llm"
        out.append(skill)
    return sorted(out, key=lambda s: -s["demand_pct"])


def soft_skills(ad_skills: list[dict]) -> list[str]:
    """Professional skills the ad names (communication, teamwork): shown, but not part of the gap list."""
    names = {m.get("canonical") or m["text"] for m in ad_skills if _is_soft(m)}
    return sorted(names, key=lambda k: -_demand().get(k, 0.0))


def role_profile(top_n: int = 15) -> list[dict]:
    """A role as skill mentions: the most-asked technical skills (top_skills.csv), ready for match()."""
    mentions = []
    for row in _rows(TOP_CSV)[:top_n]:
        pct = float(row["pct_ads"])
        mentions.append({
            "text": row["skill"], "canonical": row["skill"], "method": "dictionary",
            "sentence": f"Asked for in {pct:.0f}% of {N_ADS:,} Seek Data Scientist ads (2019-22).",
        })
    return mentions


# ----------------------------------------------------------- ranking ads for a resume

def skill_overlap(ad_skills: list[dict], resume_skills: list[dict]) -> float:
    """Demand-weighted share of the ad's skills the resume covers (have = 1, partial = 0.5), in [0, 1]."""
    skills = match(ad_skills, resume_skills)
    weights = [s["demand_pct"] + 1 for s in skills]          # +1 so 0% skills still count
    credit = [{"have": 1.0, "partial": 0.5, "missing": 0.0}[s["status"]] for s in skills]
    return sum(w * c for w, c in zip(weights, credit)) / sum(weights) if weights else 0.0


def score_matrix(resume_texts: list[str], ad_texts: list[str], method: str = "tfidf",
                 extract_method: str = "dictionary"):
    """How well each ad fits each resume: array [len(resume_texts), len(ad_texts)].

    "tfidf"   cosine of the two whole texts under TF-IDF (baseline)
    "embed"   cosine of mean sentence embeddings
    "skills"  skill_overlap() of the extracted skills (what the app shows)
    Rank a row to get the best ads for that resume; score it with P@5 and MRR.
    """
    import numpy as np

    from .extract import extract, split_sentences

    if method == "tfidf":
        return tfidf_similarity(list(resume_texts), list(ad_texts))
    if method == "embed":
        resumes = embed_documents([split_sentences(t) for t in resume_texts])
        ads = embed_documents([split_sentences(t) for t in ad_texts])
        return resumes @ ads.T
    if method == "skills":
        resumes = [extract(t, extract_method) for t in resume_texts]
        ads = [extract(t, extract_method) for t in ad_texts]
        return np.array([[skill_overlap(ad, resume) for ad in ads] for resume in resumes])
    raise ValueError(f'method must be "tfidf", "embed" or "skills", got {method!r}')
