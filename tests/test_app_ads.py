"""The ads the app offers to browse (app/ads.py) and the ad highlighter (app/ui.py)."""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))

import ads  # noqa: E402
import ui  # noqa: E402


@pytest.fixture
def no_raw_fetch(monkeypatch, tmp_path):
    """A machine without data/raw/ (a fresh clone, the deployed app): the JobsPipe texts are not there."""
    monkeypatch.setattr(ads.paths, "RAW", tmp_path)
    ads.jobspipe_texts.cache_clear()
    ads.load.cache_clear()
    yield tmp_path
    ads.jobspipe_texts.cache_clear()
    ads.load.cache_clear()


def test_the_ads_are_the_2026_ones_for_all_eleven_roles():
    # Quan, 17 Oct: the newest sources only. JobsPipe 2026 for all 11 roles, plus the job-board ads with an IT role.
    import pandas as pd
    rows = ads.load()
    jobspipe = pd.read_csv(ads.paths.JOBSPIPE_SKILLS, dtype=str)
    assert sum(a["id"].startswith("jp-") for a in rows) == len(jobspipe)
    assert {a["role"] for a in rows} == set(ads.roles_of(None)) and len(ads.roles_of(None)) == 11
    assert min(a["posted"] for a in rows) >= "2026-08"
    assert [a["posted"] for a in rows] == sorted((a["posted"] for a in rows), reverse=True)
    keys = [ads._key(a["company"], a["title"]) for a in rows if not a["id"].startswith("jp-")]
    jp_keys = {ads._key(a["company"], a["title"]) for a in rows if a["id"].startswith("jp-")}
    assert keys and not set(keys) & jp_keys and len(keys) == len(set(keys))   # a job-board ad JobsPipe has: once
    assert all(len(a["text"]) >= 500 for a in rows if a["skills"] is None)    # the job-board text is in git


def test_jobspipe_text_comes_only_from_the_raw_fetch(no_raw_fetch):
    import json
    rows = ads.load()
    jp = [a for a in rows if a["id"].startswith("jp-")]
    assert jp and not any(a["text"] for a in jp) and all(a["skills"] is not None for a in jp)   # listed, no text
    (no_raw_fetch / "jobspipe").mkdir()
    one = jp[0]
    (no_raw_fetch / "jobspipe" / "2026-10-16_x.json").write_text(
        json.dumps([{"id": one["id"][3:], "description": "We need SQL and Python."}]), encoding="utf-8")
    ads.jobspipe_texts.cache_clear()
    ads.load.cache_clear()
    assert ads.by_id(one["id"])["text"] == "We need SQL and Python."


def test_places_are_short():
    assert ads.short_location("Sydney, New South Wales, Australia") == "Sydney, NSW"
    assert ads.short_location("Sydney, Sydney Region") == "Sydney"
    assert ads.short_location("") == "Australia"
    # the job boards' own spellings (17 Oct)
    assert ads.short_location("Sydney NSW 2000") == "Sydney, NSW"
    assert ads.short_location("Melbourne VIC") == "Melbourne, VIC"
    assert ads.short_location("Australian Capital Territory, Australia") == "ACT"
    assert ads.short_location("AU - HQ - NSW") == "NSW"
    assert ads.short_location("AU - Sydney") == "Sydney"
    assert ads.short_location("AU: Melbourne: (260 Burwood Rd)") == "Melbourne"
    assert ads.short_location("Greater Sydney Area") == "Sydney"
    assert ads.short_location("Sydney or Melbourne") == "Sydney or Melbourne"


def test_search_filters_combine():
    scientists = ads.search(role="Data Scientist", limit=None)
    assert scientists and all(a["role"] == "Data Scientist" for a in scientists)
    cloud = ads.search(family="Cloud & infrastructure", limit=None)
    assert {a["role"] for a in cloud} == {"Cloud Engineer", "DevOps/SRE", "Network/Systems Administrator"}
    assert not ads.search(role="Data Scientist", family="Security")              # a role outside the family
    sydney = ads.search(role="Data Scientist", location="Sydney")
    assert sydney and all("sydney" in (a["location"] + a["text"][:300]).lower() for a in sydney)
    power_bi = ads.search("power bi", limit=None)                               # the skills found at fetch time count
    assert any("Power BI" in (a["skills"] or []) and "power bi" not in a["title"].lower() for a in power_bi)
    assert ads.search(query="zzzz-no-such-skill") == []
    assert len(ads.search(limit=5)) == 5 and len(ads.search(limit=None)) == len(ads.load())


