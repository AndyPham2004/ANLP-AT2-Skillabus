"""classify_ats_roles.py (plan D2, #116): the title rules that give a 2026 job-board ad its role."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from classify_ats_roles import COLUMNS, OTHER, RULES, classify, role_of  # noqa: E402


@pytest.mark.parametrize("title, role", [
    ("Senior Software Engineer, AI Tooling (Information Security)", "Software Engineer"),   # "Software Engineer" wins
    ("Staff Engineer", "Software Engineer"),
    ("Senior Java Developer", "Software Engineer"),
    ("Senior Engineer - ML Systems (AI Products)", "Machine Learning Engineer"),
    ("Senior Machine Learning Engineer", "Machine Learning Engineer"),
    ("Principal AI Platform Engineer", "Machine Learning Engineer"),
    ("Lead AI Security Engineer", "Cybersecurity Analyst"),                                # security before AI
    ("Senior Cyber Security Analyst", "Cybersecurity Analyst"),
    ("Principal Cloud Platform Engineer", "Cloud Engineer"),                               # cloud before platform
    ("Senior DevOps Engineer / Site Reliability Engineer", "DevOps/SRE"),
    ("Senior Platform Engineer", "DevOps/SRE"),
    ("Network Operations Analyst", "Network/Systems Administrator"),
    ("IT Support Admin", "Network/Systems Administrator"),
    ("Software Tester", "QA/Test Engineer"),
    ("Analytics Engineer", "Data Engineer"),
    ("Lead Analyst - Product Analytics", "Data Analyst"),
    ("NetSuite Functional Analyst", "Business Analyst"),
    ("Staff Applied AI Scientist", "Data Scientist"),
    ("Principal Research Scientist - Evaluations", "Data Scientist"),
    # not one of the 11 roles
    ("Engineering Manager - Data", OTHER),                      # management
    ("Senior Production Engineering Manager", OTHER),           # "Engineering" is not "engineer"
    ("Head of Engineering, Workflow & Integration Services", OTHER),
    ("Senior Solutions Engineer - Payments", OTHER),            # pre-sales
    ("Technical Support Engineer - Tier 3", OTHER),             # support
    ("Delivery Solutions Architect", OTHER),
    ("Account Executive, Mid Market", OTHER),
    ("Marketing Analyst", OTHER),                               # an analyst, but not a data or business analyst
    ("", OTHER),
])
def test_title_rules(title, role):
    assert role_of(title) == role


def test_rules_name_only_known_roles():
    with open(Path(__file__).resolve().parents[1] / "data/1_knowledge/taxonomies/role_occupations.csv", encoding="utf-8") as f:
        roles = {line.split(",")[0] for line in f.read().splitlines()[1:]}
    assert {role for role, _ in RULES} <= roles | {OTHER}


def test_classify_keeps_the_columns_and_sorts_by_role():
    ads = pd.DataFrame({"ad_id": ["a", "b"], "source": ["lever", "ashby"], "company": ["X", "Y"],
                        "title": ["Sales Representative", "Data Engineer"], "location": ["Sydney", "Melbourne"],
                        "posted": ["2026-10-01", ""], "snapshot": ["2026-10-16"] * 2, "description": ["t"] * 2, "url": ["u"] * 2})
    out = classify(ads)
    assert list(out.columns) == COLUMNS and out.role.tolist() == ["Data Engineer", OTHER]
