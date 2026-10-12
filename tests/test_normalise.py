"""Normalisation rules that do not depend on the embedding model (runs without data/raw)."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ["SKILLABUS_NO_EMBED"] = "1"
os.environ.pop("LIGHTCAST_CLIENT_ID", None)

from skillabus.normalise import key, normalise  # noqa: E402


def norm(*phrases):
    return {r["text"]: r for r in normalise([{"text": p, "method": "llm", "sentence": p} for p in phrases])}


def test_key_ignores_case_brackets_and_punctuation():
    assert key("Python (computer programming)") == "python"
    assert key("Problem-Solving") == "problem solving"
    assert key("C++") == "c++"


def test_dictionary_alias_with_esco_link():
    r = norm("python")["python"]
    assert r["vocab"] == "esco" and r["canonical"] == "Python" and r["skill_id"].startswith("esco:")


def test_known_non_esco_skills_become_emerging_not_a_wrong_concept():
    r = norm("GenAI", "LLM")
    assert r["GenAI"]["vocab"] == "emerging" and r["GenAI"]["skill_label"] == "Generative AI"
    assert r["LLM"]["vocab"] == "emerging" and r["LLM"]["skill_label"] == "Large language models"


def test_spark_is_not_linked_to_the_esco_java_framework():
    r = norm("PySpark")["PySpark"]
    assert r["vocab"] == "seed" and r["skill_label"] == "Spark"


def test_unknown_phrase_is_kept_as_emerging():
    r = norm("agentic AI")["agentic AI"]
    assert r["vocab"] == "emerging" and r["skill_id"] == "emerging:agentic-ai"


def test_every_mention_comes_back_with_the_contract_fields():
    for r in norm("SQL", "stakeholder management", "agentic AI").values():
        assert {"skill_id", "skill_label", "vocab", "method", "sentence", "how"} <= set(r)


def test_canonical_from_extract_is_kept():
    # Tier 2 matches "REST APIs" to API development although the alias list lacks the plural.
    r = normalise([{"text": "REST APIs", "canonical": "API development", "method": "ner", "sentence": "x"}])[0]
    assert r["canonical"] == "API development" and r["vocab"] != "emerging"


def test_csharp_row_survives_reading_the_seed():
    r = norm("C#")["C#"]
    assert r["canonical"] == "C#"
