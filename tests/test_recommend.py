"""Tests for recommend() and the learning path. Run: pytest tests/

They read tests/fixtures/subject_profiles_sample.csv: the 2026 Handbook rows of the 19 MDSI
subjects and 12 others, taken from app/mock/subject_layers.csv, and the prerequisites and
teaching periods of the same 31 subjects (prerequisites_sample.csv, offerings_sample.csv, cut
from the 13 Oct scrape). Demand weights are pinned, so the tests do not move when
skill_counts_2026.csv is rebuilt.
"""
from pathlib import Path

import numpy as np
import pytest

import skillabus.recommend as recommend_module
import skillabus.requisites as requisites_module
import skillabus.similarity as similarity_module
from skillabus.extract import extract
from skillabus.match import match
from skillabus.recommend import MAX_PATH, _weight, learning_path, recommend, subject_evidence
from skillabus.requisites import Rules
from skillabus.similarity import embeddings_available

ROOT = Path(__file__).resolve().parents[1]
PROFILES = str(ROOT / "tests/fixtures/subject_profiles_sample.csv")
AD = (ROOT / "tests/fixtures/ad_rw_2026-09-23.txt").read_text(encoding="utf-8")
RESUME = (ROOT / "tests/fixtures/resume_synthetic.txt").read_text(encoding="utf-8")
START = ("Autumn", 2027)
# The 2026 lower bounds as of 13 Oct (22 ads). Pinned: the real file grows as Van Thong adds ads.
DEMAND_2026_LOW = {"Large language models": 19.7, "Generative AI": 10.1, "Artificial intelligence": 72.2}


@pytest.fixture(autouse=True)
def sample_data(monkeypatch):
    monkeypatch.setattr(requisites_module, "PREREQUISITES_CSV", ROOT / "tests/fixtures/prerequisites_sample.csv")
    monkeypatch.setattr(requisites_module, "OFFERINGS_CSV", ROOT / "tests/fixtures/offerings_sample.csv")
    monkeypatch.setattr(recommend_module, "demand_2026_low", lambda: DEMAND_2026_LOW)
    monkeypatch.setattr(recommend_module, "EXTERNAL_CSV", ROOT / "tests/fixtures/external_courses_sample.csv")


def gap(label, demand=10.0, demand_2026=None):
    return {"skill_label": label, "status": "missing", "demand_pct": demand, "demand_pct_2026": demand_2026}


def poster_gaps():
    return [s for s in match(extract(AD), extract(RESUME)) if s["status"] != "have"]


def covering(result, label):
    return [r["subject_code"] for r in result["recommendations"] if label in r["covers"]]


# ------------------------------------------------------------------------------- shape

@pytest.mark.parametrize("method", ["keyword", "tfidf"])
def test_result_follows_the_data_contract(method):
    gaps = poster_gaps()
    result = recommend(gaps, PROFILES, method=method)
    assert set(result) == {"recommendations", "learning_path", "outside_recommendations"}
    labels = {g["skill_label"] for g in gaps}
    for rec in result["recommendations"]:
        assert {"subject_code", "subject_name", "source_url", "score", "covers", "evidence", "needs", "offered",
                "unverified"} == set(rec)
        assert 0 <= rec["score"] <= 1.0 and set(rec["covers"]) <= labels
        assert rec["score"] > 0 or not rec["covers"]          # score 0 only for a prerequisite the path adds
        assert [e["skill_label"] for e in rec["evidence"]] == rec["covers"]
        assert all(e["layer"] in ("learning_objective", "assessment", "weekly_topic", "description")
                   and e["text"] for e in rec["evidence"])
    assert max(rec["score"] for rec in result["recommendations"]) == 1.0
    path = result["learning_path"]
    assert set(path) == {"subjects", "gaps_closed", "gaps_total", "demand_covered_pct", "plan", "dropped", "outside"}
    assert len(path["subjects"]) <= MAX_PATH and path["gaps_total"] == len(gaps)
    assert sorted(step["subject_code"] for step in path["plan"]) == sorted(path["subjects"])
    assert all({"subject_code", "subject_name", "reason", "covers"} == set(d) for d in path["dropped"])
    assert path["subjects"] == [r["subject_code"] for r in result["recommendations"]][:len(path["subjects"])]


