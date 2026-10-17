"""Adzuna search counts per skill x role (plan D12, #115): the committed counts file and its queries."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from count_role_skills_adzuna import COLUMNS, COUNTS, QUERIES, TITLE  # noqa: E402
from skillabus import paths  # noqa: E402

counts = pd.read_csv(COUNTS, dtype={"skill_query": str}, keep_default_na=False, na_values={"count": [""], "role_total": [""]})
queries = pd.read_csv(QUERIES, dtype=str, keep_default_na=False)
priority = pd.read_csv(paths.PRIORITY_SKILLS, dtype=str)


def test_columns_and_one_row_per_priority_skill():
    assert list(counts.columns) == COLUMNS
    assert set(zip(counts.role, counts.skill)) == set(zip(priority.role, priority.skill))
    assert len(counts) == len(priority)


def test_every_role_has_one_positive_total_and_its_title_query():
    per_role = counts.groupby("role").agg(totals=("role_total", "nunique"), total=("role_total", "first"),
                                          query=("role_query", "first"))
    assert set(per_role.index) == set(TITLE)
    assert (per_role.totals == 1).all() and (per_role.total > 0).all()
    assert all(per_role.loc[r, "query"] == TITLE[r] for r in TITLE)


def test_a_skill_count_never_exceeds_its_role_total():
    counted = counts.dropna(subset=["count"])
    assert (counted["count"] <= counted.role_total).all()


def test_blank_count_only_where_no_phrase_was_searched():
    merged = counts.merge(queries, on=["role", "skill"], validate="one_to_one")
    assert len(merged) == len(counts)              # every counted row has its query row, so none goes unchecked
    assert (merged.skill_query == merged.what_phrase).all()
    assert (merged["count"].isna() == (merged.what_phrase == "")).all()
