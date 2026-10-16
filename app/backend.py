"""The one place the app calls the pipeline.

Runs the real stages in src/skillabus; if one fails, falls back to app/baseline.py, which
returns the same shape (Job seeker and Data Scientist only). With an OpenAI key, the
GPT-4o-mini tier then adds skills the dictionary does not know (e.g. "agentic AI"),
normalised to ESCO / Lightcast / emerging. The app shows which engine produced the result.

Also here, for the role pages: the 11 roles by family, where each role's demand comes from,
the core skills of the four roles with no Australian ad counts, certifications per role and
the self-study resources per skill.
"""

from __future__ import annotations

import csv
import os
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "app"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import baseline  # noqa: E402
from skillabus import paths  # noqa: E402

DEFAULT_ROLE = "Data Scientist"
MAX_CORE_SKILLS = 15          # like the 15 most-asked skills of the other roles
# ESCO files it under digital skills, but it is about building automation, not IT security
# (priority_skills.csv, which D9 collected resources for, leaves it out too).
NOT_CORE = {"building systems monitoring technology"}
CERT_LEVELS = ("foundational", "associate", "professional", "expert")
LEVELS = ("beginner", "intermediate", "advanced")
COST_CHOICES = {                      # the Self-study cost filter: label -> costs shown
    "Free only": ("free",),
    "Include free-to-audit": ("free", "free-to-audit"),
    "Include paid": ("free", "free-to-audit", "paid"),
}
MAX_SELF_STUDY = 3


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------- data files

def _read(path) -> list[dict]:
    """A CSV as a list of dicts, skipping "# ..." note lines."""
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def _split(cell: str) -> list[str]:
    """ "AWS; Azure" -> ["AWS", "Azure"] """
    return [x.strip() for x in (cell or "").split(";") if x.strip()]


@lru_cache(maxsize=1)
def _occupations() -> tuple[dict, ...]:
    return tuple(_read(paths.ROLE_OCCUPATIONS))


# ---------------------------------------------------------------- roles

def role_families() -> dict[str, list[str]]:
    """Role family -> its roles, in the order of role_occupations.csv (all 11 roles)."""
    families: dict[str, list[str]] = {}
    for row in _occupations():
        roles = families.setdefault(row["role_family"], [])
        if row["role"] not in roles:
            roles.append(row["role"])
    return families


def has_ad_counts(role: str) -> bool:
    """True for the 7 roles with Australian ad counts; False for the 4 shown as core skills only."""
    from skillabus.match import roles
    return role in {r["role"] for r in roles()}


def occupation(role: str, source: str) -> dict | None:
    """The role's first occupation in one taxonomy ("esco", "onet" or "asc"), or None."""
    return next((row for row in _occupations() if row["role"] == role and row["source"] == source), None)


def role_source(role: str, source: str | None = None, period: str | None = None) -> str:
    """Where a role's demand comes from: source, year, n and kind of data (the caption under the picker).

    source, period: a gap row's demand_source and demand_period (match.py); default: match.roles(),
    which reads the same values from the files before any resume is matched.
    """
    from skillabus.match import roles
    info = next((r for r in roles() if r["role"] == role), None)
    if info is None:
        esco, onet = occupation(role, "esco"), occupation(role, "onet")
        return (f"No Australian ad counts yet: core skills of the ESCO occupation '{esco['occupation_title']}' "
                f"and O*NET {onet['occupation_code']} {onet['occupation_title']}.")
    source, period = source or info["source"], period or info["period"]
    if source == "Seek":   # match.py takes Data Scientist from the full-text Seek ads
        return f"{info['n_ads']:,} Seek {role} ads {period}, full text."
    # "lukebarousse/data_jobs (2023, Australia)" -> "data_jobs"; that file has each ad's tool list, no text
    dataset = source.split(" (")[0].split("/")[-1]
    where = "Australian " if "Australia" in source else ""
    return f"{info['n_ads']:,} {where}{role} postings {period} ({dataset}, the tools each ad lists)."


# ---------------------------------------------------------------- core skills (roles with no ad counts)

