"""build_vocabulary.py (plan D5): the committed vocabulary, its ESCO links, its parts, and the ad counter."""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from build_vocabulary import (  # noqa: E402
    AD_SOURCES, CORE_CATEGORY, ESCO, KNOWN_WRONG, MIN_ADS, MIN_EMPLOYERS, build, check_new_aliases, check_review,
    count_ads, count_corpus, esco_essentials, load_corpus, part_certifications, read_table, self_mention, skill_hits,
    vocab_slug,
)
from skillabus import extract, paths  # noqa: E402

VOCAB = read_table(paths.SKILLS_VOCABULARY)
SEED = read_table(paths.SKILLS_SEED)
REVIEW = read_table(paths.ESCO_LINK_REVIEW)
ADDED = read_table(paths.ADDED_SKILLS)
COUNTS = read_table(paths.VOCAB_AD_COUNTS).set_index("label")
ONET_MAP = read_table(paths.ONET_TOOL_MAP)
OCC = read_table(paths.OCCUPATION_SKILLS)
ESCO_TABLE = pd.read_csv(ESCO, usecols=["concept_uri", "preferred_label"], dtype=str)
EXTRACT = VOCAB[VOCAB.used_for.str.contains("extract")]
BY_LABEL = VOCAB.set_index("label")


def test_committed_vocabulary_is_what_the_builder_writes():
    assert build().equals(VOCAB), "rerun python data-eda/src/build_vocabulary.py and commit the CSV"


def test_every_dictionary_skill_is_in_the_vocabulary_unchanged():
    """The pipeline can switch from skills_seed_v2.csv to the vocabulary without losing a skill (plan C2)."""
    assert len(SEED) == 148 and set(SEED.canonical) <= set(EXTRACT.label)
    for s in SEED.itertuples():
        row = BY_LABEL.loc[s.canonical]
        assert (row.aliases_ads, row.strict, row.category) == (s.aliases, s.strict, s.category), s.canonical


def test_skill_id_is_the_esco_id_only_for_an_exact_match():
    exact, other = VOCAB[VOCAB.esco_match == "exact"], VOCAB[VOCAB.esco_match != "exact"]
    assert (exact.skill_id == "esco:" + exact.esco_uri).all() and (exact.source == "esco").all()
    assert other.skill_id.str.startswith("skillabus:").all() and (other.source == "added").all()
    assert (other.why_added != "").all()
    assert VOCAB.skill_id.is_unique and VOCAB.label.str.casefold().is_unique
    assert set(VOCAB.esco_match) <= {"exact", "close", "broad", "none"}
    assert set(VOCAB.used_for) <= {"extract", "core_skill", "extract;core_skill", "certification"}
    assert (VOCAB[VOCAB.esco_match == "none"].esco_uri == "").all()


def test_only_rows_with_aliases_are_used_for_detection():
    assert (EXTRACT.aliases_ads != "").all()
    assert (VOCAB[~VOCAB.used_for.str.contains("extract")].aliases_ads == "").all()


def test_tools_under_one_wide_esco_concept_keep_their_own_ids():
    rows = BY_LABEL.loc[["Tableau", "Power BI"]]
    assert rows.esco_label.tolist() == ["data visualisation software"] * 2
    assert rows.esco_match.tolist() == ["broad", "broad"] and rows.skill_id.is_unique


def test_the_wrong_links_of_14_october_are_gone():
    assert not set(zip(VOCAB.label, VOCAB.esco_uri)) & KNOWN_WRONG
    assert BY_LABEL.loc["Spark"].esco_label != "SPARK"  # the Java web framework


