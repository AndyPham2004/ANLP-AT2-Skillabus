"""classify_ats_roles.py (plan D2, #116): the title rules that give a 2026 job-board ad its role."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from classify_ats_roles import COLUMNS, MAX_AGE_DAYS, OTHER, RULES, classify, read_raw, role_of  # noqa: E402


@pytest.mark.parametrize("title, role", [
    ("Senior Software Engineer, AI Tooling (Information Security)", "Software Engineer"),   # "Software Engineer" wins
    ("Staff Engineer", "Software Engineer"),
    ("Senior Java Developer", "Software Engineer"),
    ("Senior Engineer - ML Systems (AI Products)", "Machine Learning Engineer"),
    ("Senior Machine Learning Engineer", "Machine Learning Engineer"),
    ("Principal AI Platform Engineer", "Machine Learning Engineer"),
    ("Lead AI Security Engineer", "Cybersecurity Analyst"),                                # security before AI
    ("Senior Cyber Security Analyst", "Cybersecurity Analyst"),
    ("Senior Threat Detection Analyst", "Cybersecurity Analyst"),
    ("Senior DevOps Support Engineer", "DevOps/SRE"),                                     # devops before "support"
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


def test_read_raw_keeps_fresh_ads_once(tmp_path):
    # Two fetches: an evergreen ad from 2019, a fresh ad listed in two cities, a fresh ad seen on both days.
    cols = "ad_id,source,title,company,location,created,description,redirect_url"
    long = "x" * 250
    (tmp_path / "ats_ads_2026-10-13.csv").write_text(
        f"{cols}\n1,lever,Software Engineer,A,Sydney,2019-05-01T00:00:00Z,{long},u1\n"
        f"2,lever,Data Engineer,A,Sydney,2026-10-01T00:00:00Z,{long},u2\n"
        f"3,lever,Data Engineer,A,Melbourne,2026-10-01T00:00:00Z,{long},u3\n", encoding="utf-8")
    (tmp_path / "ats_ads_2026-10-16.csv").write_text(
        f"{cols}\n2,lever,Data Engineer,A,Sydney,2026-10-01T00:00:00Z,{long},u2\n"
        f"4,ashby,Data Analyst,B,Sydney,,{long},u4\n", encoding="utf-8")
    ads = read_raw(sorted(tmp_path.glob("ats_ads_2026-10-*.csv")))
    assert sorted(ads.ad_id) == ["ats-2", "ats-4"]                  # 2019 ad dropped; one row per company + title
    assert ads.set_index("ad_id").loc["ats-2", "snapshot"] == "2026-10-16"   # the latest fetch wins
    assert MAX_AGE_DAYS == 60


def test_classify_keeps_the_columns_and_sorts_by_role():
    ads = pd.DataFrame({"ad_id": ["a", "b"], "source": ["lever", "ashby"], "company": ["X", "Y"],
                        "title": ["Sales Representative", "Data Engineer"], "location": ["Sydney", "Melbourne"],
                        "posted": ["2026-10-01", ""], "snapshot": ["2026-10-16"] * 2, "description": ["t"] * 2, "url": ["u"] * 2})
    out = classify(ads)
    assert list(out.columns) == COLUMNS and out.role.tolist() == ["Data Engineer", OTHER]
