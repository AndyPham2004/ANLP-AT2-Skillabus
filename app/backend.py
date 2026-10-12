"""The one place the app calls the pipeline.

Runs the real stages in src/skillabus when they are implemented; until then (or if one
fails) falls back to app/baseline.py, which returns the same shape. With an OpenAI key,
the GPT-4o-mini tier then adds skills the dictionary does not know (e.g. "agentic AI"),
normalised to ESCO / Lightcast / emerging. The app shows which engine produced the result.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "app"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import baseline  # noqa: E402


def llm_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def augment_with_llm(result: dict, resume_text: str, ad_text: str | None, taken: list[str]) -> dict:
    """Add the hard skills only the LLM tier finds in the ad, then recompute subjects and path."""
    from skillabus.llm_extract import extract_llm
    from skillabus.normalise import normalise

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
            "demand_pct_2026": None,
            "emerging": m["vocab"] in ("emerging", "lightcast"),
            "ad_evidence": m["sentence"],
            "resume_evidence": have["sentence"] if have else None,
            "found_by": "llm",
        })
    if not extra:
        return result
    skills = result["skills"] + extra
    gaps = [s for s in skills if s["status"] != "have"]
    recs, path = baseline.recommend(gaps, set(taken))
    return {**result, "skills": skills, "recommendations": recs, "learning_path": path}


def analyse(resume_text: str, ad_text: str | None, taken: list[str]) -> tuple[dict, str]:
    """Return (gap result, engine name)."""
    try:
        from skillabus.extract import extract
        from skillabus.match import match
        from skillabus.normalise import normalise
        from skillabus.recommend import recommend

        if ad_text is None:
            raise NotImplementedError("role mode runs on the baseline until the pipeline supports it")
        ad_skills = normalise(extract(ad_text))
        resume_skills = normalise(extract(resume_text)) if resume_text else []
        skills = match(ad_skills, resume_skills)
        rec = recommend([s for s in skills if s["status"] != "have"])
        return {"ad_id": "pasted-ad", "mode": "pasted-ad", "skills": skills, "soft_skills": [], **rec}, "pipeline"
    except Exception as e:  # not built yet, or a half-finished stage: the demo must still run
        result = baseline.analyse(resume_text, ad_text, taken=taken)
        engine = "baseline" if isinstance(e, NotImplementedError) else f"baseline (pipeline error: {e})"

    if ad_text and llm_enabled():
        try:
            result = augment_with_llm(result, resume_text, ad_text, taken)
            engine += " + GPT-4o-mini"
        except Exception as e:
            engine += f" (LLM tier skipped: {e})"
    return result, engine


def subjects() -> list[tuple[str, str]]:
    """(code, name) for every subject in the profiles, for the 'subjects I've taken' picker."""
    lay = baseline.resources().layers
    pairs = lay[["subject_code", "subject_name"]].drop_duplicates().sort_values("subject_code")
    return list(pairs.itertuples(index=False, name=None))
