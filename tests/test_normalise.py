"""Normalisation rules that do not depend on the embedding model (runs without data/raw)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import skillabus.normalise as normalise_module  # noqa: E402
from skillabus.normalise import key, normalise  # noqa: E402


@pytest.fixture(autouse=True)
def rules_only(tfidf_only, monkeypatch, tmp_path):
    """No embedding model and no live Lightcast call, per test: set at import, both leaked into every later file.
    The Lightcast cache is emptied too: lightcast_lookup() reads a cached answer before it checks for a key."""
    monkeypatch.delenv("LIGHTCAST_CLIENT_ID", raising=False)
    monkeypatch.setattr(normalise_module, "LIGHTCAST_CACHE", tmp_path / "lightcast")


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


SPARK_JAVA = "http://data.europa.eu/esco/skill/af7ae54f-4649-4c16-87c7-59ba41d4d57f"   # ESCO "SPARK", a Java framework


def test_spark_is_not_linked_to_the_esco_java_framework():
    r = norm("PySpark")["PySpark"]
    assert r["vocab"] == "seed" and r["skill_label"] == "Spark"


def test_the_embedding_step_never_links_the_blocked_spark_concept(monkeypatch):
    """A phrase outside the vocabulary reaches the embedding step, where the nearest ESCO label can be "SPARK"."""
    def nearest(uri):
        return lambda phrases: [(uri, "SPARK", 0.99)] * len(phrases)

    phrase = "Spark Structured Streaming"
    monkeypatch.setattr(normalise_module, "esco_nearest", nearest("http://data.europa.eu/esco/skill/other"))
    assert norm(phrase)[phrase]["how"] == "esco_embed"                    # the stub is what normalise() calls
    monkeypatch.setattr(normalise_module, "esco_nearest", nearest(SPARK_JAVA))
    r = norm(phrase)[phrase]
    assert r["vocab"] == "emerging" and SPARK_JAVA not in r["skill_id"]


def test_a_mention_that_is_just_ai_is_the_ai_skill():
    """extract() no longer searches ad text for a bare 'AI' (#148), but when the GPT or spaCy tier
    returns 'AI' as a skill, the tier has already judged it one: it is Artificial intelligence."""
    r = norm("AI", "A.I.")
    assert r["AI"]["canonical"] == "Artificial intelligence" and r["AI"]["skill_id"].startswith("esco:")
    assert r["A.I."]["canonical"] == "Artificial intelligence"


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


def test_csharp_keeps_its_hash_sign():
    # read_csv(comment="#") once cut the row to "C"; and without "#" in the key, C# and C are one skill.
    r = norm("C#", "C")
    assert r["C#"]["canonical"] == "C#" and r["C"]["canonical"] == "C"


def test_vocabulary_skills_esco_lacks_are_seed_not_emerging():
    """Review #109: Kafka, MLflow and the certifications are known skills ESCO lacks; "emerging" is
    for phrases outside the vocabulary, plus generative AI and LLMs."""
    r = norm("Kafka", "MLflow", "AWS Certified Solutions Architect - Associate")
    assert r["Kafka"]["vocab"] == "seed" and r["Kafka"]["skill_id"] == "skillabus:kafka"
    assert r["MLflow"]["vocab"] == "seed" and r["MLflow"]["skill_id"] == "skillabus:mlflow"
    assert r["AWS Certified Solutions Architect - Associate"]["vocab"] == "seed"


def test_vocabulary_ids_keep_close_tools_apart():
    """C2: a broad ESCO link ("data visualisation software") does not merge Tableau and Power BI."""
    r = norm("tableau", "power bi")
    assert r["tableau"]["skill_id"] == "skillabus:tableau" and r["power bi"]["skill_id"] == "skillabus:power-bi"
    assert r["tableau"]["vocab"] == "seed" and r["tableau"]["how"] == "dictionary"

