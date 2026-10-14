"""Tests for data-eda/src/scrape_requisites.py. Run: pytest tests/test_scrape_requisites.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data-eda" / "src"))

from scrape_requisites import parse_requisites  # noqa: E402

HTML = (ROOT / "tests/fixtures/evop_36118.html").read_text(encoding="utf-8", errors="replace")

MIXED = """<html><body>Requisite rule: ((1 OR 1a) AND 2) Item Type Details
1 Admission requisite Admission into C04372 Master of Data Science and Innovation
1a Academic requisite Must have completed at least 48 credit points in 48.0000000000 Credit Points spk(s): C04379 - Master of Business Analytics (Extension)
2 Academic requisite 36106 Machine Learning Algorithms and Applications
Note: See also the information</body></html>"""

NONE = "<html><body>36100 Data Science for Innovation Note: See also the information</body></html>"


def test_36118_needs_three_subjects():
    out = parse_requisites(HTML)
    assert out["rule"] == "(1 AND 2 AND 3)"
    assert [i["code"] for i in out["items"]] == ["36100", "36103", "36106"]
    assert {i["type"] for i in out["items"]} == {"academic"}


def test_mixed_rule_keeps_item_types_and_ids():
    out = parse_requisites(MIXED)
    assert out["rule"] == "((1 OR 1a) AND 2)"
    assert out["items"][0] == {"item": "1", "type": "admission", "code": "",
                               "text": "Admission into C04372 Master of Data Science and Innovation"}
    assert out["items"][1]["item"] == "1a" and out["items"][1]["type"] == "academic" and out["items"][1]["code"] == ""
    assert out["items"][2] == {"item": "2", "type": "academic", "code": "36106",
                               "text": "36106 Machine Learning Algorithms and Applications"}


def test_no_rule_gives_empty_rule_and_no_items():
    out = parse_requisites(NONE, "36100")
    assert out["rule"] == "" and out["items"] == [] and out["found"] is True


def test_generic_not_found_page_is_flagged():
    page = "<html><body>Access Conditions There are no access restrictions enforced for this subject Note:</body></html>"
    assert parse_requisites(page, "220700")["found"] is False


ANTI = """<html><body>36100 Data Science for Innovation Anti-requisite(s) Anti-requisite rule: (1 AND 2) Item Type Details
1 Academic requisite 31250 Introduction to Data Analytics
2 Academic requisite 321130 Fundamentals of Data Analytics
Note: See also</body></html>"""


ANTI_NO_TYPE = """<html><body>32130 Fundamentals of Data Analytics Anti-requisite(s) Anti-requisite rule: (1 AND 2 AND 3) Item Details
1 31250 Introduction to Data Analytics 2 321130 Fundamentals of Data Analytics 3 329130 Fundamentals of Data Analytics
Note: See also</body></html>"""


def test_anti_requisite_table_without_type_column():
    out = parse_requisites(ANTI_NO_TYPE, "32130")
    assert out["anti_rule"] == "(1 AND 2 AND 3)"
    assert [(i["item"], i["code"], i["type"]) for i in out["anti_items"]] == [
        ("1", "31250", "academic"), ("2", "321130", "academic"), ("3", "329130", "academic")]
    assert out["anti_items"][0]["text"] == "31250 Introduction to Data Analytics"


def test_anti_requisites_are_parsed_separately():
    out = parse_requisites(ANTI, "36100")
    assert out["rule"] == "" and out["items"] == []
    assert out["anti_rule"] == "(1 AND 2)"
    assert [(i["item"], i["code"]) for i in out["anti_items"]] == [("1", "31250"), ("2", "321130")]


COREQ = """<html><body>Requisite rule: (((1 OR 1a)) OR (2 AND 3)) Item Type Details
1 Admission requisite Admission into MAJ08994 36cp Digital Finance Major
1a corequisite Must have completed at least 24 credit points in 24.0000000000 Credit Points spk(s): MAJ08984 - 36cp Finance Major MBA
2 Academic corequisite 25741 Capital Markets
3 Admission requisite Admission into STM92125 24cp Financial Technology
Note: See also</body></html>"""


def test_corequisites_are_items_of_their_own_type():
    out = parse_requisites(COREQ)
    assert [(i["item"], i["type"], i["code"]) for i in out["items"]] == [
        ("1", "admission", ""), ("1a", "corequisite", ""), ("2", "corequisite", "25741"), ("3", "admission", "")]


ANTI_THEN_REQUISITE = """<html><body>32513 Advanced Data Analytics Algorithms Anti-requisite(s) Anti-requisite rule: (1) Item Details
1 31005 Machine Learning Requisite(s) Requisite rule: (((1 OR 1a)) OR (2)) Item Type Details
1 Academic requisite 32130 Fundamentals of Data Analytics 1a Academic requisite 31250 Introduction to Data Analytics
2 Academic requisite 26776 Foundations of Business Analytics Note: See also</body></html>"""


def test_anti_requisite_table_before_the_requisite_table():
    """The live page lists anti-requisites first; the requisite rows must not leak into them (14 Oct fix)."""
    out = parse_requisites(ANTI_THEN_REQUISITE, "32513")
    assert out["anti_rule"] == "(1)"
    assert [(i["item"], i["code"]) for i in out["anti_items"]] == [("1", "31005")]
    assert out["rule"] == "(((1 OR 1a)) OR (2))"
    assert [i["code"] for i in out["items"]] == ["32130", "31250", "26776"]
