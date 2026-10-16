"""The JobsPipe top-up (17 Oct): fetch only ads older than the ones we have, and keep the first fetch's rows."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data-eda" / "src"))

from fetch_jobspipe import (drop_known_tenders, drop_near_duplicates, drop_not_local,  # noqa: E402
                            older_than_kept, union_raw)


def test_each_role_is_asked_only_for_ads_older_than_its_oldest_kept_ad():
    kept = pd.DataFrame({"role": ["Data Scientist", "Data Scientist", "Software Engineer"],
                         "date_posted": ["2026-09-24", "2026-10-16", "2026-10-13"]})
    windows = older_than_kept(kept, since="2026-09-01")
    assert windows["Data Scientist"] == {"posted_at_lte": "2026-09-23", "posted_at_gte": "2026-09-01"}
    assert windows["Software Engineer"] == {"posted_at_lte": "2026-10-12", "posted_at_gte": "2026-09-01"}


def test_a_role_already_past_the_start_date_gets_no_window():
    kept = pd.DataFrame({"role": ["Cloud Engineer"], "date_posted": ["2026-09-01"]})
    assert older_than_kept(kept, since="2026-09-01") == {}


def test_union_keeps_the_first_fetch_when_an_ad_comes_back(tmp_path):
    pd.DataFrame({"ad_id": ["jp-1", "jp-2"], "role_query": ["QA", "QA"], "title": ["a", "b"]}).to_csv(
        tmp_path / "jobspipe_ads_2026-10-16.csv", index=False)
    pd.DataFrame({"ad_id": ["jp-2", "jp-3"], "role_query": ["QA", "QA"], "title": ["b again", "c"]}).to_csv(
        tmp_path / "jobspipe_ads_2026-10-17.csv", index=False)
    raw = union_raw(tmp_path)
    assert raw.ad_id.tolist() == ["jp-1", "jp-2", "jp-3"]
    assert raw.set_index("ad_id").title["jp-2"] == "b"


def test_union_keeps_an_ad_fetched_for_two_roles(tmp_path):
    """'Senior Cloud Engineer - DEVOPS' comes back for the Cloud and the DevOps query; derive() keeps the row
    whose query matches the title, so both rows must reach it."""
    pd.DataFrame({"ad_id": ["jp-1", "jp-1"], "role_query": ["DevOps/SRE", "Cloud Engineer"], "title": ["t", "t"]}).to_csv(
        tmp_path / "jobspipe_ads_2026-10-16.csv", index=False)
    assert union_raw(tmp_path).role_query.tolist() == ["DevOps/SRE", "Cloud Engineer"]


BODY = ("We are seeking a senior cloud engineer to design build and operate secure Azure landing zones for a federal "
        "agency, automate infrastructure with Terraform and pipelines, harden identity and network controls, support "
        "migration of legacy workloads, document patterns and mentor the platform team across a twelve month contract. ")
OTHER = ("Join our data platform squad to build streaming pipelines in Kafka and Spark, model the warehouse in dbt, "
         "run data quality checks, and partner with analysts on dashboards for the retail business units this year. ")


def test_the_same_job_posted_by_two_agencies_counts_once():
    """17 Oct: one federal cloud tender came back from 27 agencies with different names and titles."""
    ads = pd.DataFrame({"ad_id": ["jp-1", "jp-2", "jp-3", "jp-4"],
                        "role": ["Cloud Engineer", "Cloud Engineer", "Cloud Engineer", "DevOps/SRE"],
                        "description": [BODY, "Babylon Data is hiring for our client. " + BODY,
                                        "Babylon Data is hiring for our client. " + OTHER, BODY]})
    assert drop_near_duplicates(ads).ad_id.tolist() == ["jp-1", "jp-3", "jp-4"]


def test_a_tender_rewritten_by_many_agencies_counts_once():
    """23 agencies rewrote one federal Azure + Dynamics 365 tender (16-18 Sep): the texts barely overlap, so
    drop_near_duplicates() cannot see it; KNOWN_TENDERS keeps the first ad."""
    tender = "Azure landing zones and integration with Microsoft Dynamics 365 CRM for a federal agency."
    ads = pd.DataFrame({"ad_id": ["jp-1", "jp-2", "jp-3", "jp-4"],
                        "role": ["Cloud Engineer"] * 4,
                        "title": ["Senior Cloud Architect / Cloud Engineer", "Multiple Cloud Architects / Cloud Engineers",
                                  "Cloud Engineer", "Senior Cloud Architect / Cloud Engineer"],
                        "date_posted": ["2026-09-16", "2026-09-17", "2026-09-17", "2026-10-10"],
                        "description": [tender, "We seek: " + tender, tender, tender]})
    assert drop_known_tenders(ads).ad_id.tolist() == ["jp-1", "jp-3", "jp-4"]


def test_ai_training_gigs_and_foreign_jobs_are_not_australian_demand():
    """Alignerr's 'Cybersecurity Analyst' is remote AI-training work, and a Virginia college job tagged
    'Senior, South Australia' is not an Australian ad; an agency's ordinary ad stays."""
    ads = pd.DataFrame({"ad_id": ["jp-1", "jp-2", "jp-3", "jp-4", "jp-5"],
                        "company": ["Alignerr", "mercor", "UCI-OC Alliance", "Hays", "GitLab"],
                        "title": ["Cloud Security Analyst", "Visual Data Analyst - Fully Remote | Upto $35/hr",
                                  "Senior Network Engineer at Virginia's Community Colleges System",
                                  "Data Analyst | $90/hr | 6 months", "Site Reliability Engineer, Infrastructure Platforms — UK"]})
    assert drop_not_local(ads).ad_id.tolist() == ["jp-4"]
