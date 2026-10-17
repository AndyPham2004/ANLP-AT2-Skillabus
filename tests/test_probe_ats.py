"""Tests for data-eda/src/probe_ats.py counting rules. Run: pytest tests/test_probe_ats.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from probe_ats import classify, count_roles  # noqa: E402


def row(title, location):
    return {"title": title, "location": location, "description": "x"}


def test_counts_split_by_country_and_title():
    rows = [row("Data Scientist", "Sydney"), row("Senior Data Scientist", "Melbourne, VIC"),
            row("Data Engineer", "Sydney"), row("Data Scientist", "London"),
            row("Quantitative AI Designer", "Sydney")]   # DATA_TITLE takes "quantitative"; the bare "AI" rule drops it
    assert count_roles(rows) == {"total": 5, "au": 4, "data_au": 3, "ds_au": 2}


def test_us_state_codes_are_not_australia():
    rows = [row("Data Scientist", "Seattle, WA"), row("Data Scientist", "San Antonio, TX | Remote"),
            row("Data Scientist", "Perth, Western Australia"), row("Data Scientist", "Melbourne, VIC"),
            row("Data Scientist", "Remote - AU")]
    assert count_roles(rows)["au"] == 3


def test_empty_board_is_reachable_but_empty():
    assert classify(200, []) == "empty"
    assert classify(200, [row("x", "y")]) == "ok"
    assert classify(404, None) == "missing"
    assert classify(500, None) == "error"