def core_skill_rows(role: str) -> list[dict]:
    """The role's core skills as vocabulary rows: O*NET in-demand tools first, then ESCO essential digital skills.

    Each: label, skill_id, source ("onet" or "esco"), why (the sentence the app shows as evidence).
    A tool O*NET names twice (GitHub and Git are both Git) is listed once.
    """
    vocab = [v for v in _read(paths.SKILLS_VOCABULARY) if "core_skill" in v["used_for"]]
    by_label = {v["label"]: v for v in vocab}
    by_uri = {v["esco_uri"]: v for v in vocab if v["esco_match"] == "exact"}
    tool_label = {r["onet_tool"]: r["label"] for r in _read(paths.ONET_TOOL_MAP)}
    rows = [r for r in _read(paths.OCCUPATION_SKILLS) if r["role"] == role]

    picked: dict[str, dict] = {}
    for r in rows:
        if r["source"] == "onet" and r["importance"] == "in_demand":
            v = by_label.get(tool_label.get(r["skill"], ""))
            if v and v["label"] not in picked:
                picked[v["label"]] = {"label": v["label"], "skill_id": v["skill_id"], "source": "onet",
                                      "why": f"O*NET lists {v['label']} as an in-demand tool for "
                                             f"{r['occupation_title']} ({r['occupation_code']})."}
    for r in rows:
        if r["source"] == "esco" and r["importance"] == "essential" and r["esco_digital"] == "y":
            v = by_uri.get(r["skill_ref"])
            if v and v["label"] not in picked and v["label"] not in NOT_CORE:
                picked[v["label"]] = {"label": v["label"], "skill_id": v["skill_id"], "source": "esco",
                                      "why": f"An essential skill of the ESCO occupation '{r['occupation_title']}'."}
    return list(picked.values())


def core_skills(role: str, resume_skills: list[dict], top_n: int = MAX_CORE_SKILLS) -> list[dict]:
    """The gap list for a role with no ad counts: each core skill, have or missing, no percentage.

    resume_skills are the resume's mentions from extract() + normalise(); a core skill is "have"
    when the resume names it (same vocabulary label as the mention's dictionary name or ESCO label).
    """
    named: dict[str, str] = {}     # lower-case label -> the resume sentence naming it
    for m in resume_skills:
        for name in (m.get("canonical"), m.get("skill_label")):
            if name:
                named.setdefault(name.lower(), m["sentence"])
    out = []
    for c in core_skill_rows(role)[:top_n]:
        sentence = named.get(c["label"].lower())
        out.append({
            "skill_id": c["skill_id"], "skill_label": c["label"],
            "status": "have" if sentence else "missing",
            "demand_pct": None, "demand_pct_2026": None,      # no Australian ad counts for this role
            "demand_source": None, "demand_period": None,
            "emerging": False, "ad_evidence": c["why"], "resume_evidence": sentence,
            "core_source": c["source"],
        })
    return out


def role_gaps(role: str, resume_skills: list[dict]) -> list[dict]:
    """match_role() for the 7 roles with ad counts; core skills for the 4 without."""
    from skillabus.match import match_role
    return match_role(resume_skills, role) if has_ad_counts(role) else core_skills(role, resume_skills)


def credit_taken(skills: list[dict], taken: list[str]) -> list[dict]:
    """A subject the student has taken counts as having the skills its text names (the 'taken' box)."""
    missing = [s["skill_label"] for s in skills if s["status"] == "missing"]
    if not taken or not missing:
        return skills
    from skillabus.recommend import subject_evidence
    evidence = subject_evidence(missing, method="keyword")      # rows that name the skill, no similarity
    out = []
    for s in skills:
        done = [e for e in evidence.get(s["skill_label"], []) if e["subject_code"] in taken]
        if s["status"] == "missing" and done:
            s = {**s, "status": "have", "resume_evidence": f"From {done[0]['subject_code']} {done[0]['subject_name']} (taken)"}
        out.append(s)
    return out


# ---------------------------------------------------------------- certifications and self-study