def test_no_gaps_and_bad_inputs():
    assert recommend([], PROFILES) == {"recommendations": [], "outside_recommendations": [], "learning_path": {
        "subjects": [], "gaps_closed": 0, "gaps_total": 0, "demand_covered_pct": 0.0, "plan": [], "dropped": [],
        "outside": {"courses": [], "gaps_closed": 0, "gaps_open_before": 0, "still_open": [], "demand_covered_pct": 0.0}}}
    with pytest.raises(ValueError):
        recommend([gap("Deep learning")], PROFILES, method="bm25")
    with pytest.raises(FileNotFoundError):
        recommend([gap("Deep learning")], "data/processed/no_such_file.csv", method="keyword")


# ---------------------------------------------------------------------------- evidence

def test_the_subject_about_the_skill_beats_a_subject_that_mentions_it():
    """94691 Deep Learning names it in the title and many rows; 36118 has one weekly topic."""
    ranked = [e["subject_code"] for e in subject_evidence(["Deep learning"], PROFILES, "keyword")["Deep learning"]]
    assert ranked[0] == "94691"
    assert ranked.index("94691") < ranked.index("36118")


def test_one_passing_mention_does_not_cover_a_skill():
    """32130's 'collaboration with AI tools' is evidence, but far weaker than the AI subjects."""
    evidence = subject_evidence(["Artificial intelligence"], PROFILES, "keyword")["Artificial intelligence"]
    assert "32130" in [e["subject_code"] for e in evidence]
    result = recommend([gap("Artificial intelligence", 22.5)], PROFILES, method="keyword")
    assert "32130" not in covering(result, "Artificial intelligence")
    assert covering(result, "Artificial intelligence")[0] == "36121"


def test_evidence_is_the_strongest_layer_and_says_how_it_matched():
    best = subject_evidence(["Large language models"], PROFILES, "keyword")["Large language models"]
    by_code = {e["subject_code"]: e for e in best}
    assert by_code["36118"]["text"] == "Large Language Models (LLMs)"
    assert (by_code["36118"]["layer"], by_code["36118"]["match"]) == ("weekly_topic", "named")


def test_skill_outside_the_dictionary_is_searched_as_a_phrase():
    result = recommend([gap("fuzzy logic", 0.0)], PROFILES, method="keyword")
    assert covering(result, "fuzzy logic") == ["49275"]


def test_taken_subjects_are_excluded():
    assert "94691" in covering(recommend([gap("Deep learning")], PROFILES, method="keyword"), "Deep learning")
    result = recommend([gap("Deep learning")], PROFILES, method="keyword", exclude={"94691"})
    assert "94691" not in [r["subject_code"] for r in result["recommendations"]]


def test_similar_rows_count_with_embeddings(monkeypatch, tmp_path):
    """A row that never names the skill is found by meaning; the keyword method misses it."""
    profiles = tmp_path / "profiles.csv"
    profiles.write_text(
        "subject_code,subject_name,course,layer,text,source_url,collected_by\n"
        "11111,Charts for Everyone,C00001,learning_objective,Communicate findings with charts and plots,u,t\n"
        "22222,Tax Law,C00001,learning_objective,Interpret the income tax assessment act,u,t\n", encoding="utf-8")

    def fake_embed(texts):
        visual = ("visualis", "chart", "plot")
        return np.array([[1.0, 0.0] if any(w in t.lower() for w in visual) else [0.0, 1.0] for t in texts])

    monkeypatch.setattr(similarity_module, "embed", fake_embed)
    assert recommend([gap("Data visualisation")], str(profiles), method="keyword")["recommendations"] == []
    (rec,) = recommend([gap("Data visualisation")], str(profiles), method="embed")["recommendations"]
    assert rec["subject_code"] == "11111" and rec["evidence"][0]["match"] == "similar"


