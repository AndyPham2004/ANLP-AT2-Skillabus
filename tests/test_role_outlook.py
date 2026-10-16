"""role_outlook.csv (plan D13, #118): the official Australian signal per role, from Jobs and Skills Australia."""

import csv

from skillabus import paths

COLUMNS = ["role", "anzsco_code", "anzsco_title", "shortage_2025", "vacancies_latest", "vacancies_latest_month",
           "vacancies_12m_ago", "source_osl_url", "source_ivi_url", "date_checked", "note"]
RATINGS = {"Shortage", "No shortage", "Regional shortage", "Metro shortage", ""}


def rows():
    with open(paths.ROLE_OUTLOOK, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_columns_and_one_row_per_role():
    table = rows()
    assert list(table[0].keys()) == COLUMNS
    with open(paths.ROLE_OCCUPATIONS, encoding="utf-8", newline="") as f:
        roles = {r["role"] for r in csv.DictReader(f)}
    assert {r["role"] for r in table} == roles                      # all 11 roles
    by_role = {}
    for r in table:
        by_role.setdefault(r["role"], []).append(r["anzsco_code"])
    assert all(len(codes) == 1 for role, codes in by_role.items() if role != "Network/Systems Administrator")
    assert sorted(by_role["Network/Systems Administrator"]) == ["262113", "263112"]   # two ANZSCO codes


def test_values_are_what_the_sources_give():
    for r in rows():
        assert r["anzsco_code"].isdigit() and len(r["anzsco_code"]) == 6
        assert r["shortage_2025"] in RATINGS
        for col in ("vacancies_latest", "vacancies_12m_ago"):
            assert r[col] == "" or float(r[col]) >= 0
        assert r["vacancies_latest_month"] == "2026-08"
        assert r["source_osl_url"].startswith("https://www.jobsandskills.gov.au/")
        assert r["source_ivi_url"].startswith("https://www.jobsandskills.gov.au/")
        assert r["date_checked"] == "2026-10-16" and r["note"]       # every row says what its numbers are


def test_shortage_roles_are_the_ones_the_2025_list_names():
    shortage = {r["role"] for r in rows() if r["shortage_2025"] == "Shortage"}
    assert shortage == {"QA/Test Engineer", "DevOps/SRE"}
