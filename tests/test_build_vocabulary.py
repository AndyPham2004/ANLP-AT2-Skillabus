"""build_vocabulary.py (plan D5): the committed vocabulary, its ESCO links, and the ad counter."""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from build_vocabulary import (  # noqa: E402
    ESCO, KNOWN_WRONG, build, check_review, count_ads, read_table, vocab_slug,
)
from skillabus import extract, paths  # noqa: E402

VOCAB = read_table(paths.SKILLS_VOCABULARY)
SEED = read_table(paths.SKILLS_SEED)
REVIEW = read_table(paths.ESCO_LINK_REVIEW)
ESCO_TABLE = pd.read_csv(ESCO, usecols=["concept_uri", "preferred_label"], dtype=str)


def test_committed_vocabulary_is_what_the_builder_writes():
    assert build().equals(VOCAB), "rerun python data-eda/src/build_vocabulary.py and commit the CSV"


def test_every_dictionary_skill_is_in_the_vocabulary_unchanged():
    """The pipeline can switch from skills_seed_v2.csv to the vocabulary without losing a skill (plan C2)."""
    part1 = VOCAB[VOCAB.used_for.str.contains("extract")].set_index("label")
    assert len(SEED) == 148 and set(SEED.canonical) <= set(part1.index)
    for s in SEED.itertuples():
        row = part1.loc[s.canonical]
        assert (row.aliases_ads, row.strict, row.category) == (s.aliases, s.strict, s.category), s.canonical


def test_skill_id_is_the_esco_id_only_for_an_exact_match():
    exact = VOCAB[VOCAB.esco_match == "exact"]
    other = VOCAB[VOCAB.esco_match != "exact"]
    assert (exact.skill_id == "esco:" + exact.esco_uri).all() and (exact.source == "esco").all()
    assert other.skill_id.str.startswith("skillabus:").all() and (other.source == "added").all()
    assert (other.why_added != "").all() and (exact.why_added == "").all()
    assert VOCAB.skill_id.is_unique and VOCAB.label.is_unique
    assert set(VOCAB.esco_match) <= {"exact", "close", "broad", "none"}
    assert (VOCAB[VOCAB.esco_match == "none"].esco_uri == "").all()


def test_tools_under_one_wide_esco_concept_keep_their_own_ids():
    rows = VOCAB.set_index("label").loc[["Tableau", "Power BI"]]
    assert rows.esco_label.tolist() == ["data visualisation software"] * 2
    assert rows.esco_match.tolist() == ["broad", "broad"] and rows.skill_id.is_unique


def test_the_wrong_links_of_14_october_are_gone():
    links = set(zip(VOCAB.label, VOCAB.esco_uri))
    assert not links & KNOWN_WRONG
    assert VOCAB.set_index("label").loc["Spark"].esco_label != "SPARK"  # the Java web framework


def test_a_bad_review_row_is_reported():
    bad = REVIEW.copy()
    i = bad.index[bad.canonical == "Tableau"][0]
    bad.loc[i, "esco_label"] = "Tableau"                      # not ESCO's label for that URI
    j = bad.index[bad.canonical == "Kafka"][0]
    bad.loc[j, "note"] = ""                                   # a non-exact link with no reason
    k = bad.index[bad.canonical == "Keras"][0]
    bad.loc[k, ["esco_uri", "esco_label"]] = ["http://data.europa.eu/esco/skill/7b0d5000-00da-4864-b776-6de49a87a669",
                                             "computer vision"]
    errors = check_review(SEED, bad, ESCO_TABLE)
    assert any(e.startswith("Tableau:") for e in errors)
    assert any(e.startswith("Kafka:") and "note" in e for e in errors)
    assert any(e.startswith("Keras:") and "wrong" in e for e in errors)
    assert check_review(SEED, REVIEW, ESCO_TABLE) == []
    assert check_review(SEED.iloc[:-1], REVIEW, ESCO_TABLE) == ["review row for a skill not in the dictionary: Ansible"]


def test_slugs_keep_plus_and_hash_apart():
    assert vocab_slug("C++") != vocab_slug("C#") and vocab_slug("D3.js") == "d3-js"


def test_ad_counts_use_the_same_matching_as_extract():
    texts = [
        "Strong SQL and Python and R. Experience with SQL Server and PowerBI dashboards.",
        "You will excel in a team: C#, .NET and Kubernetes (k8s). See https://python.org",
        "SAS or sas? AWS, Azure and GCP; machine-learning and generative AI.",
    ]
    counts = count_ads(VOCAB[VOCAB.used_for.str.contains("extract")], texts)
    expected = Counter()
    for t in texts:
        expected.update({m["canonical"] for m in extract.extract(t)})
    assert counts == expected
    assert counts["SQL Server"] == 1 and counts["SAS"] == 1 and "Python" in counts
