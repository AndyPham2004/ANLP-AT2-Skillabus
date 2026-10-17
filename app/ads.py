"""The "Browse ads" page: the newest Australian ads the project collected, all from 2026, for all 11 roles,
as a searchable list, so a student who has no ad at hand can pick a real one (Quan, 17 Oct: the newest sources).

- JobsPipe 2026 (`ads/jobspipe_2026_skills.csv`): 1,932 ads posted 1 Sep to 16 Oct 2026, 89 to 216 per role, the
  same ads behind the demand bars. Their text is not in git (JobsPipe's terms forbid redistributing it in bulk, and
  it is the employers'), so it is read from `data/raw/jobspipe/`, where the fetch left it. Without that folder an ad
  still lists, with the skills found at fetch time and its link, but it cannot become the goal.
- ATS 2026 (`ads/ats_2026_clean.csv`): the 85 job-board ads with an IT role, text in git. An ad JobsPipe also has
  (same company and title) is listed once.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

import pandas as pd

import backend  # noqa: F401  (puts src/ on sys.path)
from skillabus import paths  # noqa: E402

FAMILIES = backend.role_families()                 # family -> its roles, in the app's order
ALL = "All roles"
LOCATIONS = ["Anywhere", "Sydney", "Melbourne", "Brisbane", "Perth", "Canberra", "Adelaide", "Remote"]
STATES = {"New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD", "Western Australia": "WA",
          "South Australia": "SA", "Australian Capital Territory": "ACT", "Tasmania": "TAS", "Northern Territory": "NT"}
STATE_CODES = "|".join(STATES.values())


def short_location(loc: str) -> str:
    """'Sydney, New South Wales, Australia' -> 'Sydney, NSW'; 'Sydney, Sydney Region' -> 'Sydney'.

    The job boards write it their own way: 'Sydney NSW 2000' -> 'Sydney, NSW', 'AU - HQ - NSW' -> 'NSW',
    'AU - Sydney' -> 'Sydney', 'AU: Melbourne: (260 Burwood Rd)' -> 'Melbourne', 'Greater Sydney Area' -> 'Sydney',
    'Australian Capital Territory, Australia' -> 'ACT'.
    """
    loc = re.sub(r"\(.*?\)", "", str(loc or ""))                 # a street address in brackets
    loc = re.sub(r"^\s*AU\s*[-:]\s*", "", loc)                    # the country as a prefix
    loc = re.sub(r"\bHQ\s*[-:]\s*", "", loc)
    loc = re.sub(r"^\s*Greater (.+?) Area\s*$", r"\1", loc).strip(" :-")
    loc = re.sub(r"\s+\d{4}$", "", loc)                           # a postcode
    loc = re.sub(rf"^([^,]*\S)\s+({STATE_CODES})$", r"\1, \2", loc)   # 'Sydney NSW'
    parts = [p.strip() for p in loc.split(",") if p.strip() and p.strip() != "Australia"]
    if not parts:
        return "Australia"
    city = STATES.get(parts[0], parts[0])
    state = next((STATES.get(p, p) for p in parts[1:] if p in STATES or p in STATES.values()), None)
    return f"{city}, {state}" if state else city


def _key(company: str, title: str) -> tuple[str, str]:
    return re.sub(r"\W+", " ", company.lower()).strip(), re.sub(r"\W+", " ", title.lower()).strip()


@lru_cache(maxsize=1)
def jobspipe_texts() -> dict[str, str]:
    """ad_id -> the ad's text, from the raw JobsPipe fetches on this machine ({} where they are absent)."""
    out: dict[str, str] = {}
    for f in sorted(paths.RAW.joinpath("jobspipe").glob("*.json")):
        try:
            items = json.loads(f.read_text(encoding="utf-8")) or []
        except (OSError, ValueError):
            continue
        for item in items:
            if item.get("id") and item.get("description"):
                out[f"jp-{item['id']}"] = str(item["description"]).strip()
    return out


@lru_cache(maxsize=1)
def load() -> list[dict]:
    """Every ad, newest first: id, title, company, location, posted, source, url, role, text ("" when it is not
    on this machine) and skills (the vocabulary skills found at fetch time; None when only the text has them)."""
    texts = jobspipe_texts()
    jp = pd.read_csv(paths.JOBSPIPE_SKILLS, dtype=str).fillna("")
    out = [{"id": r.ad_id, "title": r.title.strip(), "company": r.company.strip(), "location": short_location(r.location),
            "posted": r.date_posted[:10], "source": f"{r.providers or 'a job board'} via JobsPipe", "url": r.url,
            "role": r.role, "text": texts.get(r.ad_id, ""), "skills": [s for s in r.skills.split("|") if s]}
           for r in jp.itertuples(index=False)]
    seen = {_key(a["company"], a["title"]) for a in out}
    ats = pd.read_csv(paths.ATS_2026_ADS, dtype=str).fillna("")
    for r in ats[ats.role != "other"].itertuples(index=False):
        if _key(r.company, r.title) in seen:
            continue
        seen.add(_key(r.company, r.title))
        out.append({"id": r.ad_id, "title": r.title.strip(), "company": r.company.strip(),
                    "location": short_location(r.location), "posted": r.posted[:10], "source": r.source, "url": r.url,
                    "role": r.role, "text": r.description.strip(), "skills": None})
    # Newest first; within a day by id, which mixes the roles (the JobsPipe file is sorted by role).
    return sorted(out, key=lambda a: (a["posted"], a["id"]), reverse=True)


def roles_of(family: str | None) -> list[str]:
    """The roles of a family, or all 11 for None / "All"."""
    return FAMILIES.get(family) or [r for roles in FAMILIES.values() for r in roles]


def search(query: str = "", role: str = ALL, location: str = "Anywhere", limit: int | None = 30,
           family: str | None = None) -> list[dict]:
    """Ads matching a free-text query (title, company, location, skills or text), a family, a role and a place."""
    q = (query or "").strip().lower()
    allowed = set(roles_of(family))
    rows = []
    for ad in load():
        if ad["role"] not in allowed or (role not in (ALL, None) and ad["role"] != role):
            continue
        if location not in ("Anywhere", None):
            where = (ad["location"] + " " + ad["text"][:300]).lower()
            if location.lower() not in where:
                continue
        if q and q not in " ".join((ad["title"], ad["company"], ad["location"], " ".join(ad["skills"] or []),
                                    ad["text"])).lower():
            continue
        rows.append(ad)
        if limit and len(rows) >= limit:
            break
    return rows


def by_id(ad_id: str) -> dict | None:
    return next((a for a in load() if a["id"] == ad_id), None)
