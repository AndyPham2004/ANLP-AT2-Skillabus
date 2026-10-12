"""The one place the app calls the pipeline.

Runs the real stages in src/skillabus when they are implemented; until then (or if one
fails) falls back to app/baseline.py, which returns the same shape. The app shows which
engine produced the result.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "app"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import baseline  # noqa: E402


def analyse(resume_text: str, ad_text: str | None, taken: list[str]) -> tuple[dict, str]:
    """Return (gap result, engine name). Engine is "pipeline" or "baseline"."""
    try:
        from skillabus.extract import extract
        from skillabus.match import match
        from skillabus.normalise import normalise
        from skillabus.recommend import recommend

        ad_skills = normalise(extract(ad_text)) if ad_text else None
        resume_skills = normalise(extract(resume_text)) if resume_text else []
        if ad_skills is None:
            raise NotImplementedError("role mode runs on the baseline until the pipeline supports it")
        skills = match(ad_skills, resume_skills)
        rec = recommend([s for s in skills if s["status"] != "have"])
        return {"ad_id": "pasted-ad", "mode": "pasted-ad", "skills": skills, "soft_skills": [], **rec}, "pipeline"
    except NotImplementedError:
        return baseline.analyse(resume_text, ad_text, taken=taken), "baseline"
    except Exception as e:  # a half-finished stage must not take the demo down
        return baseline.analyse(resume_text, ad_text, taken=taken), f"baseline (pipeline error: {e})"


def subjects() -> list[tuple[str, str]]:
    """(code, name) for every subject in the profiles, for the 'subjects I've taken' picker."""
    lay = baseline.resources().layers
    pairs = lay[["subject_code", "subject_name"]].drop_duplicates().sort_values("subject_code")
    return list(pairs.itertuples(index=False, name=None))
