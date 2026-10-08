"""Tests for match(), soft_skills(), role_profile() and score_matrix(). Run: pytest tests/"""
import csv
from pathlib import Path

import pytest

from skillabus.extract import extract
from skillabus.match import match, role_profile, score_matrix, skill_overlap, soft_skills
from skillabus.similarity import embeddings_available, similarity

ROOT = Path(__file__).resolve().parents[1]
AD = (ROOT / "tests/fixtures/ad_rw_2026-09-23.txt").read_text(encoding="utf-8")
RESUME = (ROOT / "tests/fixtures/resume_synthetic.txt").read_text(encoding="utf-8")
CONTRACT_KEYS = {"skill_id", "skill_label", "status", "demand_pct", "demand_pct_2026",
                 "emerging", "ad_evidence", "resume_evidence"}


def mention(text, canonical=None, sentence=None, **extra):
    return {"text": text, "canonical": canonical, "method": "dictionary",
            "sentence": sentence or f"Experience with {text} in production systems.", **extra}


def status(skills):
    return {s["skill_label"]: s["status"] for s in skills}


# ------------------------------------------------------------------------ the poster case

def test_gap_result_follows_the_data_contract():
    skills = match(extract(AD), extract(RESUME))
    for s in skills:
        assert CONTRACT_KEYS <= set(s) <= CONTRACT_KEYS | {"related_skill", "found_by"}
        assert s["status"] in ("have", "partial", "missing")
        assert (s["resume_evidence"] is None) == (s["status"] == "missing")


def test_reproduces_the_poster_gap_chart():
    """data/processed/gap.csv: 8 technical skills, the resume covers Python and SQL."""
    with open(ROOT / "data/processed/gap.csv", encoding="utf-8") as f:
        gap = list(csv.DictReader(line for line in f if not line.startswith("#")))
    skills = match(extract(AD), extract(RESUME))
    assert {s["skill_label"]: s["demand_pct"] for s in skills} == {r["skill"]: float(r["pct_ads"]) for r in gap}
    assert {s["skill_label"] for s in skills if s["status"] == "have"} == {r["skill"] for r in gap if r["covered"] == "1"}
    assert [s["demand_pct"] for s in skills] == sorted((s["demand_pct"] for s in skills), reverse=True)
    assert {s["skill_label"] for s in skills if s["emerging"]} == {"Large language models", "Generative AI"}


def test_soft_skills_are_listed_apart():
    ad = extract(AD)
    assert soft_skills(ad) == ["Teamwork", "Problem solving"]
    assert not {"Teamwork", "Problem solving"} & set(status(match(ad, extract(RESUME))))
    assert {"Teamwork", "Problem solving"} <= set(status(match(ad, extract(RESUME), include_soft=True)))


def test_evidence_is_a_sentence_not_the_title_line():
    python = next(s for s in match(extract(AD), extract(RESUME)) if s["skill_label"] == "Python")
    assert python["ad_evidence"].startswith("You will leverage your strong Python and SQL skills")
    assert python["resume_evidence"].startswith("Python: pandas and matplotlib")


# ------------------------------------------------------------------------------- partial

def test_umbrella_skill_is_partial_when_the_resume_shows_a_part_of_it():
    ad = extract("Solid machine learning and deep learning experience.")
    resume = extract("Built churn models with scikit-learn and XGBoost.")
    skills = match(ad, resume)
    assert status(skills) == {"Machine learning": "partial", "Deep learning": "missing"}
    ml = skills[0]
    assert ml["related_skill"] in ("scikit-learn", "XGBoost")
    assert ml["resume_evidence"] == "Built churn models with scikit-learn and XGBoost."


def test_another_programming_language_is_not_partial():
    assert status(match(extract("Strong Python skills."), extract("Five years of Java and Scala."))) == {
        "Python": "missing"}