def certifications(role: str) -> list[dict]:
    """certifications.csv rows for the role, foundational first, then associate, professional, expert."""
    rows = [r for r in _read(paths.CERTIFICATIONS) if role in _split(r["roles"])]
    rank = {level: i for i, level in enumerate(CERT_LEVELS)}
    return sorted(rows, key=lambda r: rank.get(r["level"], len(CERT_LEVELS)))   # file order within a level


def self_study(skill: str, levels=LEVELS, cost=COST_CHOICES["Include free-to-audit"], role: str | None = None,
               limit: int = MAX_SELF_STUDY) -> list[dict]:
    """At most `limit` self-study resources for one skill, easiest and shortest first (resources.for_skill).

    A resource mainly about the skill (the first skill it lists) comes before one that only touches it,
    so "Linux" shows a Linux course before a Hadoop set-up guide that also uses Linux.
    """
    from skillabus.resources import for_skill
    hits = for_skill(skill, tuple(levels), tuple(cost), role)
    if not hits and role:   # a resource collected for another role still teaches the skill
        hits = for_skill(skill, tuple(levels), tuple(cost))
    hits = sorted(hits, key=lambda r: r["skills"][0] != skill)   # stable: keeps the easiest-first order
    return hits[:limit]


# ---------------------------------------------------------------- analysis

def baseline_ranking(gaps: list[dict], taken: list[str]) -> dict:
    """The baseline's subjects and path, in the shape recommend() returns (no outside courses)."""
    recs, path = baseline.recommend(gaps, set(taken))
    return {"recommendations": recs, "learning_path": path, "outside_recommendations": []}


def augment_with_llm(result: dict, resume_text: str, ad_text: str | None, taken: list[str], rank=None) -> dict:
    """Add the hard skills only the LLM tier finds in the ad, then recompute subjects and path.

    rank(gaps) -> {"recommendations", "learning_path", "outside_recommendations"}; the baseline ranker when not given.
    """
    from skillabus.llm_extract import extract_llm
    from skillabus.match import DEFAULT_PERIOD, DEFAULT_SOURCE, _demand_2026
    from skillabus.normalise import normalise

    trend = _demand_2026()   # ad mode is weighted by the Seek shares, so the 2026 trend applies as in match()
    ad = normalise(extract_llm(ad_text))
    cv = normalise(extract_llm(resume_text)) if resume_text else []
    cv_ids = {m["skill_id"]: m for m in cv} | {m["canonical"]: m for m in cv if m["canonical"]}
    known = {s["skill_label"].lower() for s in result["skills"]} | {s["skill_id"] for s in result["skills"]}
    res = baseline.resources()

    extra, seen = [], set()
    for m in ad:
        label = m["canonical"] or m["skill_label"]
        if m["kind"] != "hard" or label.lower() in known or m["skill_id"] in known or label.lower() in seen:
            continue
        if m["canonical"] and res.category.get(m["canonical"]) in baseline.SOFT_CATEGORIES:
            continue
        seen.add(label.lower())
        have = cv_ids.get(m["skill_id"]) or cv_ids.get(m["canonical"])
        extra.append({
            "skill_id": m["skill_id"], "skill_label": label,
            "status": "have" if have else "missing",
            "demand_pct": round(res.demand.get(m["canonical"], 0.0), 1) if m["canonical"] else 0.0,
            "demand_pct_2026": trend.get(m["canonical"]) if m["canonical"] else None,
            "demand_source": DEFAULT_SOURCE, "demand_period": DEFAULT_PERIOD,
            "emerging": m["vocab"] in ("emerging", "lightcast"),
            "ad_evidence": m["sentence"],
            "resume_evidence": have["sentence"] if have else None,
            "found_by": "llm",
        })
    if not extra:
        return result
    skills = result["skills"] + extra
    gaps = [s for s in skills if s["status"] != "have"]
    ranked = rank(gaps) if rank else baseline_ranking(gaps, taken)
    return {**result, "skills": skills, **ranked}


