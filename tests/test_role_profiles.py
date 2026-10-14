"""build_role_profiles.py: tool names -> dictionary skills, and the shares per role."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from build_role_profiles import (  # noqa: E402
    australian_postings, load_dictionary, parse_skills, profiles, to_skill,
)

LOOKUP, CATEGORY = load_dictionary()


def test_tool_names_map_to_dictionary_skills():
    assert to_skill("python", LOOKUP) == "Python"
    assert to_skill("power bi", LOOKUP) == "Power BI"
    assert to_skill("pyspark", LOOKUP) == "Spark"            # an alias
    assert to_skill("word", LOOKUP) == "Microsoft Office"   # TOKEN_MAP, not an alias
    assert to_skill("unix", LOOKUP) == "Linux"
    assert to_skill("c#", LOOKUP) == "C#"


def test_unreliable_and_unknown_names_are_left_out():
    assert to_skill("go", LOOKUP) is None                   # the English word, per the dataset
    assert to_skill("golang", LOOKUP) == "Go"
    assert to_skill("splunk", LOOKUP) is None


def test_parse_skills_tolerates_empty_and_broken_cells():
    assert parse_skills("['python', 'sql']") == ["python", "sql"]
    assert parse_skills("") == []
    assert parse_skills("['python', ") == []


def test_shares_dedupe_and_fold_senior_titles():
    df = pd.DataFrame({
        "job_country": ["Australia"] * 4 + ["United States"],
        "job_title_short": ["Data Engineer", "Senior Data Engineer", "Data Engineer", "Data Analyst", "Data Engineer"],
        "job_title": ["DE", "Senior DE", "DE", "DA", "DE"],
        "company_name": ["A", "B", "A", "C", "D"],
        "job_location": ["Sydney"] * 5,
        "job_skills": ["['python', 'sql']", "['python', 'kafka']", "['python', 'sql']", "", "['java']"],
    })
    au = australian_postings(df)
    assert len(au) == 3                                       # one repeat and the US ad dropped
    out, _ = profiles(au, LOOKUP, CATEGORY)
    de = out[out.role == "Data Engineer"].set_index("skill")
    assert de.loc["Python", "pct_ads"] == 100.0 and de.loc["Python", "total_ads"] == 2
    assert de.loc["Kafka", "n_ads"] == 1 and de.loc["Kafka", "pct_ads"] == 50.0
    assert "Data Analyst" not in set(out.role)               # its only ad names no tool
