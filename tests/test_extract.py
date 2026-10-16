"""Tests for skill extraction tiers 1-2. Run from the repo root: pytest tests/"""
import csv
from pathlib import Path

import pytest

from skillabus import paths
from skillabus.extract import extract, load_dictionary, split_sentences

ROOT = Path(__file__).resolve().parents[1]
AD = (ROOT / "tests/fixtures/ad_rw_2026-09-23.txt").read_text(encoding="utf-8")
RESUME = (ROOT / "tests/fixtures/resume_synthetic.txt").read_text(encoding="utf-8")


def skills(text, method="dictionary"):
    return {m["canonical"] for m in extract(text, method) if m["canonical"]}


def candidates(text):
    return {m["text"] for m in extract(text, "ner") if m["canonical"] is None}


def poster_gap():
    with open(paths.POSTER_GAP, encoding="utf-8") as f:   # archive/poster_AT2A/data/gap.csv
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


# ---------------------------------------------------------------- shape and sentences

@pytest.mark.parametrize("method", ["dictionary", "ner"])
def test_mentions_follow_the_data_contract(method):
    mentions = extract(AD, method)
    assert mentions
    for m in mentions:
        assert set(m) == {"text", "canonical", "method", "sentence", "requirement"}
        assert m["requirement"] in ("required", "preferred", "")
        assert m["method"] == method
        assert m["text"] in m["sentence"]


def test_wrapped_bullet_is_one_sentence():
    sentences = split_sentences(AD)
    assert ("Develop and implement predictive models and machine learning algorithms "
            "to solve complex business problems.") in sentences
    assert "Key Responsibilities" in sentences


def test_empty_text_and_bad_method():
    assert extract("", "dictionary") == []
    assert extract("   \n", "ner") == []
    with pytest.raises(ValueError):
        extract(AD, "regex")


# ------------------------------------------------------------------ tier 1 dictionary

def test_dictionary_reproduces_the_poster_gap_chart():
    """gap.csv (poster block 6) lists the technical skills of this ad and which ones
    the sample resume covers. Tier 1 must give the same answer."""
    technical = {s["canonical"] for s in load_dictionary() if s["category"] != "Professional"}
    gap = poster_gap()
    assert skills(AD) & technical == {row["skill"] for row in gap}
    covered = {row["skill"] for row in gap if row["covered"] == "1"}
    assert {row["skill"] for row in gap if row["skill"] in skills(RESUME)} == covered


def test_strict_aliases_are_case_sensitive():
    assert "SAS" in skills("Experience using SAS and SQL.")
    assert "SAS" not in skills("Works with our saas and sas-like products.")
    assert "R" not in skills("R&D team, R U ready?")
    assert "R" in skills("Strong R programming skills.")
    assert skills("Proficiency in Python and R.") == {"Python", "R"}


def test_longest_alias_wins():
    assert skills("Experience with SQL Server.") == {"SQL Server"}
    assert skills("Deployed on Google Cloud Platform.") == {"Google Cloud"}
    assert skills("Generative AI projects.") == {"Generative AI"}


def test_aliases_with_symbols():
    assert skills("C++, C# and CI/CD pipelines; A/B testing.") == {"C++", "C#", "CI/CD", "A/B testing"}
    assert skills("PL/SQL developer") == {"SQL", "Oracle"}


def test_urls_and_emails_are_ignored():
    assert skills("Contact julia.smith@spark.com.au or visit https://www.tableau.com/careers") == set()


def test_one_mention_per_skill_per_sentence():
    mentions = extract("Python, python and more Python. We also use Python daily.")
    assert [m["canonical"] for m in mentions] == ["Python", "Python"]
    assert mentions[0]["sentence"] != mentions[1]["sentence"]


# ----------------------------------------------------------------------- tier 2 spaCy

spacy = pytest.importorskip("spacy")


def test_ner_drops_aliases_used_as_verbs():
    sentence = "You will excel in a fast-paced team and spark new ideas."
    assert skills(sentence, "dictionary") == {"Excel", "Spark"}   # tier 1 false positives
    assert skills(sentence, "ner") == set()
    assert "Excel" in skills("Advanced Excel skills and Power BI.", "ner")


def test_ner_keeps_ing_forms():
    sentence = "Coaching juniors, forecasting demand and clustering customers."
    assert skills(sentence, "ner") == {"Leadership", "Time series forecasting", "Clustering"}


