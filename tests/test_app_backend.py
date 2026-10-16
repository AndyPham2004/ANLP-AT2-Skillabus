"""Tests for the app's role helpers in app/backend.py (plan C3-C6). Run: pytest tests/

They read the committed data files (role_occupations.csv, occupation_skills.csv, skills_vocabulary.csv,
certifications.csv, resources.csv), so a rebuilt file that breaks the app fails here first.
"""
import csv
import os
import sys
from pathlib import Path

os.environ.setdefault("SKILLABUS_NO_EMBED", "1")   # TF-IDF: fast, and the same on every machine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import backend  # noqa: E402
from skillabus import paths  # noqa: E402

FAMILIES = ["Data & AI", "Software", "Cloud & infrastructure", "Security", "Business analysis"]
NO_COUNTS = {"QA/Test Engineer", "DevOps/SRE", "Network/Systems Administrator", "Cybersecurity Analyst"}
RESUME = paths.SAMPLE_RESUME.read_text(encoding="utf-8")


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def all_roles():
    return [role for roles in backend.role_families().values() for role in roles]


# ---------------------------------------------------------------- C3: roles and where their demand comes from

def test_eleven_roles_in_five_families():
    families = backend.role_families()
    assert list(families) == FAMILIES
    assert len(all_roles()) == len(set(all_roles())) == 11
    assert families["Security"] == ["Cybersecurity Analyst"]


def test_seven_roles_have_ad_counts():
    assert {r for r in all_roles() if not backend.has_ad_counts(r)} == NO_COUNTS


def test_role_source_takes_n_from_the_files():
    totals = {r["role"]: int(r["total_ads"]) for r in rows(paths.ROLE_PROFILES)}
    for role in all_roles():
        text = backend.role_source(role)
        if role == "Data Scientist":
            assert text == "3,204 Seek Data Scientist ads 2019-22, full text."
        elif role in NO_COUNTS:
            esco, onet = backend.occupation(role, "esco"), backend.occupation(role, "onet")
            assert text.startswith("No Australian ad counts yet: core skills of the ESCO occupation")
            assert esco["occupation_title"] in text and onet["occupation_code"] in text
        else:
            assert text == f"{totals[role]:,} Australian {role} postings 2023 (data_jobs, the tools each ad lists)."


# ---------------------------------------------------------------- C5: core skills

def test_core_skills_are_vocabulary_core_rows_onet_first():
    core = {v["label"] for v in rows(paths.SKILLS_VOCABULARY) if "core_skill" in v["used_for"]}
    for role in NO_COUNTS:
        found = backend.core_skill_rows(role)
        labels = [c["label"] for c in found]
        assert labels and len(labels) == len(set(labels))
        assert set(labels) <= core
        sources = [c["source"] for c in found]
        assert sources == sorted(sources, key=lambda s: s != "onet")      # every O*NET tool before any ESCO skill


def test_core_skills_keep_only_essential_digital_esco_skills():
    occ = rows(paths.OCCUPATION_SKILLS)
    vocab = {v["label"]: v for v in rows(paths.SKILLS_VOCABULARY)}
    for role in NO_COUNTS:
        allowed = {r["skill_ref"] for r in occ if r["role"] == role and r["source"] == "esco"
                   and r["importance"] == "essential" and r["esco_digital"] == "y"}
        for c in backend.core_skill_rows(role):
            if c["source"] == "esco":
                assert vocab[c["label"]]["esco_uri"] in allowed
    labels = [c["label"] for c in backend.core_skill_rows("Cybersecurity Analyst")]
    assert "building systems monitoring technology" not in labels
    assert "apply for research funding" not in [c["label"] for c in backend.core_skill_rows("Data Scientist")]


def test_core_skills_agree_with_the_self_study_priority_list():
    """D9 collected self-study resources for these 15; the app must show the same skills."""
    priority = rows(paths.PRIORITY_SKILLS)
    for role in NO_COUNTS:
        expected = [r["skill"] for r in priority if r["role"] == role]
        shown = [s["skill_label"] for s in backend.core_skills(role, [])]
        # Same 15 skills; D9 put "cyber security" in the 13th slot after dropping the building-systems one.
        assert set(shown) == set(expected) and len(shown) == len(expected)
    assert backend.self_study("cyber security", role="Cybersecurity Analyst")     # D9 added two courses for it


def test_core_skills_compare_with_the_resume_without_percentages():
    resume = [{"text": "python", "canonical": "Python", "skill_label": "Python (computer programming)",
               "sentence": "Python: pandas for data cleaning."},
              {"text": "Linux", "canonical": "Linux", "skill_label": "Linux", "sentence": "Ran Linux servers."}]
    skills = backend.core_skills("Cybersecurity Analyst", resume)
    by = {s["skill_label"]: s for s in skills}
    assert len(skills) == backend.MAX_CORE_SKILLS
    assert by["Python"]["status"] == "have" and by["Python"]["resume_evidence"] == "Python: pandas for data cleaning."
    assert by["Linux"]["status"] == "have"
    assert by["Splunk"]["status"] == "missing" and by["Splunk"]["resume_evidence"] is None
    assert all(s["demand_pct"] is None for s in skills)
    assert "O*NET" in by["Splunk"]["ad_evidence"]