# ----------------------------------------------------------------------- learning path

def test_learning_path_for_the_poster_ad():
    """The Robert Walters ad: machine learning (72% of ads) first; 43023 teaches AI and LLMs but
    needs 42172 or 41040, which an MDSI student cannot take, so it is dropped with the reason."""
    result = recommend(poster_gaps(), PROFILES, method="keyword", start=START)
    path = result["learning_path"]
    assert path["subjects"] == ["36106", "32130", "36121"]
    assert path["gaps_closed"] == 5 and path["gaps_total"] == 6
    assert 85 < path["demand_covered_pct"] < 100             # large language models stay open
    dropped = {d["subject_code"]: d for d in path["dropped"]}
    assert "42172" in dropped["43023"]["reason"] and "Large language models" in dropped["43023"]["covers"]
    assert "43023" not in [r["subject_code"] for r in result["recommendations"]]
    assert [step["session"] for step in path["plan"]] == ["Autumn 2027"] * 3


def test_a_student_who_took_the_core_can_take_36118():
    """36118 needs 36100, 36103 and 36106: closed for a new student, open once they are taken."""
    llm = [gap("Large language models", 0.0)]
    new = recommend(llm, PROFILES, method="keyword", start=START)
    assert "36118" in [d["subject_code"] for d in new["learning_path"]["dropped"]]
    taken = recommend(llm, PROFILES, method="keyword", exclude={"36100", "36103", "36106"}, start=START)
    assert taken["learning_path"]["subjects"] == ["36118"]


def test_a_prerequisite_is_added_before_the_subject(monkeypatch):
    """Deep learning only in 94691, which needs 36106: the path takes both, 36106 a session earlier."""
    monkeypatch.setattr(recommend_module, "subject_evidence", lambda labels, *a, **k: {
        "Deep learning": [{"subject_code": "94691", "subject_name": "Deep Learning", "source_url": "", "strength": 1.4,
                           "layer": "learning_objective", "text": "Deep learning", "match": "named", "similarity": 1.0}]})
    path = recommend([gap("Deep learning", 16.1)], PROFILES, method="keyword", start=START)["learning_path"]
    assert path["subjects"] == ["36106", "94691"]
    assert [(s["subject_code"], s["session"], s["after"]) for s in path["plan"]] == [
        ("36106", "Autumn 2027", []), ("94691", "Autumn 2028", ["36106"])]     # 94691 runs in Autumn only


def test_without_requisite_data_every_subject_is_open():
    result = recommend(poster_gaps(), PROFILES, method="keyword", rules=Rules())
    assert "43023" in result["learning_path"]["subjects"] and result["learning_path"]["dropped"] == []


def test_a_step_with_a_prerequisite_is_valued_per_place():
    weight = {"a": 30.0, "b": 25.0}
    covers = {"S1": {"a"}, "S2": {"a", "b"}, "P": set()}
    needs = {"S1": set(), "S2": {"P"}, "P": set()}
    path = learning_path(covers, weight, {}, needs=lambda code, done: needs[code] - done)
    assert path["subjects"] == ["S1", "P", "S2"]           # 30 for one place beats 55 for two
    assert learning_path(covers, weight, {}, max_subjects=1,
                         needs=lambda code, done: needs[code] - done)["subjects"] == ["S1"]
    assert learning_path(covers, weight, {}, needs=lambda code, done: None)["subjects"] == []


# ------------------------------------------------------------------ second tier: outside

def test_outside_courses_close_what_the_uts_path_leaves_open():
    """Large language models: no UTS subject a new MDSI student can take; the Hugging Face course."""
    result = recommend(poster_gaps(), PROFILES, method="keyword", start=START)
    path, outside = result["learning_path"], result["learning_path"]["outside"]
    assert outside["gaps_open_before"] == 1 and outside["courses"] == ["EXT-HF-LLM"]
    assert outside["still_open"] == [] and path["demand_covered_pct"] < outside["demand_covered_pct"] == 100.0
    first = result["outside_recommendations"][0]
    assert (first["subject_code"], first["cost"], first["covers"]) == ("EXT-HF-LLM", "free", ["Large language models"])
    assert {"provider", "cost", "source_url", "evidence", "score"} <= set(first)
    # Outside courses only see the open gaps: none of them covers a skill the UTS path closed.
    closed_by_uts = {k for r in result["recommendations"] if r["subject_code"] in path["subjects"] for k in r["covers"]}
    assert not closed_by_uts & {k for r in result["outside_recommendations"] for k in r["covers"]}


