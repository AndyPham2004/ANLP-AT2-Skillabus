"""Tests for skillabus.rag.retrieve(). Run: pytest tests/test_rag.py

The embed backend's tests are skipped where sentence-transformers or faiss is not installed
(as on the deployed app); the tfidf backend runs everywhere.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from skillabus import rag  # noqa: E402

KEYS = {"text", "score", "source", "url", "subject_code", "subject_name", "layer", "method"}
EMBED = pytest.param("embed", marks=pytest.mark.skipif(
    not rag.embeddings_available(), reason="sentence-transformers or faiss not installed"))
METHODS = ["tfidf", EMBED]


@pytest.mark.parametrize("method", METHODS)
def test_result_shape(method):
    out = rag.retrieve("Which subject teaches deep learning?", k=5, method=method)
    assert 0 < len(out) <= 5
    assert all(KEYS <= set(r) for r in out)
    scores = [r["score"] for r in out]
    assert scores == sorted(scores, reverse=True)
    assert {r["method"] for r in out} == {method}


def test_source_reads_like_the_chat_fallback():
    """app/chat.py formats sources as '<code> <name> (<layer>)'; retrieve() must match."""
    r = rag.retrieve("large language models", k=1, method="tfidf")[0]
    assert re.fullmatch(r"\d{5} .+ \((learning objective|assessment|topic|description)\)", r["source"])
    assert r["url"].startswith("https://")


@pytest.mark.parametrize("method", METHODS)
def test_subject_code_in_question_restricts_results(method):
    out = rag.retrieve("What does 36118 teach?", k=5, method=method)
    assert out
    assert {r["subject_code"] for r in out} == {"36118"}


@pytest.mark.parametrize("method", METHODS)
def test_off_topic_question_returns_nothing(method):
    assert rag.retrieve("best pizza recipe in Naples", k=5, method=method) == []


def test_an_alias_in_the_question_is_spelled_out():
    # The chat's first suggested question. The embedding model reads "LLMs" as "LMS" (17 Oct UI check).
    # In place: a leftover "LLMs" still pulled the LMS exam into the top five.
    assert rag.spell_out("Which subject teaches LLMs?") == "Which subject teaches Large language models?"
    assert rag.spell_out("What does 36118 cover?") == "What does 36118 cover?"     # nothing to spell out
    assert rag.spell_out("deep learning subjects") == "deep learning subjects"     # already the full name


@pytest.mark.parametrize("method", METHODS)
def test_an_acronym_question_finds_the_subject_that_teaches_it(method):
    out = rag.retrieve("Which subject teaches LLMs?", k=3, method=method)
    assert "36118" in {r["subject_code"] for r in out}, [r["source"] for r in out]


def test_empty_question_or_zero_k():
    assert rag.retrieve("") == []
    assert rag.retrieve("deep learning", k=0) == []


@pytest.mark.parametrize("method", METHODS)
def test_sanity_questions_find_the_right_subject(method):
    table = rag.sanity_check(method)
    assert table["rank"].notna().sum() >= len(table) - 1, table.to_string()


def test_no_duplicate_passages():
    out = rag.retrieve("machine learning", k=10, method="tfidf")
    keys = [(r["subject_code"], r["text"]) for r in out]
    assert len(keys) == len(set(keys))


def test_ads_are_opt_in():
    subjects_only = rag.retrieve("experience with Spark and Hadoop", k=5, method="tfidf")
    assert all(r["layer"] != "ad" for r in subjects_only)
    with_ads = rag.retrieve("experience with Spark and Hadoop", k=5, method="tfidf",
                            sources=("subjects", "ads"))
    ads = [r for r in with_ads if r["layer"] == "ad"]
    assert ads and all(r["source"].startswith("Seek ad: ") for r in ads)


def test_ad_corpus_skill_pattern_follows_the_vocabulary():
    # Follow-up to #109: the pattern that keeps an ad sentence comes from the extractor's rows.
    rx = rag._skill_pattern()
    assert rx.search("Grafana dashboards") and rx.search("kubernetes clusters")   # vocabulary-only skills
    assert rx.search("SAS and SQL").group() == "SAS"                              # a strict row, as written
    assert not rx.search("saas and sas-like products")                            # ... and only as written


def test_unknown_method_is_an_error():
    with pytest.raises(ValueError):
        rag.retrieve("deep learning", method="bm25")