def test_ner_finds_plural_forms():
    sentence = "Experience building REST APIs and data warehouses; manage stakeholders."
    assert skills(sentence, "dictionary") == set()
    assert skills(sentence, "ner") == {"API development", "Data warehousing", "Stakeholder management"}


def test_ner_keeps_every_tier_1_skill_of_the_ad():
    assert skills(AD, "dictionary") <= skills(AD, "ner")


def test_ner_proposes_skills_outside_the_dictionary():
    # Alteryx joined the dictionary on 14 Oct (#65), so only the other two are candidates.
    assert candidates("Experience with tools such as Alteryx, Dataiku and KNIME.") == {
        "Dataiku", "KNIME"}
    assert candidates("Demonstrated experience in customer segmentation and Python.") == {
        "customer segmentation"}
    assert "data science" in candidates(AD)


def test_ner_candidates_skip_numbers_places_and_vague_nouns():
    assert candidates("5+ years of experience in Sydney with large clusters and Python.") == set()
    assert candidates("Understanding of retrieval-augmented generation (RAG).") == set()


# ------------------------------------------------- C2: the vocabulary; D14: required or preferred

def test_extraction_reads_the_vocabulary_detection_rows():
    """Since C2 the dictionary is skills_vocabulary.csv's detection rows; the old 148 are all in it."""
    vocabulary = {s["canonical"]: s for s in load_dictionary()}
    with open(paths.SKILLS_SEED, encoding="utf-8") as f:
        old = {r["canonical"] for r in csv.DictReader(line for line in f if not line.startswith("#"))}
    assert old <= set(vocabulary) and len(vocabulary) > len(old)
    assert vocabulary["Tableau"]["skill_id"] == "skillabus:tableau" and vocabulary["Python"]["esco_match"] == "exact"
    assert [m["canonical"] for m in extract("Experience with Kubernetes, Terraform and Grafana.")] == [
        "Kubernetes", "Terraform", "Grafana"]                       # Grafana: an IT skill added in D5


def test_requirement_comes_from_the_sentence_or_its_heading():
    ad = """Essential criteria:
- Python and SQL
Nice to have:
- dbt
Benefits
- Free Python books
Must have strong Tableau skills. Experience with Power BI is desirable but not required."""
    req = {(m["canonical"], m["sentence"]): m["requirement"] for m in extract(ad)}
    assert req[("Python", "Python and SQL")] == req[("SQL", "Python and SQL")] == "required"
    assert req[("dbt", "dbt")] == "preferred"
    assert req[("Python", "Free Python books")] == ""                 # "Benefits" ends the section
    assert req[("Tableau", "Must have strong Tableau skills.")] == "required"
    assert req[("Power BI", "Experience with Power BI is desirable but not required.")] == "preferred"


def test_requirement_cues_skip_business_requirements_and_question_lines():
    # Review #109: "requirements" and "minimum" count only in a heading, "as required" never, and a
    # line that names a skill or ends a sentence (. ? !) is not a heading.
    ad = """Gather business requirements and build dashboards in Tableau.
Minimum 3 years with Python.
Other duties as required, including SQL reporting.
Don't meet every requirement?
We encourage you to apply anyway and tell us about your Python projects.
Minimum requirements:
- Java"""
    req = {(m["canonical"], m["sentence"]): m["requirement"] for m in extract(ad)}
    assert req[("Tableau", "Gather business requirements and build dashboards in Tableau.")] == ""
    assert req[("Python", "Minimum 3 years with Python.")] == ""
    assert req[("SQL", "Other duties as required, including SQL reporting.")] == ""
    assert req[("Python", "We encourage you to apply anyway and tell us about your Python projects.")] == ""
    assert req[("Java", "Java")] == "required"                       # "Minimum requirements:" is a heading


def test_a_section_heading_still_ends_the_section_when_it_names_a_skill_or_asks():
    ad = """Essential criteria:
- Python
Why join us?
Great Snowflake projects.
Must have:
- SQL
About MongoDB
MongoDB is a database company."""
    req = {(m["canonical"], m["sentence"]): m["requirement"] for m in extract(ad)}
    assert req[("Python", "Python")] == "required" and req[("SQL", "SQL")] == "required"
    assert req[("Snowflake", "Great Snowflake projects.")] == ""      # "Why join us?" ends the section
    assert req[("MongoDB", "MongoDB is a database company.")] == ""   # so does "About MongoDB"

