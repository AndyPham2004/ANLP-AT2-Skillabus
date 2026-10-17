"""Tests for the app's role helpers in app/backend.py (plan C3-C6). Run: pytest tests/

They read the committed data files (role_occupations.csv, occupation_skills.csv, skills_vocabulary.csv,
certifications.csv, resources.csv), so a rebuilt file that breaks the app fails here first.
"""
import csv
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.usefixtures("tfidf_only")   # TF-IDF per test (conftest): fast, the same on every machine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import backend  # noqa: E402
from skillabus import paths  # noqa: E402

FAMILIES = ["Data & AI", "Software", "Cloud & infrastructure", "Security", "Business analysis"]
# The four roles shown as core skills until JobsPipe gave them ad counts (C2); core_skills() stays as the
# fallback for a role with no counted block, and D9's priority list was made from these core skills.
CORE_ROLES = {"QA/Test Engineer", "DevOps/SRE", "Network/Systems Administrator", "Cybersecurity Analyst"}
RESUME = paths.SAMPLE_RESUME.read_text(encoding="utf-8")


def rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def all_roles():
    return [role for roles in backend.role_families().values() for role in roles]


def demand_meta(role="Data Scientist", source="jobspipe_2026"):
    """(source, period, total_ads, text_type) of a role's latest block in the committed demand table. Read, not
    typed: the JobsPipe counts are topped up (71 -> 89 Data Scientist ads on 17 Oct)."""
    block = [r for r in rows(paths.ROLE_SKILL_DEMAND) if r["role"] == role and r["source"] == source]
    r = max(block, key=lambda r: r["period"])
    return r["source"], r["period"], int(float(r["total_ads"])), r["text_type"]


# ---------------------------------------------------------------- C3: roles and where their demand comes from

def test_eleven_roles_in_five_families():
    families = backend.role_families()
    assert list(families) == FAMILIES
    assert len(all_roles()) == len(set(all_roles())) == 11
    assert families["Security"] == ["Cybersecurity Analyst"]


def test_role_source_takes_n_from_the_demand_table():
    totals = {r["role"]: int(r["total_ads"]) for r in rows(paths.ROLE_SKILL_DEMAND) if r["source"] == "jobspipe_2026"}
    for role in all_roles():
        text = backend.role_source(role)
        assert text == f"{totals[role]:,} JobsPipe {role} ads, Sep-Oct 2026, full text."
        assert backend.source_2019_22(role) == (                     # the trend column: Data Scientist only
            "3,204 Seek Data Scientist ads, 2019-22, full text." if role == "Data Scientist" else None)
    assert backend.source_2019_22(None) == backend.source_2019_22("Data Scientist")   # an ad: the Data Scientist ads
    # Home.py passes a gap row's demand_source and demand_period
    assert backend.role_source("Data Scientist", "seek_2019_22", "2019-22") == backend.source_2019_22("Data Scientist")


def test_a_role_without_a_counted_block_falls_back_to_core_skills(demand_sample):
    # The sample table gives QA/Test Engineer taxonomy rows only.
    assert not backend.has_ad_counts("QA/Test Engineer") and backend.has_ad_counts("Data Engineer")
    assert backend.role_source("QA/Test Engineer").startswith("No Australian ad counts yet: core skills of the ESCO occupation")
    assert backend.source_2019_22("QA/Test Engineer") is None
    skills = backend.role_gaps("QA/Test Engineer", [])
    assert skills == backend.core_skills("QA/Test Engineer", [])
    assert all(s["demand_pct"] is None and s["demand_pct_2019_22"] is None and s["total_ads"] is None
               and s["text_type"] is None for s in skills)


# ---------------------------------------------------------------- C5: core skills

def test_core_skills_are_onet_tools_then_essential_digital_esco_skills():
    # The occupations also list optional and non-digital ESCO skills that have core vocabulary rows
    # ("create incident reports", "C#" as optional), so the filter has something to drop.
    occ = rows(paths.OCCUPATION_SKILLS)
    vocab = {v["label"]: v for v in rows(paths.SKILLS_VOCABULARY)}
    for role in CORE_ROLES:
        found = backend.core_skill_rows(role)
        sources = [c["source"] for c in found]
        assert sources and sources == sorted(sources, key=lambda s: s != "onet")   # every O*NET tool before any ESCO skill
        allowed = {r["skill_ref"] for r in occ if r["role"] == role and r["source"] == "esco"
                   and r["importance"] == "essential" and r["esco_digital"] == "y"}
        for c in found:
            if c["source"] == "esco":
                assert vocab[c["label"]]["esco_uri"] in allowed, (role, c["label"])
    labels = [c["label"] for c in backend.core_skill_rows("Cybersecurity Analyst")]
    assert "building systems monitoring technology" not in labels
    assert "apply for research funding" not in [c["label"] for c in backend.core_skill_rows("Data Scientist")]


