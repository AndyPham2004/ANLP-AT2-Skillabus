"""The self-study store (plan D9): resources.csv, resource_modules.csv, priority_skills.csv."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skillabus import paths, resources  # noqa: E402

ROLES = {"Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer", "Software Engineer",
         "QA/Test Engineer", "Cloud Engineer", "DevOps/SRE", "Network/Systems Administrator", "Cybersecurity Analyst",
         "Business Analyst"}
ALLOWED = {
    "provider_type": {"vendor", "university", "community", "platform"},
    "format": {"course", "official_docs", "hands_on_lab", "tutorial", "book"},
    "level": {"beginner", "intermediate", "advanced"},
    "cost": {"free", "free-to-audit", "paid"},
    "certificate": {"y", "n"},
}


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_fields_are_complete_and_valid():
    res = rows(paths.RESOURCES)
    assert len({r["resource_id"] for r in res}) == len(res)
    for r in res:
        for col, allowed in ALLOWED.items():
            assert r[col] in allowed, (r["resource_id"], col, r[col])
        float(r["hours"])
        assert r["url"].startswith("https://"), r["resource_id"]
        assert r["date_checked"] and r["title"] and r["provider"]
        assert (r["cost"] == "paid") == bool(r["cost_aud"]), r["resource_id"]
        assert set(r["roles"].split("; ")) <= ROLES, r["resource_id"]


def test_skills_are_vocabulary_labels():
    labels = {r["label"] for r in rows(paths.SKILLS_VOCABULARY)}
    for r in rows(paths.RESOURCES):
        skills = [s.strip() for s in r["skills"].split(";") if s.strip()]
        assert skills and set(skills) <= labels, (r["resource_id"], set(skills) - labels)


def test_every_resource_has_text_and_every_text_has_a_resource():
    ids = {r["resource_id"] for r in rows(paths.RESOURCES)}
    old = {r["subject_code"] for r in rows(paths.EXTERNAL_COURSES)}
    new = rows(paths.RESOURCE_MODULES)
    assert not old & {r["subject_code"] for r in new}            # one file per resource's text
    # Through text_rows(), which reads both files: a resource with no text row is never recommended.
    assert ids == {r["subject_code"] for r in resources.text_rows()}
    with_description = {r["subject_code"] for r in new if r["layer"] == "description"}
    assert {r["subject_code"] for r in new} <= with_description
    assert {r["layer"] for r in new} <= {"description", "weekly_topic"}


def test_every_priority_skill_has_two_options_and_a_beginner_one():
    for p in rows(paths.PRIORITY_SKILLS):
        found = resources.for_skill(p["skill"])
        assert len(found) >= 2, p["skill"]
        assert found[0]["level"] == "beginner", p["skill"]
    assert {p["role"] for p in rows(paths.PRIORITY_SKILLS)} == ROLES


def test_for_skill_filters_and_sorts():
    free = resources.for_skill("Docker", cost=("free",))
    assert free and all(r["cost"] == "free" for r in free)
    levels = [resources.LEVELS.index(r["level"]) for r in resources.for_skill("Python")]
    assert levels == sorted(levels)
    assert resources.for_skill("Docker", role="Business Analyst") == [
        r for r in resources.for_skill("Docker") if "Business Analyst" in r["roles"]]
