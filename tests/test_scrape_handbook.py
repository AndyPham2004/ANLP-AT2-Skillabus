"""Tests for data-eda/src/scrape_handbook.py: the payload parser. Run: pytest tests/test_scrape_handbook.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from scrape_handbook import parse_subject  # noqa: E402

PAYLOAD = json.loads((ROOT / "tests/fixtures/handbook_payload_36118.json").read_text(encoding="utf-8"))
# The 36118 page has two offerings, already distinct and sorted; these are out of order, list Autumn twice,
# and include one the handbook marks as not offered.
OFFERINGS = [
    {"teaching_period": "Spring Session", "mode": "On campus - Weekly", "offered": "true"},
    {"teaching_period": "Autumn Session", "mode": "Online - Weekly", "offered": "true"},
    {"teaching_period": "Autumn Session", "mode": "On campus - Weekly", "offered": "true"},
    {"teaching_period": "Summer Session", "mode": "Block", "offered": "false"},
]


def test_sessions_are_the_unique_teaching_periods_sorted():
    assert parse_subject(PAYLOAD, "2026")["sessions"] == "Autumn Session|Spring Session"
    assert parse_subject({**PAYLOAD, "offering": OFFERINGS}, "2026")["sessions"] == "Autumn Session|Spring Session"


def test_modes_come_from_the_offerings():
    row = parse_subject({**PAYLOAD, "offering": OFFERINGS}, "2026")
    assert row["modes"] == "On campus - Weekly|Online - Weekly"   # not "Block": that offering is not offered


def test_no_offerings_gives_empty_strings():
    row = parse_subject({**PAYLOAD, "offering": None}, "2026")
    assert row["sessions"] == "" and row["modes"] == ""