def test_a_bad_review_row_is_reported():
    bad = REVIEW.copy()
    bad.loc[bad.canonical == "Tableau", "esco_label"] = "Tableau"   # not ESCO's label for that URI
    bad.loc[bad.canonical == "Kafka", "note"] = ""                  # a non-exact link with no reason
    bad.loc[bad.canonical == "Keras", ["esco_uri", "esco_label"]] = [
        "http://data.europa.eu/esco/skill/7b0d5000-00da-4864-b776-6de49a87a669", "computer vision"]
    errors = check_review(SEED, bad, ESCO_TABLE)
    assert any(e.startswith("Tableau:") for e in errors)
    assert any(e.startswith("Kafka:") and "note" in e for e in errors)
    assert any(e.startswith("Keras:") and "wrong" in e for e in errors)
    assert check_review(SEED, REVIEW, ESCO_TABLE) == []
    assert check_review(SEED.iloc[:-1], REVIEW, ESCO_TABLE) == ["review row for a skill not in the dictionary: Ansible"]


def test_every_esco_essential_skill_of_the_roles_is_one_exact_row():
    essentials = esco_essentials(OCC)
    exact_uris = VOCAB.esco_uri[VOCAB.esco_match == "exact"]
    assert set(essentials) <= set(exact_uris) and exact_uris.is_unique
    core = VOCAB[VOCAB.category == CORE_CATEGORY]
    assert (core.used_for == "core_skill").all() and (core.aliases_ads == "").all() and (core.source == "esco").all()
    # A dictionary skill that is an essential ESCO concept is marked, not repeated.
    assert BY_LABEL.loc["Statistics"].used_for == "extract;core_skill"


def test_every_onet_in_demand_tool_maps_to_a_core_skill_or_is_dropped_with_a_reason():
    tools = set(OCC[OCC.source == "onet"].skill)
    assert tools == set(ONET_MAP.onet_tool)
    mapped = ONET_MAP[ONET_MAP.label != ""]
    assert set(mapped.label) <= set(VOCAB.label)
    assert BY_LABEL.loc[sorted(set(mapped.label))].used_for.str.contains("core_skill").all()
    assert (ONET_MAP[ONET_MAP.label == ""].note != "").all()
    assert BY_LABEL.loc["AWS"].used_for == "extract;core_skill"   # "Amazon Web Services AWS software"


def test_added_rows_follow_the_ad_rule():
    onet_labels = set(ONET_MAP.label)
    for r in ADDED.itertuples():
        c = COUNTS.loc[r.label]
        ok = int(c.n_ads) >= MIN_ADS and int(c.n_employers) >= MIN_EMPLOYERS
        if ok:
            assert BY_LABEL.loc[r.label].aliases_ads == r.aliases_ads, r.label
            assert "AU ad" in BY_LABEL.loc[r.label].why_added
        elif r.label in onet_labels:
            assert BY_LABEL.loc[r.label].used_for == "core_skill", r.label
        else:
            assert r.label not in BY_LABEL.index, r.label
    assert set(SEED.canonical) | set(ADDED.label) <= set(COUNTS.index)


def test_added_rows_take_no_mention_from_a_dictionary_skill():
    """The same ads give the dictionary skills the same hits with or without the added rows."""
    ads = pd.read_csv(paths.RECENT_ADS, dtype=str, keep_default_na=False).description  # texts hold "#" lines
    seed_rows = pd.DataFrame({"label": SEED.canonical, "category": SEED.category, "strict": SEED.strict,
                              "aliases_ads": SEED.aliases})
    alone = skill_hits(seed_rows, ads)
    together = skill_hits(EXTRACT, ads)
    dictionary = set(SEED.canonical)
    assert all(a == (t & dictionary) for a, t in zip(alone, together))


def test_a_new_alias_that_hides_or_repeats_another_is_refused():
    rows = pd.DataFrame({"label": ["Git", "GitHub Actions", "Copy"], "strict": ["0", "0", "0"],
                         "aliases_ads": ["git|github", "github actions", "github"]})
    errors = check_new_aliases(rows, {"GitHub Actions", "Copy"})
    assert any("GitHub Actions" in e and "hide" in e for e in errors)
    assert any(e.startswith("Copy:") and "also an alias" in e for e in errors)
    assert check_new_aliases(rows.iloc[:1], set()) == []


