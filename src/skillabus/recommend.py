"""Rank subjects for the missing skills and build the learning path. Owner: Phuong Nhi.

    recommend(gaps)  ->  {"recommendations": [...], "learning_path": {...}}   (data contract section 2)

For each gap skill and each subject:
1. Evidence. Every row of the subject profile (one learning objective, assessment, weekly
   topic or description sentence) is compared with the skill. A row counts when it names
   the skill (dictionary aliases) or is similar enough to it (TF-IDF baseline, embeddings
   final). Its score is that similarity (1.0 when named) times the weight of its layer.
2. Strength. A subject that names the skill in its title, or in several rows, is more likely
   to teach it than one that mentions it once: best row + a bonus per extra row + a title bonus.
3. A subject "covers" a skill when its strength is at least COVER_RATIO of the strongest
   subject's for that skill, so one passing mention does not count next to a whole subject.

Learning path: greedy weighted cover. Take the subject that covers the most still-uncovered
demand, repeat, at most three subjects. Only subjects the student can enrol in count
(requisites.py): a subject that needs one or two open prerequisites comes with them, as one
step that uses that many of the three places and is valued per place; a subject the student
cannot take (43023 needs 42172 or 41040, which an MDSI student cannot enrol in) is left out
and listed under `learning_path.dropped`. The path is then laid out over sessions.

Second tier (ideas doc 4.5): the gaps the UTS path leaves open get the same greedy cover over
outside courses (external_courses.csv: free or free-to-audit, no UTS credit), at most three.
The two are never mixed in one pass: a short course aimed at one skill would push UTS subjects
out. Output: `outside_recommendations`, and `learning_path.outside` with the share of demand
the UTS path and outside courses close together.
"""

from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

import numpy as np

from . import paths
from .extract import _dictionary_hits, load_dictionary
from .match import demand_2026_low, skill_query
from .requisites import Rules, enrolment, load_rules, schedule, sessions_offered
from .similarity import best_method, similarity

ROOT = paths.ROOT
# Van Thong's four-layer file (committed). The Handbook-only mock of 3 Oct is in archive/mock_2026-10-03/.
PROFILE_PATHS = (paths.SUBJECT_PROFILES,)

METHODS = ("keyword", "tfidf", "embed")
# Stronger evidence first: taught and assessed > graded > covered in class > mentioned.
LAYER_WEIGHT = {"learning_objective": 1.0, "assessment": 0.9, "weekly_topic": 0.8, "description": 0.5}
# A row that does not name the skill counts only above this similarity. Set by reading the
# closest unnamed rows (notebooks/pn_calibrate_matching.py, 8 Oct, 429 Handbook rows):
# embed >= 0.55 keeps "Classification and prediction" for machine learning and "Evaluate and
# deploy predictive models in business production" for MLOps; at 0.50 about half the rows were
# generic ("key concepts, definitions, and algorithms"). TF-IDF above 0.35 only finds rows
# that share the skill's words.
MIN_SIM = {"tfidf": 0.35, "embed": 0.55}
EXTRA_ROW_BONUS = 0.15      # per further row of the same subject about the skill, at most MAX_EXTRA_ROWS
MAX_EXTRA_ROWS = 3
TITLE_BONUS = 0.40          # the subject's name names the skill ("94691 Deep Learning")
HOME_COURSE = "C04372"      # MDSI: its subjects need no approval, so they win ties
HOME_BONUS = 0.10
COVER_RATIO = 0.60          # a subject covers a skill if it is at least this strong, relative to the best
SUBJECTS_PER_SKILL = 5      # and is among this many strongest subjects for it
MAX_PATH = 3
MAX_SUBJECTS = 10           # recommendations returned: the path first, then the next best
EXTERNAL_CSV = paths.EXTERNAL_COURSES
MAX_OUTSIDE = 3             # outside courses in the second tier
MAX_OUTSIDE_SHOWN = 6       # outside recommendations returned