def test_substitute_tools_are_not_partial():
    """Embedding similarity could not tell substitutes apart (see match.py), so Power BI does not count for Tableau."""
    assert status(match(extract("Reporting in Tableau."), extract("Reports in Power BI."))) == {"Tableau": "missing"}


# ----------------------------------------------------- mentions from normalise() or the LLM

def test_skills_outside_the_dictionary_match_on_skill_id():
    agentic = dict(skill_id="emerging:agentic-ai", skill_label="agentic AI", vocab="emerging")
    ad = [mention("agentic AI", **agentic) | {"method": "llm"},
          mention("LangGraph", skill_id="emerging:langgraph", skill_label="LangGraph", vocab="emerging") | {"method": "llm"}]
    resume = [mention("Agentic AI", **agentic)]
    skills = match(ad, resume)
    assert status(skills) == {"agentic AI": "have", "LangGraph": "missing"}
    assert all(s["emerging"] and s["found_by"] == "llm" and s["demand_pct"] == 0.0 for s in skills)


def test_normalised_ids_and_labels_are_kept():
    esco = "esco:http://data.europa.eu/esco/skill/ccd0a1d9"
    ad = [mention("python", "Python", skill_id=esco, skill_label="Python (computer programming)", vocab="esco")]
    (skill,) = match(ad, [])
    assert (skill["skill_id"], skill["skill_label"], skill["emerging"]) == (esco, "Python", False)


def test_raw_mentions_get_a_seed_id():
    (skill,) = match(extract("Predictive modelling experience."), [])
    assert skill["skill_id"] == "seed:predictive-modelling"


def test_empty_inputs():
    assert match([], extract(RESUME)) == []
    assert status(match(extract("Python and SQL."), [])) == {"Python": "missing", "SQL": "missing"}


# --------------------------------------------------------------------- role and ranking

def test_role_profile_matches_like_an_ad():
    role = role_profile()
    assert len(role) == 15 and role[0]["canonical"] == "Python"
    skills = match(role, extract(RESUME))
    assert {k for k, v in status(skills).items() if v == "have"} == {"Python", "SQL", "Statistics", "Data visualisation"}
    assert skills[1]["ad_evidence"] == "Asked for in 72% of 3,204 Seek Data Scientist ads (2019-22)."


def test_skill_overlap_is_demand_weighted():
    ad = extract("Python and Tableau.")
    assert skill_overlap(ad, extract("Python.")) > skill_overlap(ad, extract("Tableau.")) > skill_overlap(ad, []) == 0.0
    assert skill_overlap(ad, ad) == 1.0


@pytest.mark.parametrize("method", ["tfidf", "skills"])
def test_score_matrix_ranks_the_fitting_ad_first(method):
    resumes = [RESUME, "Deep learning engineer. PyTorch, TensorFlow, computer vision, neural networks, Python."]
    ads = [AD, "BI analyst. SQL, Power BI dashboards, Excel, data visualisation, statistics for business stakeholders."]
    scores = score_matrix(resumes, ads, method)
    assert scores.shape == (2, 2)
    assert scores[0, 1] > scores[0, 0]      # the BI resume fits the BI ad better
    assert scores[1, 0] > scores[1, 1]      # the deep learning resume fits the data scientist ad better


def test_score_matrix_rejects_unknown_method():
    with pytest.raises(ValueError):
        score_matrix([RESUME], [AD], "bm25")


# ------------------------------------------------- real embedding model, when installed

needs_model = pytest.mark.skipif(not embeddings_available(), reason="sentence-transformers model not available")


@needs_model
def test_embeddings_see_meaning_not_words():
    sims = similarity(["deep learning"], ["neural networks and backpropagation", "stakeholder management"], "embed")[0]
    assert sims[0] > sims[1]
    assert similarity(["deep learning"], ["neural networks and backpropagation"], "tfidf")[0, 0] == 0.0


@needs_model
def test_score_matrix_with_embeddings_has_the_right_shape():
    assert score_matrix([RESUME], [AD, "Chef wanted for a busy kitchen."], "embed").shape == (1, 2)