def empty_result(role: str) -> dict:
    """A result with no skills, for a role the baseline cannot stand in for."""
    return {"ad_id": "none", "mode": "none", "role": role, "skills": [], "soft_skills": [],
            "recommendations": [], "outside_recommendations": [],
            "learning_path": {"subjects": [], "gaps_closed": 0, "gaps_total": 0, "demand_covered_pct": 0.0,
                              "plan": [], "dropped": [], "outside": {"courses": [], "gaps_closed": 0,
                                                                     "gaps_open_before": 0, "still_open": [],
                                                                     "demand_covered_pct": 0.0}}}


def analyse(resume_text: str, ad_text: str | None, taken: list[str], role: str = DEFAULT_ROLE,
            home_course: str | None = "C04372", use_llm: bool = True) -> tuple[dict, str]:
    """Return (gap result, engine name). ad_text None = role mode: the resume against `role`.

    home_course: the student's course for the prerequisite rules (C04372 = MDSI; None = not enrolled,
    so "admission into ..." conditions are not met). use_llm: run the GPT-4o-mini tier when a key is set.
    """
    try:
        from skillabus.extract import extract
        from skillabus.match import match, slug, soft_skills
        from skillabus.normalise import normalise
        from skillabus.recommend import recommend

        def rank(gaps):  # subjects already taken are never recommended
            rec = recommend(gaps, exclude=set(taken), home_course=home_course)
            return {key: rec[key] for key in ("recommendations", "learning_path", "outside_recommendations")}

        resume_skills = normalise(extract(resume_text)) if resume_text else []
        if ad_text is None:
            skills = credit_taken(role_gaps(role, resume_skills), taken)
            mode, soft = f"role-{slug(role)}", []
        else:
            ad_skills = normalise(extract(ad_text))
            skills = match(ad_skills, resume_skills)
            mode, soft = "pasted-ad", soft_skills(ad_skills)
        result = {"ad_id": mode, "mode": mode, "role": role if ad_text is None else None, "skills": skills,
                  "soft_skills": soft, **rank([s for s in skills if s["status"] != "have"])}
        engine = "pipeline"
    except Exception as e:  # a missing library or a half-finished stage: the demo must still run
        rank = None
        if ad_text is None and role != DEFAULT_ROLE:
            # The baseline knows only the Data Scientist profile, so it cannot stand in for this role.
            result, engine = empty_result(role), f"none (pipeline error: {e})"
        else:
            result = baseline.analyse(resume_text, ad_text, taken=taken)
            result.update({"role": None if ad_text else DEFAULT_ROLE, "outside_recommendations": []})
            engine = f"baseline (pipeline error: {e})"

    if ad_text and use_llm and llm_enabled():
        try:
            result = augment_with_llm(result, resume_text, ad_text, taken, rank)
            engine += " + GPT-4o-mini"
        except Exception as e:
            engine += f" (LLM tier skipped: {e})"
    return result, engine


def subjects() -> list[tuple[str, str]]:
    """(code, name) for every subject in the profiles, for the 'subjects I've taken' picker."""
    lay = baseline.resources().layers
    pairs = lay[["subject_code", "subject_name"]].drop_duplicates().sort_values("subject_code")
    return list(pairs.itertuples(index=False, name=None))


