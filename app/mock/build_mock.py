"""Build the mock data the app is designed against (docs/data_contract.md).

Real inputs, simple methods: skills come from the one dictionary (skills_seed_v2.csv),
demand from the 3,204 Seek ads (skill_counts_v2.csv), subject evidence from a keyword
match over the UTS Handbook 2026 text. The real pipeline (embeddings, LLM tier) replaces
this; the shapes stay the same.

Run from the repo root:  python app/mock/build_mock.py
Needs data/raw/data-eda/ (Van Thong's folder) for uts_subjects_2026.csv.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MOCK = ROOT / "app" / "mock"
SUBJECTS_CSV = ROOT / "data/raw/data-eda/data/raw/uts_subjects_2026.csv"
SEED_CSV = ROOT / "data/processed/skills_seed_v2.csv"
COUNTS_CSV = ROOT / "data/processed/skill_counts_v2.csv"
TOP_CSV = ROOT / "data/processed/top_skills.csv"
MDSI = "C04372"

# Van Thong's dictionary-to-ESCO links; skills without one keep a seed: id (data_contract.md).
_esco = pd.read_csv(ROOT / "data/raw/data-eda/config/skill_to_esco.csv", dtype=str).dropna(subset=["esco_uri"])
ESCO = {r.canonical: f"esco:{r.esco_uri}" for _, r in _esco.iterrows()}

# Stronger evidence first; assessment rows arrive from Akash's collection.
LAYER_WEIGHT = {"learning_objective": 1.0, "assessment": 0.9, "weekly_topic": 0.8, "description": 0.5}


def fix_text(s: str) -> str:
    """Undo the UTF-8-read-as-Latin-1 damage in some Handbook fields (bullets show as 'â€¢')."""
    if not isinstance(s, str):
        return ""
    if "â" in s or "Ã" in s:
        try:
            s = s.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return re.sub(r"\s+", " ", s).strip()


def split_topics(s: str) -> list[str]:
    s = fix_text(s)
    if not s:
        return []
    parts = re.split(r"\s*(?:\||•|\(\d+\)|(?<!\d)\d{1,2}\.\s)\s*", s)
    out = []
    for p in (p.strip(" :;-") for p in parts):
        if len(p) <= 3 or re.search(r"will cover (the )?(following )?topics|topics from the following", p, re.I):
            continue
        # Some subjects put a whole week's paragraph in one bullet; keep evidence sentence-sized.
        out.extend(split_sentences(p) if len(p) > 250 else [p])
    return out


def split_outcomes(s: str) -> list[str]:
    s = fix_text(s)
    parts = re.split(r"(?=SLO\s?\d+\s?:)", s)
    return [p.strip() for p in parts if len(p.strip()) > 5]


def split_sentences(s: str) -> list[str]:
    s = fix_text(s)
    return [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if len(p.strip()) > 10]


def subject_layers() -> pd.DataFrame:
    """One row per piece of subject text: the data_contract section 3 shape."""
    u = pd.read_csv(SUBJECTS_CSV, dtype=str)
    rows = []
    for _, r in u.iterrows():
        base = {
            "subject_code": r.subject_code,
            "subject_name": fix_text(r.subject_name),
            "course": r.courses,
            "source_url": r.handbook_url,
            "collected_by": "handbook",
        }
        for t in split_outcomes(r.learning_outcomes):
            rows.append({**base, "layer": "learning_objective", "text": t})
        for t in split_topics(r.topics):
            rows.append({**base, "layer": "weekly_topic", "text": t})
        for t in split_sentences(r.description):
            rows.append({**base, "layer": "description", "text": t})
    return pd.DataFrame(rows)


def load_aliases() -> dict[str, tuple[list[str], bool]]:
    seed = pd.read_csv(SEED_CSV, comment="#", dtype=str)
    out = {}
    for _, r in seed.iterrows():
        aliases = [r.canonical] + [a for a in str(r.aliases).split("|") if a and a != "nan"]
        out[r.canonical] = (aliases, r.strict == "1")
    return out


def alias_regex(aliases: list[str], strict: bool) -> re.Pattern:
    alt = "|".join(re.escape(a) for a in sorted(set(aliases), key=len, reverse=True))
    return re.compile(rf"(?<![\w+#]){'(?:' + alt + ')'}(?![\w+#])", 0 if strict else re.I)


def demand() -> dict[str, float]:
    c = pd.read_csv(COUNTS_CSV, comment="#")
    skill_col = "skill" if "skill" in c.columns else c.columns[0]
    pct_col = next(col for col in c.columns if "pct" in col)
    return dict(zip(c[skill_col], c[pct_col].astype(float)))


def text_units(text: str) -> list[str]:
    """Bullets and sentences of an ad or resume, with hard line wraps joined back up."""
    blocks = re.split(r"\n\s*[-•]\s+|\n\s*\n", text)
    units = []
    for b in blocks:
        units.extend(split_sentences(b.replace("\n", " ")) or ([b.strip()] if b.strip() else []))
    return units


def first_match(units: list[str], rx: re.Pattern) -> str | None:
    """First sentence naming the skill; the header block (job title, source) only as a last resort."""
    hits = [t for t in units if rx.search(t)]
    return next((t for t in hits if t is not units[0]), hits[0] if hits else None)


def evidence_for(skill: str, rx: re.Pattern, layers: pd.DataFrame) -> list[dict]:
    """Best piece of evidence per subject for one skill, strongest subjects first."""
    hits = layers[layers.text.str.contains(rx, regex=True)]
    best = {}
    for _, h in hits.iterrows():
        score = LAYER_WEIGHT[h.layer] + (0.2 if MDSI in str(h.course) else 0.0)
        if h.subject_code not in best or score > best[h.subject_code]["score"]:
            best[h.subject_code] = {
                "subject_code": h.subject_code,
                "subject_name": h.subject_name,
                "score": round(score, 2),
                "skill_label": skill,
                "layer": h.layer,
                "text": h.text,
                "source_url": h.source_url,
            }
    return sorted(best.values(), key=lambda e: -e["score"])


def recommend(missing: list[dict], layers, rx_of) -> tuple[list[dict], dict]:
    """Subjects that teach the missing skills, plus a greedy demand-weighted learning path."""
    per_subject: dict[str, dict] = {}
    for s in missing:
        for e in evidence_for(s["skill_label"], rx_of[s["skill_label"]], layers)[:3]:
            rec = per_subject.setdefault(e["subject_code"], {
                "subject_code": e["subject_code"], "subject_name": e["subject_name"],
                "source_url": e["source_url"], "covers": [], "evidence": [], "_score": 0.0})
            rec["covers"].append(s["skill_label"])
            rec["evidence"].append({k: e[k] for k in ("skill_label", "layer", "text")})
            # +1 so skills at 0% in the 2019-22 corpus (LLMs, generative AI) still count
            rec["_score"] += e["score"] * (s["demand_pct"] + 1)
    recs = sorted(per_subject.values(), key=lambda r: -r["_score"])
    top = max((r["_score"] for r in recs), default=1.0)
    for r in recs:
        r["score"] = round(r.pop("_score") / top, 2)

    weight = {s["skill_label"]: s["demand_pct"] + 1 for s in missing}
    uncovered, path = set(weight), []
    while uncovered and len(path) < 3:
        gain = lambda r: sum(weight[k] for k in set(r["covers"]) & uncovered)
        best = max(recs, key=gain, default=None)
        if not best or gain(best) == 0:
            break
        path.append(best["subject_code"])
        uncovered -= set(best["covers"])
    closed = set(weight) - uncovered
    raw_total = sum(s["demand_pct"] for s in missing) or 1.0
    learning_path = {
        "subjects": path,
        "gaps_closed": len(closed),
        "gaps_total": len(weight),
        "demand_covered_pct": round(100 * sum(s["demand_pct"] for s in missing if s["skill_label"] in closed) / raw_total, 1),
    }
    # The path's subjects are always shown, then the next best up to six in total.
    shown = [r for r in recs if r["subject_code"] in path]
    shown.sort(key=lambda r: path.index(r["subject_code"]))
    shown += [r for r in recs if r["subject_code"] not in path][: max(0, 6 - len(shown))]
    return shown, learning_path


def build(mode: str, skills: list[str], ad_text: str | None, resume_text: str, aliases, layers, pct,
          partial: dict[str, str] | None = None) -> dict:
    partial = partial or {}
    rx_of = {k: alias_regex(*aliases[k]) for k in skills}
    ad_units, cv_units = text_units(ad_text or ""), text_units(resume_text)
    out_skills = []
    for k in skills:
        cv_ev = first_match(cv_units, rx_of[k])
        status = "partial" if k in partial else ("have" if cv_ev else "missing")
        out_skills.append({
            "skill_id": ESCO.get(k, f"seed:{k.lower().replace(' ', '-')}"),
            "skill_label": k,
            "status": status,
            "demand_pct": round(pct.get(k, 0.0), 1),
            "demand_pct_2026": None,
            "emerging": k in ("Large language models", "Generative AI"),
            "ad_evidence": first_match(ad_units, rx_of[k]) if ad_text else
                           f"Asked for in {pct.get(k, 0.0):.0f}% of 3,204 Seek Data Scientist ads (2019-22).",
            "resume_evidence": partial.get(k, cv_ev),
        })
    gaps = [s for s in out_skills if s["status"] != "have"]
    recs, path = recommend(gaps, layers, rx_of)
    return {"ad_id": mode, "mode": mode, "skills": out_skills, "recommendations": recs, "learning_path": path}


def main() -> None:
    layers = subject_layers()
    layers.to_csv(MOCK / "subject_layers.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    aliases, pct = load_aliases(), demand()
    ad = (MOCK / "sample_ad.txt").read_text(encoding="utf-8")
    cv = (MOCK / "sample_resume.txt").read_text(encoding="utf-8")

    # Job seeker: the poster's block 5 example, the same 8 technical skills.
    gap = pd.read_csv(ROOT / "data/processed/gap.csv", comment="#")
    job = build("rw-2026-09-23", list(gap.skill), ad, cv, aliases, layers, pct)

    # Elective chooser / career switcher: target role = the 15 most-asked technical skills.
    top = list(pd.read_csv(TOP_CSV, comment="#").skill)
    role = build("role-data-scientist", top, None, cv, aliases, layers, pct,
                 partial={"Statistics": "Statistics: descriptive statistics, hypothesis testing basics"})

    for name, data in (("gap_job_seeker.json", job), ("gap_role_data_scientist.json", role)):
        (MOCK / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        p = data["learning_path"]
        print(f"{name}: {sum(s['status'] != 'have' for s in data['skills'])}/{len(data['skills'])} gaps, "
              f"path {p['subjects']} closes {p['gaps_closed']}/{p['gaps_total']} ({p['demand_covered_pct']}% of demand)")
    print(f"subject_layers.csv: {len(layers)} rows, {layers.subject_code.nunique()} subjects, "
          f"{layers.layer.value_counts().to_dict()}")


if __name__ == "__main__":
    main()