def test_at_most_three_outside_courses_and_none_without_the_file():
    gaps = [gap(label, 0.0) for label in ("Large language models", "PyTorch", "scikit-learn", "Prompt engineering")]
    outside = recommend(gaps, PROFILES, method="keyword", start=START)["learning_path"]["outside"]
    assert 1 <= len(outside["courses"]) <= 3
    none = recommend(poster_gaps(), PROFILES, method="keyword", start=START, external_csv="")
    assert none["outside_recommendations"] == [] and none["learning_path"]["outside"]["courses"] == []
    assert none["learning_path"]["outside"]["demand_covered_pct"] == none["learning_path"]["demand_covered_pct"]


def test_greedy_takes_the_largest_uncovered_demand_first():
    weight = {"a": 50.0, "b": 30.0, "c": 20.0, "d": 1.0}
    covers = {"S1": {"a"}, "S2": {"b", "c"}, "S3": {"a", "b"}, "S4": {"d"}}
    path = learning_path(covers, weight, score={})
    assert path["subjects"] == ["S3", "S2", "S4"]            # 80, then 20 (c is all S2 adds), then 1
    assert (path["gaps_closed"], path["gaps_total"], path["demand_covered_pct"]) == (4, 4, 100.0)


def test_greedy_stops_at_three_subjects_or_when_nothing_is_gained():
    weight = {k: 10.0 for k in "abcde"}
    assert len(learning_path({f"S{k}": {k} for k in "abcde"}, weight, {})["subjects"]) == 3
    assert learning_path({"S1": {"a"}, "S2": {"a"}}, weight, {})["subjects"] == ["S1"]
    assert learning_path({}, weight, {}) == {"subjects": [], "gaps_closed": 0, "gaps_total": 5, "demand_covered_pct": 0.0}


def test_ties_go_to_the_higher_scoring_subject():
    weight = {"a": 10.0}
    assert learning_path({"S1": {"a"}, "S2": {"a"}}, weight, {"S1": 0.2, "S2": 0.9})["subjects"] == ["S2"]


def test_a_zero_demand_skill_still_gets_a_subject():
    result = recommend([gap("Large language models", 0.0)], PROFILES, method="keyword", exclude={"36100", "36103", "36106"})
    assert result["learning_path"]["subjects"] and result["learning_path"]["demand_covered_pct"] == 100.0


def test_weight_uses_the_low_end_of_the_2026_interval(monkeypatch):
    monkeypatch.setattr(recommend_module, "demand_2026_low", lambda: {"Large language models": 18.0, "Hadoop": 1.0})
    assert _weight(gap("Large language models", 0.0, 36.4)) == 19.0     # 2026 lower bound, not 36.4
    assert _weight(gap("Hadoop", 17.4, 4.5)) == 18.4                    # 2019-22 is higher
    monkeypatch.setattr(recommend_module, "demand_2026_low", lambda: {"Artificial intelligence": 72.2})
    assert _weight(gap("Artificial intelligence", 22.5, 90.9)) == 23.5  # asked for before 2023: 2019-22 stays
    assert _weight(gap("Python", 82.8)) == 83.8                         # no 2026 row


# ------------------------------------------------- real embedding model, when installed

@pytest.mark.skipif(not embeddings_available(), reason="sentence-transformers model not available")
def test_recommend_runs_with_the_real_embedding_model():
    result = recommend(poster_gaps(), PROFILES, method="embed")
    assert result["learning_path"]["gaps_closed"] >= 4
    assert "36106" in [r["subject_code"] for r in result["recommendations"]]