HOME_COURSE = "C04372"
COURSE_NAMES = [   # the 44 courses in subject_profiles.csv (subject_profiles.md "Courses"), MDSI first
    ("C04372", "Master of Data Science and Innovation"),
    ("C04370", "Executive Master of Data Science and Innovation"),
    ("C04379", "Master of Business Analytics"), ("C04380", "Master of Business Analytics (C04380)"),
    ("C04467", "Master of Business Analytics (C04467)"),
    ("C04295", "Master of Information Technology"), ("C04296", "Master of Information Technology (C04296)"),
    ("C04373", "Master of Quantitative Finance"),
    ("C04443", "Master of Artificial Intelligence"), ("C04256", "Master of Artificial Intelligence (Online)"),
    ("C04430", "Master of Cybersecurity"), ("C04431", "Master of Cybersecurity (C04431)"),
    ("C04434", "Master of Technology Management"), ("C04435", "Master of Technology Management (C04435)"),
    ("C04450", "Master of Technology Innovation"),
    ("C04265", "Master of Science (Extension)"), ("C04277", "Master of Engineering (Extension)"),
    ("C06113", "Graduate Diploma in Information Technology"),
    ("C06124", "Graduate Diploma in Data Science and Innovation"),
    ("C06147", "Graduate Diploma in Artificial Intelligence"),
    ("C11142", "Graduate Certificate in Information Technology"),
    ("C11247", "Graduate Certificate in Information Technology (C11247)"),
    ("C11191", "Graduate Certificate in Artificial Intelligence"),
    ("C11274", "Graduate Certificate in Data Science and Innovation"),
    ("C11280", "Graduate Certificate in Business Analytics"),
    ("C11385", "Graduate Certificate in Business Analytics (C11385)"),
    ("C11308", "Graduate Certificate in Quantitative Finance"),
    ("C11329", "Graduate Certificate in Health Analytics"),
    ("C11339", "Graduate Certificate in AI Management"),
    ("C11340", "Graduate Certificate in Cybersecurity Management"),
    ("C11350", "Graduate Certificate in Data Visualisation and Storytelling"),
    ("C11376", "Graduate Certificate in Applied AI for Finance"),
    ("C10148", "Bachelor of Information Technology"), ("C10143", "Bachelor of Information Technology (C10143)"),
    ("C10474", "Bachelor of Artificial Intelligence"), ("C10476", "Bachelor of Computing Science"),
    ("C10471", "Bachelor of Cybersecurity"), ("C10457", "Bachelor of Mathematical Sciences"),
    ("C10395", "Bachelor of Information Systems"), ("C10229", "Bachelor of Games Development"),
    ("C10242", "Bachelor of Science"), ("C10347", "Bachelor of Advanced Science"),
    ("C09019", "Bachelor of Information Technology (Honours)"),
    ("C09119", "Bachelor of Computing Science (Honours)"),
    ("C09129", "Bachelor of Mathematical Sciences (Honours)"),
    ("C09168", "Bachelor of Science (Honours)"), ("C09066", "Bachelor of Engineering (Honours)"),
]


def _course_codes() -> set[str]:
    lay = baseline.resources().layers
    if "course" not in lay.columns:
        return set()
    return {c.strip() for cell in lay.course.astype(str) for c in cell.split("|") if c.strip()}


def courses() -> list[tuple[str, str]]:
    """(code, name) of every UTS course in the subject profiles, MDSI first; a code without a name is labelled by its code."""
    present = _course_codes()
    named = [(c, n) for c, n in COURSE_NAMES if c in present]
    known = {c for c, _ in COURSE_NAMES}
    return named + [(c, f"UTS course {c}") for c in sorted(present - known)]


def course_subjects(course: str) -> list[str]:
    """Codes of the subjects that belong to a course (a subject can belong to several)."""
    lay = baseline.resources().layers
    if "course" not in lay.columns or not course:
        return []
    return sorted(lay[lay.course.astype(str).str.contains(course, regex=False)].subject_code.astype(str).unique())


def mdsi_subjects() -> list[tuple[str, str]]:
    """(code, name) of the MDSI (C04372) subjects in the profiles: the "subjects taken" picker shows these first."""
    lay = baseline.resources().layers
    if "course" not in lay.columns:
        return subjects()
    rows = lay[lay.course.astype(str).str.contains("C04372")][["subject_code", "subject_name"]]
    return list(rows.drop_duplicates().sort_values("subject_code").itertuples(index=False, name=None))


def vote_counts() -> dict[tuple[str, str], list[int]]:
    """(subject_code, skill_label) -> [thumbs up, thumbs down] from feedback.csv; empty until someone votes."""
    out: dict[tuple[str, str], list[int]] = {}
    if not paths.FEEDBACK.exists():
        return out
    for row in _read(paths.FEEDBACK):
        out.setdefault((row["subject_code"], row["skill_label"]), [0, 0])[0 if row["vote"] == "up" else 1] += 1
    return out


def dictionary_size() -> int:
    """Number of skills the extractor looks for: the vocabulary's detection rows (281 on 16 Oct 2026;
    never hard-code it), for the footer."""
    from skillabus.extract import load_dictionary
    return len(load_dictionary())
