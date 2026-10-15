"""Self-study resources outside UTS (plan D9): the "Self-study" column next to "Learn at UTS".

    for_skill("Docker")                      ->  resources that teach Docker, beginner first
    for_skill("Docker", cost=("free",))      ->  the same, free only
    text_rows()                              ->  every text row of every resource, for the second tier of recommend()

Two files hold the text the matcher reads, in the schema of subject_profiles.csv: external_courses.csv (56
courses, 13 Oct, rebuilt by build_external.py) and resource_modules.csv (the 15 Oct resources, collected by
hand). resources.csv has one row per resource of both, with level, format, hours, cost, certificate, skills
and roles. Use text_rows() rather than reading external_courses.csv alone.
"""

from __future__ import annotations

import csv
from functools import lru_cache

from . import paths

LEVELS = ("beginner", "intermediate", "advanced")


def _read(path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def resources() -> tuple[dict, ...]:
    """resources.csv; `skills` and `roles` split into lists, `hours` a float (None when blank)."""
    out = []
    for row in _read(paths.RESOURCES):
        row = dict(row)
        row["skills"] = [s.strip() for s in row["skills"].split(";") if s.strip()]
        row["roles"] = [r.strip() for r in row["roles"].split(";") if r.strip()]
        row["hours"] = float(row["hours"]) if row["hours"] else None
        out.append(row)
    return tuple(out)


def for_skill(skill: str, levels: tuple[str, ...] = LEVELS, cost: tuple[str, ...] = ("free", "free-to-audit", "paid"),
              role: str | None = None) -> list[dict]:
    """Resources that teach `skill` (a vocabulary label), filtered by level, cost and role; easiest and shortest first."""
    hits = [r for r in resources() if skill in r["skills"] and r["level"] in levels and r["cost"] in cost
            and (role is None or role in r["roles"])]
    return sorted(hits, key=lambda r: (LEVELS.index(r["level"]), r["hours"] if r["hours"] is not None else 1e9,
                                       r["resource_id"]))


@lru_cache(maxsize=1)
def text_rows() -> tuple[dict, ...]:
    """The text rows of all self-study resources: external_courses.csv, then resource_modules.csv."""
    return tuple(_read(paths.EXTERNAL_COURSES) + _read(paths.RESOURCE_MODULES))