def test_core_skills_agree_with_the_self_study_priority_list():
    """D9 collected self-study resources for these 15; the app must show the same skills."""
    priority = rows(paths.PRIORITY_SKILLS)
    for role in CORE_ROLES:
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
    n = next(int(r["total_ads"]) for r in rows(paths.ROLE_SKILL_DEMAND)
             if r["role"] == "Data Engineer" and r["source"] == "jobspipe_2026")
    skills = backend.role_gaps("Data Engineer", [])
    assert len(skills) == 15 and all(s["demand_pct"] > 0 for s in skills)
    assert f"of {n} JobsPipe Data Engineer ads (Sep-Oct 2026)." in skills[0]["ad_evidence"]
    for role in CORE_ROLES:     # core skills until C2, counted ads now; certifications are not part of the 15
        skills = backend.role_gaps(role, [])
        assert len(skills) == 15 and all(s["demand_pct"] > 0 and s["text_type"] == "full_text" for s in skills)
        cert = {v["label"] for v in rows(paths.SKILLS_VOCABULARY) if v["category"] == "Certification"}
        assert not cert & {s["skill_label"] for s in skills}


def test_a_taken_subject_counts_as_having_the_skill():
    from skillabus.extract import load_dictionary
    from skillabus.recommend import subject_evidence
    code = subject_evidence(["Spark"], method="keyword")["Spark"][0]["subject_code"]
    # A skill other subjects name and this one does not (Kafka was no good: 94693 names it too).
    labels = [d["canonical"] for d in load_dictionary()]
    evidence = subject_evidence(labels, method="keyword")
    other = next(label for label in labels
                 if evidence.get(label) and code not in {e["subject_code"] for e in evidence[label]})
    skills = [{"skill_label": "Spark", "status": "missing", "resume_evidence": None},
              {"skill_label": other, "status": "missing", "resume_evidence": None}]
    out = backend.credit_taken(skills, [code])
    assert out[0]["status"] == "have" and out[0]["resume_evidence"].startswith(f"From {code}")
    assert out[1] == skills[1], other                                    # still missing, no evidence
    assert backend.credit_taken(skills, []) == skills


# ---------------------------------------------------------------- C6: certifications and self-study

def test_certifications_for_a_role_sorted_by_level():
    # Every certification of certifications.csv that names the role, foundational first, file order within a
    # level. The expected list is read from the file: D11 adds and re-counts certifications.
    table = rows(paths.CERTIFICATIONS)
    for role in all_roles():
        in_file = [r["cert"] for r in table if role in [x.strip() for x in r["roles"].split(";")]]
        certs = backend.certifications(role)
        assert certs, role
        assert sorted(c["cert"] for c in certs) == sorted(in_file), role       # none lost, none of another role
        levels = [backend.CERT_LEVELS.index(c["level"]) for c in certs]
        assert levels == sorted(levels), role
        for level in set(levels):
            same = [c["cert"] for c in certs if backend.CERT_LEVELS.index(c["level"]) == level]
            assert same == [name for name in in_file if name in same], role


def test_self_study_filters_by_level_and_cost():
    free = backend.self_study("Python", cost=backend.COST_CHOICES["Free only"], limit=50)
    assert free and all(r["cost"] == "free" for r in free)
    # Deep learning has resources at all three levels; Python has no advanced one, which made this check empty.
    advanced = backend.self_study("Deep learning", levels=("advanced",), cost=backend.COST_CHOICES["Include paid"],
                                  limit=50)
    assert advanced and all(r["level"] == "advanced" for r in advanced)
    assert len(backend.self_study("Python")) == backend.MAX_SELF_STUDY
    assert backend.self_study("Python", levels=()) == []


def test_self_study_puts_resources_about_the_skill_first():
    main = [r["skills"][0] == "Linux" for r in backend.self_study("Linux", limit=50)]
    assert True in main and False in main            # both kinds, or the order proves nothing
    assert main == sorted(main, reverse=True)        # every Linux course before any guide that only uses Linux


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
        assert {s["demand_source"] for s in result["skills"]} == {"jobspipe_2026"}
    by = {s["skill_label"]: s for s in result["skills"]}       # Cybersecurity Analyst
    assert by["Splunk"]["status"] == "missing" and by["Splunk"]["demand_pct"] > 0


def test_recommendations_list_each_subject_once():
    # #125: the strongest subject for a gap was appended again when it was already shown (in the path)
    # without covering that gap: 43008 twice for DevOps/SRE with TF-IDF, 48730 twice for
    # Cybersecurity Analyst with embeddings. This file runs TF-IDF (tfidf_only), so only the first case is checked.
    for role in ("DevOps/SRE", "Cybersecurity Analyst"):
        result, _ = backend.analyse(RESUME, None, [], role=role)
        codes = [r["subject_code"] for r in result["recommendations"]]
        assert len(codes) == len(set(codes)), (role, codes)


