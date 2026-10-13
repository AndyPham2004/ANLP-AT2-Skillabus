"""Tests for emerging.py: proposing, scoring and filtering emerging-skill phrases.

Synthetic corpora: the real 2026 sample is 22 ads and changes as Van Thong adds ads.
"""
import pytest

import skillabus.emerging as emerging
from skillabus.emerging import Ad, detect, known_as, log_odds_z, ngrams, overlap, tokens


def ads(texts, employers=None):
    employers = employers or [f"E{i}" for i in range(len(texts))]
    return [Ad(str(i), e, t) for i, (t, e) in enumerate(zip(texts, employers))]


OLD = ads(["Experience with Python and SQL for reporting."] * 40
          + ["Python and statistics for forecasting."] * 40)
NEW = ads([
    "Experience with Python and agentic workflows in production.",
    "Python, SQL and agentic workflows; evaluation of models.",
    "You will build agentic workflows with Python.",
    "Python and SQL. We offer a wellness allowance.",
    "Python. We offer a wellness allowance.",
], employers=["A", "B", "C", "A", "A"])


@pytest.fixture(autouse=True)
def no_esco(monkeypatch):
    monkeypatch.setattr(emerging, "esco_phrases", lambda: frozenset({("evaluation",)}))


def test_tokens_keep_tool_names():
    assert tokens("C++, scikit-learn and GPT-4o’s A/B tests") == ["c++", "scikit-learn", "and", "gpt-4o's", "a/b", "tests"]
    assert ("agentic", "workflows") in ngrams(tokens("build agentic workflows with Python"))
    assert ("with", "python") not in ngrams(tokens("with Python"))          # no stop word at an edge


def test_log_odds_rises_with_the_new_count_and_shrinks_small_counts():
    assert log_odds_z(3, 5, 0, 80) > log_odds_z(1, 5, 0, 80) > 0
    assert log_odds_z(1, 5, 16, 80) == pytest.approx(log_odds_z(1, 5, 16, 80))
    assert abs(log_odds_z(1, 5, 16, 80)) < 1.96                          # same rate: not significant


def test_known_skills_and_esco_labels_are_not_emerging():
    assert known_as(("python",)) == "dictionary"
    assert known_as(("llms",)) == "dictionary"                           # alias "llm" + plural
    assert known_as(("evaluation",)) == "esco"
    assert known_as(("agentic", "workflows")) == ""


def test_detect_keeps_rising_phrases_from_several_employers():
    table = detect(("ngram",), new=NEW, old=OLD, top=10)
    phrases = [r["phrase"] for r in table]
    assert phrases[0] == "agentic workflows"                              # 3 ads, 3 employers, 0 before
    assert "agentic" not in phrases and "workflows" not in phrases        # nested, same ads
    assert "python" not in phrases and "sql" not in phrases               # dictionary skills
    assert "wellness allowance" not in phrases                            # one employer, no skill line
    row = table[0]
    assert (row["df_new"], row["employers_new"], row["df_2019_22"], row["rank"]) == (3, 3, 0, 1)
    assert row["is_skill"] == ""


def test_overlap_counts_shared_phrases():
    table = [{"method": "ngram", "phrase": "Agentic workflows"}, {"method": "spacy", "phrase": "agentic workflows"},
             {"method": "spacy", "phrase": "Neo4j"}]
    assert overlap(table) == {("ngram", "spacy"): 1}
