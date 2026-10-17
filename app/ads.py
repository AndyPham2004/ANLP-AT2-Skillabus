"""The "Browse ads" page: the cleaned Australian ads of 2024-26 (data/2_demand/ads, Van Thong)
as a searchable list, so a student who has no ad at hand can pick a real one.

Only ads with their full text (160 of 192) are offered: a truncated ad would hide skills.
"""

from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd

import backend  # noqa: F401  (puts src/ on sys.path)
from skillabus import paths  # noqa: E402

ROLES = [                      # the app's role name, pattern on the title (first match wins)
    ("Data Scientist", r"data scien"),
    ("Data Engineer", r"data engineer|data platform|etl"),
    ("Data Analyst", r"data analyst|analytics|insights"),
    ("Machine Learning Engineer", r"machine learning|\bml\b|mlops"),
    ("Machine Learning Engineer", r"\bai\b|artificial intelligence|gen(erative)? ?ai|llm"),     # AI Engineer ads
    ("Data Analyst", r"\bbi\b|business intelligence|tableau|power bi|reporting"),             # BI Developer ads
]
# A chip only for a role that has ads; the few "Other" ads stay under All roles.
ROLE_CHIPS = ["All roles"] + sorted({label for label, _ in ROLES})
LOCATIONS = ["Anywhere", "Sydney", "Melbourne", "Brisbane", "Perth", "Canberra", "Remote"]
STATES = {"New South Wales": "NSW", "Victoria": "VIC", "Queensland": "QLD", "Western Australia": "WA",
          "South Australia": "SA", "Australian Capital Territory": "ACT", "Tasmania": "TAS"}


def role_of(title: str) -> str:
    t = (title or "").lower()
    for label, pattern in ROLES:
        if re.search(pattern, t):
            return label
    return "Other"


def short_location(loc: str) -> str:
    """'Sydney, New South Wales, Australia' -> 'Sydney, NSW'; 'Sydney, Sydney Region' -> 'Sydney'.

    The applicant-tracking ads write it their own way: 'AU - HQ - NSW' -> 'NSW', 'AU - Sydney' -> 'Sydney',
    'AU: Melbourne: (260 Burwood Rd)' -> 'Melbourne', 'Greater Sydney Area' -> 'Sydney'.
    """
    loc = re.sub(r"\(.*?\)", "", str(loc or ""))                 # a street address in brackets
    loc = re.sub(r"^\s*AU\s*[-:]\s*", "", loc)                    # the country as a prefix
    loc = re.sub(r"\bHQ\s*[-:]\s*", "", loc)
    loc = re.sub(r"^\s*Greater (.+?) Area\s*$", r"\1", loc).strip(" :-")
    parts = [p.strip() for p in loc.split(",") if p.strip() and p.strip() != "Australia"]
    if not parts:
        return "Australia"
    city = parts[0]
    state = next((STATES[p] for p in parts[1:] if p in STATES), None)
    return f"{city}, {state}" if state else city


@lru_cache(maxsize=1)
def load() -> list[dict]:
    """Every full-text ad, newest first: id, title, company, location, posted, source, url, text, role."""
    df = pd.read_csv(paths.RECENT_ADS)
    df = df[df["full_text"].astype(str).str.lower().isin(("true", "1", "yes", "y"))]
    df = df.sort_values("posted", ascending=False)
    out = []
    for r in df.itertuples(index=False):
        out.append({
            "id": str(r.ad_id), "title": str(r.title).strip(), "company": str(r.company).strip(),
            "location": short_location(r.location), "posted": str(r.posted)[:10],
            "source": str(r.source), "url": str(r.url) if isinstance(r.url, str) else "",
            "text": str(r.description).strip(), "role": role_of(str(r.title)),
        })
    return out


def search(query: str = "", role: str = "All roles", location: str = "Anywhere", limit: int = 30) -> list[dict]:
    """Ads matching a free-text query (title, company, location or text), a role chip and a location chip."""
    q = (query or "").strip().lower()
    rows = []
    for ad in load():
        if role not in ("All roles", None) and ad["role"] != role:
            continue
        if location not in ("Anywhere", None):
            where = (ad["location"] + " " + ad["text"][:300]).lower()
            if location.lower() not in where:
                continue
        if q and q not in " ".join((ad["title"], ad["company"], ad["location"], ad["text"])).lower():
            continue
        rows.append(ad)
        if len(rows) >= limit:
            break
    return rows


def label(ad: dict) -> str:
    """One line for the list: title, company, location, date."""
    return f"{ad['title']} — {ad['company']} · {ad['location']} · {ad['posted']}"


def by_id(ad_id: str) -> dict | None:
    return next((a for a in load() if a["id"] == ad_id), None)