def test_footer_count_and_the_fallback_follow_the_vocabulary():
    # Follow-up to #109: the footer and the baseline fallback read the detection rows the extractor
    # uses (skills_vocabulary.csv), not the 148-skill seed.
    detection = [v for v in rows(paths.SKILLS_VOCABULARY) if "extract" in v["used_for"] and v["aliases_ads"].strip()]
    assert backend.dictionary_size() == len(detection) > 148
    found = backend.baseline.find_skills("Experience with Kubernetes, Terraform and Grafana dashboards.")
    assert {"Kubernetes", "Terraform", "Grafana"} <= set(found)            # Grafana: an IT skill added in D5
    skills = backend.baseline.analyse("", "Must know Tableau and Python.")["skills"]
    ids = {s["skill_label"]: s["skill_id"] for s in skills}
    assert ids["Tableau"] == "skillabus:tableau" and ids["Python"].startswith("esco:")


def test_analyse_job_mode_still_works():
    ad = paths.SAMPLE_AD.read_text(encoding="utf-8")
    result, engine = backend.analyse(RESUME, ad, [])           # no key (conftest): the app must run without one
    assert engine == "pipeline"
    assert result["role"] is None and result["skills"]
    assert "outside_recommendations" in result
    source, _, n_ads, _ = demand_meta()                        # a pasted ad is weighed by the Data Scientist ads
    assert {(s["demand_source"], s["total_ads"]) for s in result["skills"]} == {(source, n_ads)}
    # 17 Oct (#162): 31250 and 43007 are Bachelor-only subjects, closed to an MDSI student: they are dropped with
    # the reason and never on the path (before #162 the path was 31250, 43007, 36106 and covered LLMs).
    path, recs = result["learning_path"], {r["subject_code"]: r for r in result["recommendations"]}
    dropped = {d["subject_code"]: d["reason"] for d in path["dropped"]}
    assert not {"31250", "43007"} & set(path["subjects"])
    assert "43007" in dropped and "undergraduate" in dropped["43007"]
    assert all("undergraduate" in dropped[c] for c in ("31005", "41040") if c in dropped)
    weight = {s["skill_label"]: s["demand_pct"] + 1 for s in result["skills"] if s["status"] != "have"}
    closed = {c for code in path["subjects"] for c in recs.get(code, {}).get("covers", [])} & set(weight)
    # The "covers X% of the employer demand" line agrees with the gaps the path closes (+1 as recommend._weight).
    assert path["demand_covered_pct"] == round(100 * sum(weight[k] for k in closed) / sum(weight.values()), 1)


def test_llm_terms_outside_the_vocabulary_are_listed_apart_not_counted(monkeypatch):
    """17 Oct UI check: GPT added "business problems", "complex data" and the like, each counted as a missing
    skill ("28 of 29"). A GPT-only skill counts only when the vocabulary knows it; the rest are listed apart."""
    from skillabus import llm_extract

    found = [{"text": "LLMs", "kind": "hard", "method": "llm", "sentence": "Experience with LLMs."},
             {"text": "two-tower architectures", "kind": "hard", "method": "llm",
              "sentence": "Build two-tower architectures."}]
    monkeypatch.setattr(llm_extract, "extract_llm", lambda text, **kw: found if "LLMs" in text else [])
    ranked = []
    empty = {"skills": [], "recommendations": [], "learning_path": {}, "outside_recommendations": []}
    out = backend.augment_with_llm(empty, "I write Python.", "Experience with LLMs. Build two-tower architectures.",
                                   [], rank=lambda gaps: ranked.append([g["skill_label"] for g in gaps]) or {})
    assert [s["skill_label"] for s in out["skills"]] == ["Large language models"]
    assert out["also_in_ad"] == ["two-tower architectures"]
    assert ranked == [["Large language models"]]                  # the path never weighs an uncounted term


def test_llm_only_gaps_are_weighed_like_the_ad_s_other_skills(monkeypatch):
    """A skill only the GPT tier finds in an ad is weighed like the dictionary's rows: the 2026 Data Scientist
    share, with the 2019-22 trend."""
    from skillabus import llm_extract
    from skillabus.extract import extract
    from skillabus.match import match

    found = [{"text": "LLMs", "kind": "hard", "method": "llm", "sentence": "Experience with LLMs."}]
    monkeypatch.setattr(llm_extract, "extract_llm", lambda text, **kw: found if "LLMs" in text else [])
    empty = {"skills": [], "recommendations": [], "learning_path": {}, "outside_recommendations": []}
    out = backend.augment_with_llm(empty, "I write Python.", "Experience with LLMs.", [], rank=lambda gaps: {})
    row = next(s for s in out["skills"] if s["found_by"] == "llm")
    # the same skill found by the dictionary in the same sentence: every demand field must agree
    twin = next(s for s in match(extract("Experience with LLMs."), []) if s["skill_label"] == row["skill_label"])
    fields = ("demand_pct", "demand_pct_2026", "demand_pct_2019_22", "demand_source", "demand_period", "total_ads",
              "text_type")
    assert {k: row[k] for k in fields} == {k: twin[k] for k in fields}
    assert row["demand_pct"] > 0 and row["demand_pct_2019_22"] == 0.0      # in the 2026 ads, in none of 2019-22
    assert (row["demand_source"], row["demand_period"], row["total_ads"], row["text_type"]) == demand_meta()
