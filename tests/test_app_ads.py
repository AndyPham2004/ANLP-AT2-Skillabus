"""The ads the app offers to browse (app/ads.py) and the ad highlighter (app/ui.py)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "src"))

import ads  # noqa: E402
import ui  # noqa: E402


def test_only_full_text_ads_newest_first():
    rows = ads.load()
    assert 100 <= len(rows) <= 192
    assert all(len(a["text"]) >= 500 for a in rows)
    assert [a["posted"] for a in rows] == sorted((a["posted"] for a in rows), reverse=True)


def test_role_and_location_chips():
    # The chips use the app's role names and show only roles that have ads (17 Oct UI check):
    # AI Engineer ads count as Machine Learning Engineer, BI Developer ads as Data Analyst.
    assert ads.ROLE_CHIPS == ["All roles", "Data Analyst", "Data Engineer", "Data Scientist", "Machine Learning Engineer"]
    assert all(ads.search(role=chip, limit=1) for chip in ads.ROLE_CHIPS[1:])      # no chip that finds no ad
    assert ads.role_of("Senior Data Scientist, Personalisation") == "Data Scientist"
    assert ads.role_of("Machine Learning Engineer - AI Platform") == "Machine Learning Engineer"
    assert ads.role_of("Applied AI Engineer, Codex") == "Machine Learning Engineer"
    assert ads.role_of("Tableau - BI Developer") == "Data Analyst"
    assert ads.role_of("Accountant") == "Other"
    assert ads.short_location("Sydney, New South Wales, Australia") == "Sydney, NSW"
    assert ads.short_location("Sydney, Sydney Region") == "Sydney"
    assert ads.short_location("") == "Australia"


def test_search_filters_combine():
    scientists = ads.search(role="Data Scientist")
    assert scientists and all(a["role"] == "Data Scientist" for a in scientists)
    sydney = ads.search(role="Data Scientist", location="Sydney")
    assert sydney and all("sydney" in (a["location"] + a["text"][:300]).lower() for a in sydney)
    assert ads.search(query="zzzz-no-such-skill") == []
    assert len(ads.search(limit=5)) == 5


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