def test_role_gaps_uses_match_role_for_roles_with_counts():
    skills = backend.role_gaps("Data Engineer", [])
    assert len(skills) == 15 and all(s["demand_pct"] > 0 for s in skills)
    assert "4,438" in skills[0]["ad_evidence"]


def test_a_taken_subject_counts_as_having_the_skill():
    from skillabus.recommend import subject_evidence
    code = subject_evidence(["Spark"], method="keyword")["Spark"][0]["subject_code"]
    skills = [{"skill_label": "Spark", "status": "missing", "resume_evidence": None},
              {"skill_label": "Kafka", "status": "missing", "resume_evidence": None}]
    out = backend.credit_taken(skills, [code])
    assert out[0]["status"] == "have" and out[0]["resume_evidence"].startswith(f"From {code}")
    assert backend.credit_taken(skills, []) == skills


# ---------------------------------------------------------------- C6: certifications and self-study

def test_certifications_for_a_role_sorted_by_level():
    for role in all_roles():
        certs = backend.certifications(role)
        assert certs, role
        assert all(role in backend._split(c["roles"]) for c in certs)
        levels = [backend.CERT_LEVELS.index(c["level"]) for c in certs]
        assert levels == sorted(levels)
    assert len(backend.certifications("Cybersecurity Analyst")) == 10
    assert backend.certifications("Cybersecurity Analyst")[0]["cert"] == "ISC2 Certified in Cybersecurity (CC)"


def test_self_study_filters_by_level_and_cost():
    free = backend.self_study("Python", cost=backend.COST_CHOICES["Free only"], limit=50)
    assert free and all(r["cost"] == "free" for r in free)
    advanced = backend.self_study("Python", levels=("advanced",), cost=backend.COST_CHOICES["Include paid"], limit=50)
    assert all(r["level"] == "advanced" for r in advanced)
    assert len(backend.self_study("Python")) == backend.MAX_SELF_STUDY
    assert backend.self_study("Python", levels=()) == []


def test_self_study_puts_resources_about_the_skill_first():
    hits = backend.self_study("Linux", limit=50)
    first_not_main = next((i for i, r in enumerate(hits) if r["skills"][0] != "Linux"), len(hits))
    assert all(r["skills"][0] == "Linux" for r in hits[:first_not_main])
    assert all(r["skills"][0] != "Linux" for r in hits[first_not_main:])


def test_self_study_falls_back_to_any_role():
    # A resource tagged only for other roles still teaches the skill.
    assert backend.self_study("Python", role="No such role")


# ---------------------------------------------------------------- C4: analyse in role mode

def test_analyse_role_mode_runs_the_pipeline_with_the_second_tier():
    for role in ("Data Engineer", "Cybersecurity Analyst"):
        result, engine = backend.analyse(RESUME, None, [], role=role)
        assert engine == "pipeline"
        assert result["role"] == role and len(result["skills"]) == 15
        assert "outside_recommendations" in result and "outside" in result["learning_path"]
    by = {s["skill_label"]: s for s in result["skills"]}       # Cybersecurity Analyst
    assert by["Python"]["status"] == "have" and by["Splunk"]["status"] == "missing"


def test_analyse_job_mode_still_works(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)     # no GPT tier: the app must run without a key
    ad = paths.SAMPLE_AD.read_text(encoding="utf-8")
    result, engine = backend.analyse(RESUME, ad, [])
    assert engine.startswith("pipeline")
    assert result["role"] is None and result["skills"]
    assert "outside_recommendations" in result


def test_llm_only_gaps_keep_the_2026_trend(monkeypatch):
    """A skill only the GPT tier finds in an ad is weighted like the dictionary's rows: Seek share, 2026 trend."""
    from skillabus import llm_extract
    from skillabus.match import _demand_2026

    found = [{"text": "LLMs", "kind": "hard", "method": "llm", "sentence": "Experience with LLMs."}]
    monkeypatch.setattr(llm_extract, "extract_llm", lambda text, **kw: found if "LLMs" in text else [])
    empty = {"skills": [], "recommendations": [], "learning_path": {}, "outside_recommendations": []}
    out = backend.augment_with_llm(empty, "I write Python.", "Experience with LLMs.", [], rank=lambda gaps: {})
    row = next(s for s in out["skills"] if s["found_by"] == "llm")
    assert row["demand_pct_2026"] == _demand_2026().get(row["skill_label"])
    assert row["demand_pct_2026"] is not None
    assert (row["demand_source"], row["demand_period"]) == ("Seek", "2019-22")