# -------------------------------------------------------------------------- profiles

def _profiles_path(profiles_csv: str | None) -> Path:
    if profiles_csv:
        path = Path(profiles_csv)
        return path if path.is_absolute() else ROOT / path
    for path in PROFILE_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError(f"No subject profiles found; looked for {', '.join(str(p) for p in PROFILE_PATHS)}")


@lru_cache(maxsize=4)
def _load(path: str, mtime: float) -> tuple[list[dict], list[frozenset], dict[str, frozenset]]:
    """(rows, dictionary skills named in each row, dictionary skills named in each subject title)."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in csv.DictReader(f)]
    rows = [row for row in rows if row.get("text") and row.get("subject_code")]
    named = [frozenset(c for _, _, c in _dictionary_hits(row["text"])) for row in rows]
    titles = {row["subject_code"]: row["subject_name"] for row in rows}
    in_title = {code: frozenset(c for _, _, c in _dictionary_hits(name)) for code, name in titles.items()}
    return rows, named, in_title


def load_profiles(profiles_csv: str | None = None):
    path = _profiles_path(profiles_csv)
    return _load(str(path), path.stat().st_mtime)


@lru_cache(maxsize=1)
def _aliases() -> dict[str, tuple[str, ...]]:
    return {skill["canonical"]: skill["aliases"] for skill in load_dictionary()}


_query = skill_query   # the text a skill is compared by: its name plus its dictionary aliases


def _phrase(label: str) -> re.Pattern:
    """Whole-phrase pattern for a skill outside the dictionary (found by the NER or LLM tier)."""
    return re.compile(rf"(?<![A-Za-z0-9]){re.escape(label)}(?![A-Za-z0-9])", re.IGNORECASE)


# -------------------------------------------------------------------------- evidence

def subject_evidence(labels: list[str], profiles_csv: str | None = None, method: str | None = None,
                     exclude: set[str] | None = None, home_course: str | None = HOME_COURSE) -> dict[str, list[dict]]:
    """For each skill, the subjects with evidence for it, strongest first.

    Each item: subject_code, subject_name, source_url, strength, layer, text, match
    ("named" or "similar"), similarity.
    """
    method = method or best_method()
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    rows, named, in_title = load_profiles(profiles_csv)
    exclude = exclude or set()
    texts = [row["text"] for row in rows]
    layer = np.array([LAYER_WEIGHT.get(row["layer"], 0.5) for row in rows])
    known = _aliases()

    if method == "keyword" or not labels:
        sims = np.zeros((len(labels), len(rows)))
    else:
        sims = similarity([_query(label) for label in labels], texts, method)
        sims = np.where(sims >= MIN_SIM[method], sims, 0.0)

    out: dict[str, list[dict]] = {}
    for i, label in enumerate(labels):
        if label in known:
            is_named = np.array([label in hits for hits in named])
            title_hit = {code for code, hits in in_title.items() if label in hits}
        else:
            rx = _phrase(label)
            is_named = np.array([bool(rx.search(t)) for t in texts])
            title_hit = {row["subject_code"] for row in rows if rx.search(row["subject_name"])}
        row_sim = np.where(is_named, 1.0, sims[i])
        row_score = row_sim * layer

        by_subject: dict[str, list[int]] = {}
        for j in np.flatnonzero(row_score > 0):
            by_subject.setdefault(rows[j]["subject_code"], []).append(int(j))

        found = []
        for code, idx in by_subject.items():
            if code in exclude:
                continue
            best = max(idx, key=lambda j: row_score[j])
            row = rows[best]
            strength = (row_score[best]
                        + EXTRA_ROW_BONUS * min(len(idx) - 1, MAX_EXTRA_ROWS)
                        + (TITLE_BONUS if code in title_hit else 0.0)
                        + (HOME_BONUS if home_course and home_course in row.get("course", "") else 0.0))
            found.append({
                "subject_code": code, "subject_name": row["subject_name"],
                "source_url": row.get("source_url", ""), "strength": round(float(strength), 3),
                "layer": row["layer"], "text": row["text"],
                "match": "named" if is_named[best] else "similar",
                "similarity": round(float(row_sim[best]), 3),
            })
        out[label] = sorted(found, key=lambda e: (-e["strength"], e["subject_code"]))
    return out


# ------------------------------------------------------------------------- recommend

NEW_SKILL_PCT = 1.0  # below this share of the 2019-22 ads, a skill counts as new (LLMs, generative AI)


def _weight(gap: dict) -> float:
    """Market demand behind a gap: the 2019-22 share (3,204 ads). For a skill that barely existed
    then (LLMs are 0%), the 2026 share instead, by the lower end of its 95% interval, since the
    2026 sample is only 22 data roles from 12 employers (9 of them data scientists). Skills that
    were already asked for keep their 2019-22 share: the 2026 sample over-represents AI work
    ("Artificial intelligence" in 86% of the 22), so it would outweigh 3,204 ads. +1 so a skill at 0% still counts for something.
    Only a gap that carries a 2026 share gets the fallback: match() leaves `demand_pct_2026` empty
    for a role outside the data roles of that sample, whose own share is then the only weight."""
    old = gap.get("demand_pct") or 0.0
    if old < NEW_SKILL_PCT and gap.get("demand_pct_2026") is not None:
        old = max(old, demand_2026_low().get(gap["skill_label"], 0.0))
    return old + 1.0


def _code_number(code: str) -> int:
    return int(re.sub(r"\D", "", code) or 0)


def learning_path(covers: dict[str, set[str]], weight: dict[str, float], score: dict[str, float],
                  max_subjects: int = MAX_PATH, needs=None) -> dict:
    """Greedy weighted cover: the subject closing the most uncovered demand, then the next, ...

    covers  subject_code -> the gap skills it covers
    weight  gap skill -> demand weight
    score   subject_code -> overall score, to break ties
    needs   optional function (subject_code, subjects already in the path) -> the prerequisites
            still to add before it (a set), or None when the student cannot take it. A subject
            and its prerequisites are one step; the step's gain is shared over its places, so
            two places must close at least twice the demand of one.
    """
    uncovered, path = set(weight), []
    while uncovered and len(path) < max_subjects:
        best, best_key, best_step = None, None, None
        for code in covers:
            if code in path:
                continue
            extra = needs(code, set(path)) if needs else set()
            if extra is None:
                continue
            step = [*sorted(set(extra) - set(path)), code]
            if len(path) + len(step) > max_subjects:
                continue
            closed = set().union(*(covers.get(c, set()) for c in step)) & uncovered
            gain = sum(weight[k] for k in closed)
            # Ties: the higher-scoring subject, then the lower subject code, so the result is stable.
            key = (gain / len(step), -len(step), score.get(code, 0.0), -_code_number(code))
            if best_key is None or key > best_key:
                best, best_key, best_step = code, key, step
        if best is None or best_key[0] == 0:
            break
        path += best_step
        for c in best_step:
            uncovered -= covers.get(c, set())
    closed = set(weight) - uncovered
    total = sum(weight.values())
    return {
        "subjects": path,
        "gaps_closed": len(closed),
        "gaps_total": len(weight),
        "demand_covered_pct": round(100 * sum(weight[k] for k in closed) / total, 1) if total else 0.0,
    }


def recommend(gaps: list[dict], profiles_csv: str | None = None, method: str | None = None,
              exclude: set[str] | None = None, home_course: str | None = HOME_COURSE,
              rules: Rules | None = None, start: tuple[str, int] | None = None,
              external_csv: str | None = None) -> dict:
    """Return `recommendations` and `learning_path` (data contract section 2).

    gaps          skills from match() whose status is not "have"
    profiles_csv  subject profiles (data contract section 3); default: the real file, else the mock
    method        "keyword" (names only), "tfidf" or "embed"; default: embed when the model is installed
    exclude       subject codes the student has already taken (they also meet prerequisites)
    home_course   the student's course: admission conditions naming it are met
    rules         prerequisites and teaching periods; default: load_rules() (none when the files are missing)
    start         first session of the plan, e.g. ("Autumn", 2027); default: the next one
    external_csv  outside courses for the second tier; default: external_courses.csv ("" = none)
    """
    rules = rules if rules is not None else load_rules()
    done = set(exclude or ())
    labels = list(dict.fromkeys(g["skill_label"] for g in gaps))
    weight = {g["skill_label"]: _weight(g) for g in gaps}
    evidence = subject_evidence(labels, profiles_csv, method, done, home_course)
    names = {row["subject_code"]: (row["subject_name"], row.get("source_url", "")) for row in load_profiles(profiles_csv)[0]}

    # Who can enrol: decided once against what the student has taken; the path adds to it below.
    access = {code: enrolment(code, done, rules, home_course)
              for code in {e["subject_code"] for found in evidence.values() for e in found}}

    subjects: dict[str, dict] = {}
    dropped: dict[str, dict] = {}
    for label in sorted(labels, key=lambda k: -weight[k]):
        found = evidence[label]
        floor = COVER_RATIO * found[0]["strength"] if found else 0.0
        for e in [e for e in found if e["strength"] >= floor][:SUBJECTS_PER_SKILL]:
            code = e["subject_code"]
            if access[code]["status"] == "closed":
                drop = dropped.setdefault(code, {"subject_code": code, "subject_name": e["subject_name"],
                                                 "reason": access[code]["reason"], "covers": []})
                drop["covers"].append(label)
                continue
            rec = subjects.setdefault(code, {
                "subject_code": code, "subject_name": e["subject_name"],
                "source_url": e["source_url"], "score": 0.0, "covers": [], "evidence": [],
                "needs": access[code]["needs"], "offered": sessions_offered(code, rules),
                "unverified": access[code]["unverified"]})
            rec["covers"].append(label)
            rec["evidence"].append({"skill_label": label, "layer": e["layer"], "text": e["text"], "match": e["match"]})
            rec["score"] += e["strength"] * weight[label]

    top = max((rec["score"] for rec in subjects.values()), default=0.0) or 1.0
    for rec in subjects.values():
        rec["score"] = round(rec["score"] / top, 2)          # the best subject is 1.0

    def needs(code: str, in_path: set[str]):
        status = enrolment(code, done | in_path, rules, home_course)
        return None if status["status"] == "closed" else set(status["needs"])

    path = learning_path({code: set(rec["covers"]) for code, rec in subjects.items()}, weight,
                         {code: rec["score"] for code, rec in subjects.items()},
                         needs=needs if rules.loaded else None)
    chosen = path["subjects"]
    for code in chosen:                                   # a prerequisite that covers no gap itself
        if code not in subjects:
            name, url = names.get(code, (code, ""))
            subjects[code] = {"subject_code": code, "subject_name": name, "source_url": url, "score": 0.0,
                              "covers": [], "evidence": [], "needs": [], "offered": sessions_offered(code, rules),
                              "unverified": code in rules.unverified}
    path["plan"] = schedule(chosen, rules, start, done, home_course)
    path["dropped"] = sorted(dropped.values(), key=lambda d: (-sum(weight[k] for k in d["covers"]), d["subject_code"]))

    ranked = sorted(subjects.values(), key=lambda rec: (-rec["score"], rec["subject_code"]))
    shown = [subjects[code] for code in chosen]
    # Every gap that has a subject keeps its strongest one in the list, even past MAX_SUBJECTS.
    for label in sorted(labels, key=lambda k: -weight[k]):
        best = next((subjects[e["subject_code"]] for e in evidence[label] if e["subject_code"] in subjects), None)
        if best and not any(label in rec["covers"] for rec in shown):
            shown.append(best)
    shown += [rec for rec in ranked if rec not in shown][: max(0, MAX_SUBJECTS - len(shown))]

    still_open = [label for label in labels if not any(label in subjects[c]["covers"] for c in chosen)]
    outside_recs, path["outside"] = outside(still_open, weight, external_csv, method)
    return {"recommendations": shown, "learning_path": path, "outside_recommendations": outside_recs}


def _external_path(external_csv: str | None) -> Path | None:
    if external_csv == "":
        return None
    path = Path(external_csv) if external_csv else EXTERNAL_CSV
    path = path if path.is_absolute() else ROOT / path
    return path if path.exists() else None


def outside(open_gaps: list[str], weight: dict[str, float], external_csv: str | None = None,
            method: str | None = None) -> tuple[list[dict], dict]:
    """Second tier: outside courses for the gaps the UTS path leaves open.

    Same evidence and greedy cover as the UTS subjects (no prerequisites, no sessions), at most
    MAX_OUTSIDE courses. Returns (outside_recommendations, learning_path["outside"]).
    weight holds every gap, so `demand_covered_pct` is over all gaps: the UTS path plus these courses.
    """
    total = sum(weight.values())
    closed_by_uts = sum(w for k, w in weight.items() if k not in open_gaps)
    block = {"courses": [], "gaps_closed": 0, "gaps_open_before": len(open_gaps), "still_open": list(open_gaps),
             "demand_covered_pct": round(100 * closed_by_uts / total, 1) if total else 0.0}
    path = _external_path(external_csv)
    if not open_gaps or path is None:
        return [], block

    evidence = subject_evidence(open_gaps, str(path), method, home_course=None)
    meta = {row["subject_code"]: row for row in load_profiles(str(path))[0]}
    courses: dict[str, dict] = {}
    for label in sorted(open_gaps, key=lambda k: -weight[k]):
        found = evidence[label]
        floor = COVER_RATIO * found[0]["strength"] if found else 0.0
        for e in [e for e in found if e["strength"] >= floor][:SUBJECTS_PER_SKILL]:
            row = meta[e["subject_code"]]
            rec = courses.setdefault(e["subject_code"], {
                "subject_code": e["subject_code"], "subject_name": e["subject_name"], "source_url": e["source_url"],
                "provider": row.get("provider", ""), "cost": row.get("cost", ""), "score": 0.0,
                "covers": [], "evidence": []})
            rec["covers"].append(label)
            rec["evidence"].append({"skill_label": label, "layer": e["layer"], "text": e["text"], "match": e["match"]})
            rec["score"] += e["strength"] * weight[label]
    top = max((rec["score"] for rec in courses.values()), default=0.0) or 1.0
    for rec in courses.values():
        rec["score"] = round(rec["score"] / top, 2)

    open_weight = {k: weight[k] for k in open_gaps}
    tier2 = learning_path({c: set(r["covers"]) for c, r in courses.items()}, open_weight,
                          {c: r["score"] for c, r in courses.items()}, max_subjects=MAX_OUTSIDE)
    closed = set().union(*(courses[c]["covers"] for c in tier2["subjects"])) if tier2["subjects"] else set()
    block.update({
        "courses": tier2["subjects"],
        "gaps_closed": len(closed),
        "still_open": [k for k in open_gaps if k not in closed],
        "demand_covered_pct": round(100 * (closed_by_uts + sum(weight[k] for k in closed)) / total, 1),
    })
    ranked = sorted(courses.values(), key=lambda r: (-r["score"], r["subject_code"]))
    shown = [courses[c] for c in tier2["subjects"]]
    shown += [r for r in ranked if r not in shown][: max(0, MAX_OUTSIDE_SHOWN - len(shown))]
    return shown, block
