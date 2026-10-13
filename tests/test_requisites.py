"""Tests for requisites.py: who can enrol, what to take first, and in which session."""
from datetime import date

import pytest

from skillabus.requisites import _parse, enrolment, load_rules, next_session, schedule

HEADER = "subject_code,kind,rule,item,type,requisite_code,requisite_text,evop_found,source_url\n"


@pytest.fixture
def rules(tmp_path):
    prereq = tmp_path / "prerequisites.csv"
    prereq.write_text(HEADER + "\n".join([
        "A,requisite,,,,,,y,u",                                                       # no condition
        "B,requisite,(1),1,academic,A,A Intro,y,u",                                   # needs A
        "C,requisite,((1 OR 1a) AND 2),1,admission,,Admission into C04372 Master of Data Science,y,u",
        "C,requisite,((1 OR 1a) AND 2),1a,admission,,Admission into C09999 Master of Law,y,u",
        "C,requisite,((1 OR 1a) AND 2),2,academic,B,B Middle,y,u",                    # MDSI and B (B needs A)
        "D,requisite,(1),1,admission,,Admission into C09999 Master of Law,y,u",       # another course only
        "E,antirequisite,(1),1,academic,A,A Intro,y,u",                               # not after A
        "F,requisite,(1 AND 2),1,academic,A,A Intro,y,u",                             # item 2 was not scraped
        "G,requisite,,,,,,n,u",                                                       # no record: unverified
        "H,requisite,(1),1,corequisite,A,A Intro,y,u",
        "I,requisite,,,,,,y,u",                                                       # scraped, not taught in 2026
    ]) + "\n", encoding="utf-8")
    offer = tmp_path / "offerings.csv"
    offer.write_text("subject_code,teaching_period,mode\n" + "\n".join(
        f"{code},{period},On campus" for code, period in [
            ("A", "Autumn Session"), ("A", "Spring Session"), ("B", "Spring Session"), ("C", "Autumn Session"),
            ("D", "Autumn Session"), ("E", "Autumn Session"), ("F", "Autumn Session"), ("G", "Session 3"),
            ("H", "Autumn Session")]) + "\n", encoding="utf-8")
    return load_rules(prereq, offer)


def test_the_rule_parser_keeps_the_grouping():
    assert _parse("((1 OR 1a) AND 2)") == ("AND", [("OR", ["1", "1a"]), "2"])
    assert _parse("(1 AND 2 OR 3)") == ("OR", [("AND", ["1", "2"]), "3"])     # AND binds tighter
    with pytest.raises(ValueError):
        _parse("((1 OR 2)")


def test_open_needs_and_closed(rules):
    assert enrolment("A", set(), rules)["status"] == "open"
    assert enrolment("B", set(), rules) == {"status": "needs", "needs": ["A"], "reason": "take A first",
                                             "unverified": False}
    assert enrolment("B", {"A"}, rules)["status"] == "open"
    # C needs B, which itself needs A: one level only, so C is closed until A is taken
    assert enrolment("C", set(), rules)["status"] == "closed"
    assert enrolment("C", {"A"}, rules)["needs"] == ["B"]
    assert enrolment("C", {"A"}, rules, home_course="C01234")["status"] == "closed"


def test_reasons_say_what_is_missing(rules):
    assert enrolment("D", set(), rules)["reason"] == "needs admission into another course"
    assert enrolment("E", {"A"}, rules)["reason"] == "antirequisite: already took A"
    assert enrolment("E", set(), rules)["status"] == "open"
    assert "not in the Handbook data" in enrolment("F", {"A"}, rules)["reason"]   # a lost item never counts as met
    assert enrolment("I", set(), rules)["reason"] == "not taught in 2026 (Handbook)"
    assert enrolment("Z", set(), rules)["status"] == "open"                      # not in the scrape at all


def test_an_empty_rule_without_a_record_is_open_but_unverified(rules):
    assert enrolment("G", set(), rules) == {"status": "open", "needs": [], "reason": "", "unverified": True}


def test_without_files_everything_is_open(tmp_path):
    empty = load_rules(tmp_path / "none.csv", tmp_path / "none.csv")
    assert not empty.loaded and enrolment("43023", set(), empty)["status"] == "open"


def test_schedule_puts_prerequisites_first_and_respects_sessions(rules):
    plan = schedule(["A", "B", "C"], rules, start=("Autumn", 2027))
    assert [(s["subject_code"], s["session"], s["after"]) for s in plan] == [
        ("A", "Autumn 2027", []),
        ("B", "Spring 2027", ["A"]),                               # B runs in Spring only
        ("C", "Autumn 2028", ["B"]),                               # after B, and C runs in Autumn only
    ]
    corequisite = schedule(["A", "H"], rules, start=("Autumn", 2027))
    assert [s["session"] for s in corequisite] == ["Autumn 2027", "Autumn 2027"]
    assert schedule(["G"], rules, start=("Spring", 2027))[0] == {
        "subject_code": "G", "session": "Spring 2027", "offered": ["Session 3"], "after": [], "unverified": True}


def test_next_session():
    assert next_session(date(2026, 10, 13)) == ("Autumn", 2027)
    assert next_session(date(2027, 1, 20)) == ("Autumn", 2027)
    assert next_session(date(2027, 5, 1)) == ("Spring", 2027)
