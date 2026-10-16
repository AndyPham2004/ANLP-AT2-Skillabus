"""Drive the Streamlit page (app/Home.py) the way a student would, with no OpenAI key. Run: pytest tests/

The v2 flow (docs/design/): Start -> Inputs -> Results -> Evidence for one skill. Role mode for a role
with ad counts (Data Engineer) and one without (Cybersecurity Analyst), Job seeker mode with the sample ad
and with a browsed ad, the what-if tick box and the plan download. Uses streamlit.testing (AppTest), so no
browser is needed.
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
    import streamlit as st
    st.cache_data.clear()        # Home.py caches analyses per input; a test with another demand table must not reuse them


def start(mode: str) -> AppTest:
    """Open the app and press the card of one of the three user types (elective, job, switch)."""
    at = AppTest.from_file(HOME, default_timeout=300)
    at.run()
    at.button(key=f"role_{mode}").click().run()
    assert not at.exception
    return at


def show_gaps(at: AppTest) -> AppTest:
    at.button(key="show_gaps").click().run()
    assert not at.exception, at.exception
    return at


def open_skill(at: AppTest, n: int | None = None) -> AppTest:
    """Click a skill row on the results page (the first gap unless `n` is given): its evidence page."""
    if n is None:
        n = next(i for i, s in enumerate(at.session_state.result["skills"]) if s["status"] != "have")
    at.button(key=f"open_{n}").click().run()
    assert not at.exception, at.exception
    return at


def show_tab(at: AppTest, tab: str) -> AppTest:
    """Pick a section of the results page: Skills, Your path, Certifications, How this works."""
    at.segmented_control(key="results_tab").set_value(tab).run()
    assert not at.exception, at.exception
    return at


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    parts += [e.label for e in at.expander] + [b.label for b in at.button]
    return "\n".join(str(p) for p in parts)


def pick_role(at: AppTest, role: str) -> None:
    at.pills(key="role_box").set_value(role).run()
    assert not at.exception


def test_start_page_has_the_three_cards():
    at = AppTest.from_file(HOME, default_timeout=300)
    at.run()
    text = page_text(at)
    assert "Find the skills a job wants" in text
    for cta in ("Pick a role →", "Add ad and resume →", "Pick role, add resume →"):
        assert cta in text
    assert "Who you are" in text and "Your inputs" in text and "Results" in text      # the stepper in the top bar
    assert at.button(key="chat_toggle")


def test_role_picker_lists_eleven_roles_with_their_source():
    at = start("switch")
    pills = at.pills(key="role_box")
    assert len(pills.options) == 11 and pills.options[0] == "Data Scientist"
    assert pills.value == "Data Scientist"
    assert "JobsPipe Data Scientist ads, Sep-Oct 2026, full text." in page_text(at)
    pick_role(at, "Cybersecurity Analyst")
    assert "JobsPipe Cybersecurity Analyst ads, Sep-Oct 2026, full text." in page_text(at)   # every role since C2
    assert "No Australian ad counts yet" not in page_text(at)
    assert at.segmented_control(key="stage_box").value == "Studying at UTS"
    assert at.selectbox(key="course_box").value == "C04372"                       # MDSI by default
    at.segmented_control(key="stage_box").set_value("Already working").run()
    assert at.selectbox(key="course_box").value == ""                            # not enrolled


def test_uts_student_is_never_already_working():
    at = start("elective")
    assert at.segmented_control(key="stage_box").options == ["About to enrol", "Studying at UTS"]
    assert at.selectbox(key="course_box").value == "C04372"


def test_role_mode_data_engineer():
    at = start("switch")
    pick_role(at, "Data Engineer")
    assert "JobsPipe Data Engineer ads, Sep-Oct 2026, full text." in page_text(at)
    show_gaps(at)
    text = page_text(at)
    assert "Data Engineer" in text and "skills still to learn" in text
    assert at.segmented_control(key="results_tab").options == ["Skills", "Your path", "Outside UTS", "Certifications"]
    show_tab(at, "Outside UTS")
    assert "Outside UTS" in page_text(at)
    assert "Bars: share of " in text and "JobsPipe Data Engineer ads, Sep-Oct 2026, full text." in text
    assert "Skills the role asks for" in text and "<span style='width:" in text        # the percentage bars
    show_tab(at, "Your path")
    assert "Your path" in page_text(at) and "closes" in page_text(at)
    show_tab(at, "Certifications")
    text = page_text(at)
    assert "Certifications worth having" in text and "Databricks Certified Data Engineer Associate" in text
    show_tab(at, "Skills")
    open_skill(at)
    text = page_text(at)
    assert "Employers ask" in text and "Learn at UTS" in text and "Self-study" in text
    at.button(key="back_results").click().run()
    assert "Skills the role asks for" in page_text(at)


def test_role_mode_cybersecurity_has_bars_since_c2():
    at = start("switch")
    pick_role(at, "Cybersecurity Analyst")
    show_gaps(at)
    text = page_text(at)
    assert "<span style='width:" in text and "core skills · no Australian ad counts yet" not in text
    show_tab(at, "Certifications")
    text = page_text(at)
    assert "Certifications worth having" in text and "CompTIA Security+" in text
    show_tab(at, "Skills")
    assert "JobsPipe Cybersecurity Analyst ads, Sep-Oct 2026, full text." in page_text(at)
    open_skill(at)
    assert "Employers ask" in page_text(at) and "Self-study" in page_text(at)


def test_role_mode_without_ad_counts_shows_core_skills_without_bars(demand_sample):
    """The fallback page: the sample demand table has no block for Cybersecurity Analyst."""
    at = start("switch")
    pick_role(at, "Cybersecurity Analyst")
    assert "No Australian ad counts yet" in page_text(at)
    show_gaps(at)
    text = page_text(at)
    assert "core skills · no Australian ad counts yet" in text
    assert "<span style='width:" not in text                                          # no percentage bars
    assert "O*NET in-demand tool" in text or "ESCO essential skill" in text        # where each core skill comes from
    show_tab(at, "Certifications")
    text = page_text(at)
    assert "Certifications worth having" in text and "CompTIA Security+" in text
    show_tab(at, "Skills")
    open_skill(at)
    text = page_text(at)
    assert "Core skill" in text
    assert "Self-study" in text and "No self-study resource in our list" not in text   # every core skill has one (D9)


def test_elective_mode_counts_taken_subjects():
    at = start("elective")
    pick_role(at, "Data Engineer")
    picker = at.multiselect(key="taken_box")                  # AppTest lists the options as shown: names, no codes
    assert picker.options[:2] == ["Data Science for Innovation", "Leading Data Science Initiatives"]   # MDSI first
    assert "Big Data Engineering" in picker.options and not any(o.startswith("94693") for o in picker.options)
    picker.set_value(["94693"]).run()
    show_gaps(at)
    assert "94693" not in [r["subject_code"] for r in at.session_state.result["recommendations"]]
    spark = next(s for s in at.session_state.result["skills"] if s["skill_label"] == "Spark")
    assert spark["status"] == "have" and spark["resume_evidence"].startswith("From 94693")


def test_job_seeker_mode_with_the_sample_ad():
    at = start("job")
    assert at.segmented_control(key="ad_mode").value == "Try a sample"
    assert "Robert Walters" in at.text_area(key="ad_box").value
    show_gaps(at)
    text = page_text(at)
    assert "Data Scientist · Robert Walters · Sydney CBD" in text
    assert "Skills the ad asks for" in text
    assert "Certifications" not in at.segmented_control(key="results_tab").options   # no role in this mode
    at.button(key="toggle_ad").click().run()
    assert "<mark" in page_text(at)                                            # skills highlighted on the ad
    open_skill(at)
    text = page_text(at)
    assert "The ad says" in text and "Self-study" in text
    assert "k-dashed" in text                                                  # at least one resource card


def test_self_study_filters_change_the_column():
    at = start("switch")
    pick_role(at, "Data Engineer")
    show_gaps(at)
    open_skill(at)
    at.pills(key="level_filter").set_value([]).run()
    assert not at.exception
    assert "Nothing with these filters: widen the level or cost above." in page_text(at)
    at.segmented_control(key="cost_filter").set_value("Free only").run()
    assert not at.exception


def test_what_if_taken_reruns_the_path():
    at = start("switch")
    pick_role(at, "Data Engineer")
    show_gaps(at)
    path = at.session_state.result["learning_path"]["subjects"]
    assert path
    first = path[0]
    show_tab(at, "Your path")
    at.checkbox(key=f"wi_path_{first}").check().run()                           # "Already taken" on the first card
    assert not at.exception, at.exception
    assert at.session_state.whatif == [first]
    assert first not in at.session_state.result["learning_path"]["subjects"]
    assert "Counting as taken" in page_text(at)
    at.button(key="whatif_reset").click().run()
    assert at.session_state.whatif == [] and first in at.session_state.result["learning_path"]["subjects"]


def test_browse_ads_and_use_one():
    at = start("job")
    at.segmented_control(key="ad_mode").set_value("Browse ads").run()
    assert not at.exception
    assert "Pick a job ad" in page_text(at)
    at.pills(key="job_role").set_value("Data Scientist").run()
    assert at.dataframe                                                          # the ads to pick from
    at.button(key="use_job").click().run()                                       # no row chosen: the newest ad
    assert not at.exception, at.exception
    assert at.session_state.step == "inputs"
    assert len(at.text_area(key="ad_box").value) > 500
    show_gaps(at)
    assert "Skills the ad asks for" in page_text(at)
    assert "Robert Walters" not in page_text(at)


def test_handbook_chat_panel_opens_and_answers():
    at = start("switch")
    at.button(key="chat_toggle").click().run()
    assert "Ask anything about UTS subjects" in page_text(at)
    at.chat_input(key="chat_in").set_value("Which subject teaches machine learning?").run()
    assert not at.exception, at.exception
    assert at.session_state.messages[-1]["role"] == "assistant"
    assert "Handbook" in at.session_state.messages[-1]["content"]
