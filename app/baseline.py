"""Baseline analysis the app falls back on until the real pipeline is wired in.

Dictionary match for skills (skills_seed_v2.csv), keyword match over subject text for
evidence, greedy demand-weighted learning path. Output follows docs/data_contract.md
section 2, so swapping in src/skillabus changes nothing in the app.
Everything it reads is committed, so it also runs on Streamlit Cloud.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEED_CSV = ROOT / "data/processed/skills_seed_v2.csv"
COUNTS_CSV = ROOT / "data/processed/skill_counts_v2.csv"
TOP_CSV = ROOT / "data/processed/top_skills.csv"
ESCO_CSV = ROOT / "data/processed/skill_to_esco.csv"
PROFILES = [ROOT / "data/processed/subject_profiles.csv", ROOT / "app/mock/subject_layers.csv"]

MDSI = "C04372"
SOFT_CATEGORIES = {"Professional"}
EMERGING = {"Large language models", "Generative AI"}
# Stronger evidence first.
LAYER_WEIGHT = {"learning_objective": 1.0, "assessment": 0.9, "weekly_topic": 0.8, "description": 0.5}
N_ADS = 3204
MAX_SUBJECTS = 10  # path subjects first, then the next best


def fix_text(s) -> str:
    """Undo UTF-8-read-as-Latin-1 damage (bullets showing as 'â€¢') and squash whitespace."""
    if not isinstance(s, str):
        return ""
    if "â" in s or "Ã" in s:
        try:
            s = s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return re.sub(r"\s+", " ", s).strip()


def split_sentences(s: str) -> list[str]:
    s = fix_text(s)
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if len(p.strip()) > 10]


def text_units(text: str) -> list[str]:
    """Bullets and sentences of an ad or resume, with hard line wraps joined back up."""
    units = []
    for b in re.split(r"\n\s*[-•*]\s+|\n\s*\n", text or ""):
        units.extend(split_sentences(b.replace("\n", " ")) or ([b.strip()] if b.strip() else []))
    return units


def first_match(units: list[str], rx: re.Pattern) -> str | None:
    """First sentence naming the skill; the header block (job title, source) only as a last resort."""
    hits = [t for t in units if rx.search(t)]
    return next((t for t in hits if t is not units[0]), hits[0] if hits else None)


def alias_regex(aliases: list[str], strict: bool) -> re.Pattern:
    alt = "|".join(re.escape(a) for a in sorted(set(aliases), key=len, reverse=True))
    return re.compile(rf"(?<![\w+#])(?:{alt})(?![\w+#])", 0 if strict else re.I)


@dataclass(frozen=True)
class Resources:
    regex: dict
    category: dict
    demand: dict
    esco: dict
    layers: pd.DataFrame
    role_skills: tuple


def _read_noted(path, **kwargs) -> pd.DataFrame:
    """read_csv without the leading "# ..." note lines; comment="#" would also cut "C#" to "C"."""
    lines = Path(path).read_text(encoding="utf-8").splitlines(keepends=True)
    return pd.read_csv(io.StringIO("".join(l for l in lines if not l.startswith("#"))), **kwargs)


@lru_cache(maxsize=1)
def resources() -> Resources:
    seed = _read_noted(SEED_CSV, dtype=str)
    regex, category = {}, {}
    for _, r in seed.iterrows():
        aliases = [r.canonical] + [a for a in str(r.aliases).split("|") if a and a != "nan"]
        regex[r.canonical] = alias_regex(aliases, r.strict == "1")
        category[r.canonical] = r.category
    counts = _read_noted(COUNTS_CSV)
    demand = dict(zip(counts.skill, counts.pct_ads.astype(float)))
    esco = {}
    if ESCO_CSV.exists():
        e = pd.read_csv(ESCO_CSV, dtype=str).dropna(subset=["esco_uri"])
        esco = {r.canonical: f"esco:{r.esco_uri}" for _, r in e.iterrows()}
    layers = pd.read_csv(next(p for p in PROFILES if p.exists()), dtype=str).fillna("")
    role = tuple(_read_noted(TOP_CSV).skill)
    return Resources(regex, category, demand, esco, layers, role)


def skill_regex(skill: str) -> re.Pattern:
    """The dictionary pattern for a skill, or a plain whole-phrase pattern for one found outside it (LLM tier)."""
    return resources().regex.get(skill) or alias_regex([skill], False)


def find_skills(text: str) -> list[str]:
    """Dictionary skills named in a text, most in-demand first."""
    res = resources()
    found = [k for k, rx in res.regex.items() if rx.search(text or "")]
    return sorted(found, key=lambda k: -res.demand.get(k, 0.0))


def evidence_for(skill: str, exclude: set[str]) -> list[dict]:
    """Best piece of evidence per subject for one skill, strongest subjects first."""
    res = resources()
    lay = res.layers
    hits = lay[lay.text.str.contains(skill_regex(skill), regex=True) & ~lay.subject_code.isin(exclude)]
    best: dict[str, dict] = {}
    for _, h in hits.iterrows():
        score = LAYER_WEIGHT.get(h.layer, 0.5) + (0.2 if MDSI in h.course else 0.0)
        if h.subject_code not in best or score > best[h.subject_code]["score"]:
            best[h.subject_code] = {
                "subject_code": h.subject_code, "subject_name": h.subject_name, "score": round(score, 2),
                "skill_label": skill, "layer": h.layer, "text": h.text, "source_url": h.source_url,
            }
    return sorted(best.values(), key=lambda e: -e["score"])


def recommend(gaps: list[dict], exclude: set[str]) -> tuple[list[dict], dict]:
    """Subjects for the gaps, plus a greedy demand-weighted learning path of at most 3."""
    per_subject: dict[str, dict] = {}
    for s in gaps:
        for e in evidence_for(s["skill_label"], exclude)[:3]:
            rec = per_subject.setdefault(e["subject_code"], {
                "subject_code": e["subject_code"], "subject_name": e["subject_name"],
                "source_url": e["source_url"], "covers": [], "evidence": [], "_score": 0.0,
                # contract section 2 keys the baseline cannot fill: no prerequisite or session data here
                "needs": [], "offered": [], "unverified": False})
            rec["covers"].append(s["skill_label"])
            rec["evidence"].append({k: e[k] for k in ("skill_label", "layer", "text")})
            # +1 so skills at 0% in the 2019-22 corpus (LLMs, generative AI) still count
            rec["_score"] += e["score"] * (s["demand_pct"] + 1)
    recs = sorted(per_subject.values(), key=lambda r: -r["_score"])
    top = max((r["_score"] for r in recs), default=1.0) or 1.0
    for r in recs:
        r["score"] = round(r.pop("_score") / top, 2)

    weight = {s["skill_label"]: s["demand_pct"] + 1 for s in gaps}
    uncovered, path = set(weight), []
    while uncovered and len(path) < 3:
        def gain(r):
            return sum(weight[k] for k in set(r["covers"]) & uncovered)
        best = max(recs, key=gain, default=None)
        if not best or gain(best) == 0:
            break
        path.append(best["subject_code"])
        uncovered -= set(best["covers"])
    closed = set(weight) - uncovered
    raw_total = sum(s["demand_pct"] for s in gaps) or 1.0
    learning_path = {
        "subjects": path,
        "gaps_closed": len(closed),
        "gaps_total": len(weight),
        "demand_covered_pct": round(
            100 * sum(s["demand_pct"] for s in gaps if s["skill_label"] in closed) / raw_total, 1),
        "plan": [{"subject_code": c, "session": "", "offered": [], "after": [], "unverified": False} for c in path],
        "dropped": [],
    }
    # Shown: the path first, then each gap's two strongest subjects (so a 0%-demand skill like
    # LLMs still gets its evidence), then the best of the rest up to MAX_SUBJECTS.
    order = list(path)
    for s in gaps:
        best_two = [r["subject_code"] for r in recs if s["skill_label"] in r["covers"]][:2]
        order += [c for c in best_two if c not in order]
    order += [r["subject_code"] for r in recs if r["subject_code"] not in order]
    by_code = {r["subject_code"]: r for r in recs}
    return [by_code[c] for c in order[: max(MAX_SUBJECTS, len(path) + 2 * len(gaps))]], learning_path


def analyse(resume_text: str, ad_text: str | None = None, taken: list[str] | None = None,
            partial: dict[str, str] | None = None, ad_id: str = "pasted-ad") -> dict:
    """Gap result for a resume against one ad, or against the Data Scientist role when ad_text is None."""
    res = resources()
    taken_set, partial = set(taken or []), partial or {}
    if ad_text:
        named = find_skills(ad_text)
        skills = [k for k in named if res.category[k] not in SOFT_CATEGORIES]
        soft = [k for k in named if res.category[k] in SOFT_CATEGORIES]
        mode = ad_id
    else:
        skills, soft, mode = list(res.role_skills), [], "role-data-scientist"

    ad_units, cv_units = text_units(ad_text or ""), text_units(resume_text)
    out = []
    for k in skills:
        cv_ev = first_match(cv_units, res.regex[k]) if cv_units else None
        status = "have" if cv_ev else "missing"
        if k in partial:
            status, cv_ev = "partial", partial[k]
        if status == "missing" and taken_set:
            # A subject the student has already taken counts as having the skill.
            done = evidence_for(k, set())
            done = [e for e in done if e["subject_code"] in taken_set]
            if done:
                status, cv_ev = "have", f"From {done[0]['subject_code']} {done[0]['subject_name']} (taken)"
        pct = round(res.demand.get(k, 0.0), 1)
        out.append({
            "skill_id": res.esco.get(k, f"seed:{k.lower().replace(' ', '-')}"),
            "skill_label": k,
            "status": status,
            "demand_pct": pct,
            "demand_pct_2026": None,
            "emerging": k in EMERGING,
            "ad_evidence": first_match(ad_units, res.regex[k]) if ad_text
                           else f"Asked for in {pct:.0f}% of {N_ADS:,} Seek Data Scientist ads (2019-22).",
            "resume_evidence": cv_ev,
        })
    gaps = [s for s in out if s["status"] != "have"]
    recs, path = recommend(gaps, taken_set)
    return {"ad_id": mode, "mode": mode, "skills": out, "soft_skills": soft,
            "recommendations": recs, "learning_path": path}
