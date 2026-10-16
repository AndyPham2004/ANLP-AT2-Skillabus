"""The committed role_occupations.csv and occupation_skills.csv (plan D4, data-eda/src/build_occupation_skills.py)."""

import pandas as pd
import pytest

from skillabus import paths

ROLES = [
    "Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer", "Software Engineer",
    "QA/Test Engineer", "Cloud Engineer", "DevOps/SRE", "Network/Systems Administrator",
    "Cybersecurity Analyst", "Business Analyst",
]
FAMILIES = {"Data & AI", "Software", "Cloud & infrastructure", "Security", "Business analysis"}
IMPORTANCE = {"esco": {"essential", "optional"}, "onet": {"in_demand"},
              "asc": {"listed"} | {str(i) for i in range(1, 11)}}


@pytest.fixture(scope="module")
def occ():
    return pd.read_csv(paths.ROLE_OCCUPATIONS, dtype=str, keep_default_na=False)


@pytest.fixture(scope="module")
def skills():
    return pd.read_csv(paths.OCCUPATION_SKILLS, dtype=str, keep_default_na=False)


def test_every_role_has_an_esco_or_onet_occupation(occ):
    assert set(occ.role) == set(ROLES)
    for role in ROLES:
        assert set(occ[occ.role == role].source) & {"esco", "onet"}, role


def test_allowed_values(occ, skills):
    assert set(occ.source) <= {"esco", "onet", "asc"}
    assert set(occ.match) <= {"exact", "close", "broad"}
    assert set(occ.role_family) <= FAMILIES
    assert (occ.why.str.len() > 0).all()
    assert set(skills.role) <= set(ROLES)
    for source, allowed in IMPORTANCE.items():
        got = set(skills[skills.source == source].importance)
        assert got and got <= allowed, (source, got - allowed)
    assert set(skills[skills.source == "esco"].esco_digital) <= {"y", "n"}
    assert set(skills[skills.source == "onet"].onet_hot) <= {"Y", "N"}
    assert (skills[skills.source != "esco"].esco_digital == "").all()
    assert (skills[skills.source != "onet"].onet_hot == "").all()


def test_no_duplicate_rows(occ, skills):
    assert not occ.duplicated(["role", "source", "occupation_code"]).any()
    assert not skills.duplicated(["role", "source", "skill_ref"]).any()


def test_skill_rows_come_from_the_mapped_occupations(occ, skills):
    mapped = set(zip(occ.role, occ.source, occ.occupation_code))
    for role, source, codes in set(zip(skills.role, skills.source, skills.occupation_code)):
        for code in codes.split("|"):
            assert (role, source, code) in mapped, (role, source, code)


def test_every_role_has_core_skills(skills):
    for role in ROLES:
        r = skills[skills.role == role]
        essential = ((r.source == "esco") & (r.importance == "essential")).sum()
        in_demand = ((r.source == "onet") & (r.importance == "in_demand")).sum()
        assert essential >= 1 or in_demand >= 1, role
