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
    assert ads.role_of("Senior Data Scientist, Personalisation") == "Data Scientist"
    assert ads.role_of("Machine Learning Engineer - AI Platform") == "Machine Learning Engineer"
    assert ads.role_of("Tableau - BI Developer") == "BI Developer"
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


def test_highlight_marks_each_skill_once_in_its_colour():
    text = "Strong Python and SQL. Deep learning is a plus; Python again."
    skills = [{"skill_label": "Python", "status": "have"}, {"skill_label": "SQL", "status": "missing"},
              {"skill_label": "Deep learning", "status": "partial"}]
    html = ui.highlight(text, skills, lambda label: re.compile(re.escape(label), re.I))
    assert html.count("<mark") == 4
    assert f"border-bottom-color:{ui.HAVE}'>Python" in html
    assert f"border-bottom-color:{ui.MISSING}'>SQL" in html
    assert "&lt;" not in html and "Deep learning is a plus" in html.replace("</mark>", "")
