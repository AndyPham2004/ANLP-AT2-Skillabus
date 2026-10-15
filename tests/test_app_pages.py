"""Drive the Streamlit page (app/Home.py) the way a student would, with no OpenAI key. Run: pytest tests/

Role mode for a role with ad counts (Data Engineer) and one without (Cybersecurity Analyst), and Job
seeker mode with the sample ad; each must render the Self-study column and, in role mode, the
certifications. Uses streamlit.testing (AppTest), so no browser is needed.
"""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SKILLABUS_NO_EMBED", "1")   # TF-IDF: fast, and the same on every machine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

HOME = str(ROOT / "app" / "Home.py")


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)   # a local .env must not add a key


def start(mode: str) -> AppTest:
    """Open the app and press Start on one of the three cards (elective, job, switch)."""
    at = AppTest.from_file(HOME, default_timeout=300)
    at.run()
    at.button(key=f"role_{mode}").click().run()
    assert not at.exception
    return at


def show_gaps(at: AppTest) -> AppTest:
    at.button(key="show_gaps").click().run()
    assert not at.exception, at.exception
    return at


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    parts += [e.label for e in at.expander]
    return "\n".join(str(p) for p in parts)


def pick_role(at: AppTest, family: str, role: str) -> None:
    at.radio(key="family_box").set_value(family).run()
    at.selectbox(key="role_box").set_value(role).run()
    assert not at.exception


def test_role_picker_lists_eleven_roles_by_family():
    at = start("switch")
    assert at.radio(key="family_box").options == ["Data & AI", "Software", "Cloud & infrastructure", "Security",
                                                  "Business analysis"]
    assert at.selectbox(key="role_box").value == "Data Scientist"
    assert "3,204 Seek Data Scientist ads 2019-22, full text" in page_text(at)
    at.radio(key="family_box").set_value("Security").run()
    assert at.selectbox(key="role_box").value == "Cybersecurity Analyst"       # the new family's first role
    assert "No Australian ad counts yet" in page_text(at)
    assert "More roles once the 2026 ads are in" not in page_text(at)


def test_role_mode_data_engineer():
    at = start("switch")
    pick_role(at, "Data & AI", "Data Engineer")
    assert "4,438 Australian Data Engineer postings 2023" in page_text(at)
    show_gaps(at)
    text = page_text(at)
    assert "a Data Engineer role" in text
    assert "How often employers ask for each skill" in text
    assert at.get("vega_lite_chart")                                     # the percentage bars
    assert "Learn at UTS" in text and "Self-study" in text
    assert "Certifications worth having" in text and "Databricks Certified Data Engineer Associate" in text
    assert "Engine: pipeline" in text


def test_role_mode_cybersecurity_shows_core_skills_without_bars():
    at = start("switch")
    pick_role(at, "Security", "Cybersecurity Analyst")
    show_gaps(at)
    text = page_text(at)
    assert "Core skills of the role" in text and "No percentages" in text
    assert "How often employers ask for each skill" not in text
    assert "Self-study" in text and "ATT&CK Fundamentals Training" in text
    assert "Certifications worth having" in text and "CompTIA Security+" in text
    assert not at.get("vega_lite_chart")                                 # no percentage chart


def test_elective_mode_counts_taken_subjects():
    at = start("elective")
    pick_role(at, "Data & AI", "Data Engineer")
    at.multiselect(key="taken_box").set_value(["94693"]).run()
    show_gaps(at)
    assert "94693" not in [r["subject_code"] for r in at.session_state.result["recommendations"]]
    spark = next(s for s in at.session_state.result["skills"] if s["skill_label"] == "Spark")
    assert spark["status"] == "have" and spark["resume_evidence"].startswith("From 94693")


def test_job_seeker_mode_with_the_sample_ad():
    at = start("job")
    next(b for b in at.button if b.label.startswith("Use the sample ad")).click().run()
    show_gaps(at)
    text = page_text(at)
    assert "this ad" in text
    assert "The ad says" in text and "Learn at UTS" in text and "Self-study" in text
    assert "· free</span>" in text                                             # at least one resource listed
    assert "Certifications worth having" not in text                           # no role in this mode


def test_self_study_filters_change_the_column():
    at = start("switch")
    pick_role(at, "Data & AI", "Data Engineer")
    show_gaps(at)
    at.multiselect(key="level_filter").set_value([]).run()
    assert not at.exception
    assert "Nothing with these filters: widen the level or cost above." in page_text(at)
    at.radio(key="cost_filter").set_value("Free only").run()
    assert not at.exception