def test_an_employer_naming_its_own_product_does_not_count():
    assert self_mention("Datadog", "Datadog", "datadog")
    assert self_mention("DNS Technology", "DNS", "DNS")
    assert not self_mention("Canva", "Python", "python")
    corpus = pd.DataFrame({"source": ["ats_2026"] * 3, "title": ["a", "b", "c"],
                           "employer": ["Datadog", "Canva", "Xero"],
                           "text": ["We build Datadog.", "We use Datadog daily.", "Python only."]})
    skills = pd.DataFrame({"label": ["Datadog"], "category": ["Engineering"], "strict": ["0"],
                           "aliases_ads": ["datadog"]})
    row = count_corpus(skills, corpus).iloc[0]
    assert (row.n_ads, row.n_employers, row.ats_2026) == (1, 1, 1)


def test_ads_fetched_twice_count_once(tmp_path):
    seek = tmp_path / "seek.csv"
    ats = tmp_path / "ats.csv"
    pd.DataFrame({"title": ["DS", "DS"], "advertiser": ["Hays", "Hays"],
                  "description": ["Python and SQL.", "Python  and SQL."]}).to_csv(seek, index=False)
    pd.DataFrame({"title": ["Engineer", "Engineer", "Analyst"], "company": ["Canva", "Canva", "Canva"],
                  "description": ["Go and Rust.", "Go and Rust, Sydney.", "python and sql."]}).to_csv(ats, index=False)
    corpus = load_corpus({"seek_2019_22": [seek], "ats_2026": [ats]})
    assert corpus.source.tolist() == ["seek_2019_22", "ats_2026"]   # same text; same title and employer
    assert set(AD_SOURCES) >= set(corpus.source)


def test_certifications_hook(tmp_path):
    assert part_certifications(tmp_path / "missing.csv") == []
    f = tmp_path / "certifications.csv"
    pd.DataFrame({"cert": ["AWS Certified Solutions Architect - Associate"], "vendor": ["AWS"]}).to_csv(f, index=False)
    (row,) = part_certifications(f)
    assert (row["category"], row["used_for"], row["aliases_ads"]) == ("Certification", "certification", "")
    assert row["skill_id"] == "skillabus:aws-certified-solutions-architect-associate"


def test_slugs_keep_plus_and_hash_apart():
    assert vocab_slug("C++") != vocab_slug("C#") and vocab_slug("D3.js") == "d3-js"


def test_ad_counts_use_the_same_matching_as_extract():
    texts = [
        "Strong SQL and Python and R. Experience with SQL Server and PowerBI dashboards.",
        "You will excel in a team: C#, .NET and Kubernetes (k8s). See https://python.org",
        "SAS or sas? AWS, Azure and GCP; machine-learning and generative AI.",
    ]
    counts = count_ads(VOCAB[VOCAB.label.isin(SEED.canonical)], texts)
    expected = Counter()
    for t in texts:
        expected.update({m["canonical"] for m in extract.extract(t)})
    assert counts == expected
    assert counts["SQL Server"] == 1 and counts["SAS"] == 1 and "Python" in counts


@pytest.mark.parametrize("source", ["recent_2024_26"])
def test_committed_counts_match_a_recount_of_the_committed_ads(source):
    """The recent ads are in git, so their column can be checked without the raw ATS downloads."""
    corpus = load_corpus({"seek_2019_22": [paths.SEEK_ADS], "recent_2024_26": [paths.RECENT_ADS]})
    corpus = corpus[corpus.source == source].reset_index(drop=True)
    skills = pd.concat([pd.DataFrame({"label": SEED.canonical, "category": SEED.category, "strict": SEED.strict,
                                      "aliases_ads": SEED.aliases}),
                        ADDED[["label", "category", "strict", "aliases_ads"]]], ignore_index=True)
    recount = count_corpus(skills, corpus).set_index("label")[source]
    assert recount.astype(str).equals(COUNTS.loc[recount.index, source])