def test_highlight_marks_every_mention_in_its_skill_s_colour():
    # One mark per mention (Python twice). Of two overlapping matches the longest wins, whatever the order of
    # the skills: "SQL Server" over "SQL", "Deep learning" over "learning". The rest of the ad is escaped.
    text = "Strong Python & SQL Server <3. Deep learning is a plus; Python again."
    skills = [{"skill_label": "Python", "status": "have"}, {"skill_label": "SQL", "status": "missing"},
              {"skill_label": "SQL Server", "status": "have"}, {"skill_label": "learning", "status": "missing"},
              {"skill_label": "Deep learning", "status": "partial"}]
    html = ui.highlight(text, skills, lambda label: re.compile(re.escape(label), re.I))
    marks = re.findall(r"<mark style='[^']*border-bottom-color:([^']+)'>([^<]*)</mark>", html)
    assert marks == [(ui.HAVE, "Python"), (ui.HAVE, "SQL Server"), (ui.PARTIAL, "Deep learning"), (ui.HAVE, "Python")]
    assert "</mark> &amp; <mark" in html and "&lt;3" in html and "<3" not in html


# ------------------------------------------------- "Use this ad" without the raw text (17 Oct: the deployed app)

class _Reply:
    status_code = 200

    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


def test_a_jobspipe_ad_records_the_fetch_it_came_from(no_raw_fetch):
    jp = [a for a in ads.load() if a["id"].startswith("jp-")]
    assert jp and {a["fetched"] for a in jp} <= set(ads.FETCH_KEYS)


def test_the_full_text_comes_from_the_api_with_the_key_that_fetched_the_ad(monkeypatch):
    """That key paid for the ad this month, so JobsPipe returns it again without a credit."""
    calls = []

    def post(url, json, headers, timeout):
        calls.append((json, headers))
        return _Reply({"data": [{"id": "123", "description": "Full text of the ad."}], "metadata": {}})

    monkeypatch.setenv(ads.FETCH_KEYS["2026-10-17b"], "key-3")
    assert ads.fetch_text({"id": "jp-123", "fetched": "2026-10-17b"}, post=post) == "Full text of the ad."
    assert calls[0][0]["job_ids"] == ["123"] and calls[0][1]["Authorization"] == "Bearer key-3"


def test_no_key_or_a_failing_api_gives_no_text(monkeypatch):
    ad = {"id": "jp-123", "fetched": "2026-10-16"}
    monkeypatch.delenv(ads.FETCH_KEYS["2026-10-16"], raising=False)
    assert ads.fetch_text(ad, post=lambda *a, **k: _Reply({"data": [{"description": "x"}]})) is None
    monkeypatch.setenv(ads.FETCH_KEYS["2026-10-16"], "key-1")

    def down(*a, **k):
        raise OSError("JobsPipe is down")

    assert ads.fetch_text(ad, post=down) is None
    assert ads.fetch_text({"id": "ats-1", "fetched": ""}, post=down) is None          # not a JobsPipe ad


def test_without_its_text_an_ad_is_analysed_from_the_skills_it_named():
    from skillabus.extract import extract
    from skillabus.roles import role_of
    ad = {"id": "jp-1", "title": "Senior Cyber Security Analyst", "company": "Acme", "location": "Sydney",
          "fetched": "2026-10-17", "url": "https://example.com/ad", "skills": ["SIEM", "R", "Communication", "Incident response"]}
    text = ads.skills_text(ad)
    assert role_of(text.splitlines()[0]) == "Cybersecurity Analyst"          # the title stays the first line
    assert {m["canonical"] for m in extract(text)} >= set(ad["skills"])       # every skill is found again
    assert len(text.split()) > 20                                             # enough words for the Inputs page


def test_home_copies_every_jobspipe_key_from_the_streamlit_secrets():
    home = (ROOT / "app" / "Home.py").read_text(encoding="utf-8")
    assert all(f'"{name}"' in home for name in ads.FETCH_KEYS.values())
