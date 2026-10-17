"""Drive the Streamlit page (app/Home.py) the way a student would, with no OpenAI key. Run: pytest tests/

One flow for a UTS student (17 Oct): Inputs (course, subjects, resume | a role or a job ad) -> Results ->
Evidence for one skill. A role with ad counts (Data Engineer) and one without (Cybersecurity Analyst), the
sample ad and a browsed ad, subjects taken counted for both goals, the "I've taken this" tick. Uses
streamlit.testing (AppTest), so no browser is needed.
Keys and .env are kept out by conftest.no_live_keys.
"""
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.usefixtures("tfidf_only")   # TF-IDF per test (conftest): fast, the same on every machine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

HOME = str(ROOT / "app" / "Home.py")


@pytest.fixture(autouse=True)
def fresh_analysis_cache():
    import streamlit as st
    st.cache_data.clear()        # Home.py caches analyses per input; a test with another demand table must not reuse them


def open_app() -> AppTest:
    """Open the app: it starts on the Inputs page."""
    at = AppTest.from_file(HOME, default_timeout=300)
    at.run()
    assert not at.exception, at.exception
    return at


def aim_at_an_ad(at: AppTest) -> AppTest:
    at.segmented_control(key="goal_box").set_value("A job ad").run()
    assert not at.exception, at.exception
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
    """Pick a section of the results page: Skills, Your path, Outside UTS, Certifications (role mode only)."""
    at.segmented_control(key="results_tab").set_value(tab).run()
    assert not at.exception, at.exception
    return at


def page_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    parts += [e.label for e in at.expander] + [b.label for b in at.button]
    return "\n".join(str(p) for p in parts)


def family_of(role: str) -> int:
    import backend
    return next(n for n, roles in enumerate(backend.role_families().values()) if role in roles)


def pick_role(at: AppTest, role: str) -> None:
    """The roles are one pills row per family (role_f0 .. role_f4)."""
    at.pills(key=f"role_f{family_of(role)}").set_value(role).run()
    assert not at.exception, at.exception
    assert at.session_state.role_keep == role


def chosen_roles(at: AppTest) -> list:
    return [at.pills(key=f"role_f{n}").value for n in range(5) if at.pills(key=f"role_f{n}").value]


def test_app_opens_on_the_one_inputs_page():
    # 17 Oct (Quan): one user, a UTS student; no "Who you are" cards, no study stage, no "not enrolled".
    at = open_app()
    text = page_text(at)
    assert at.session_state.step == "inputs"
    assert "What you have and where you are heading" in text and "Your goal" in text
    assert "Your inputs" in text and "Results" in text and "Who you are" not in text   # two steps in the top bar
    assert "Pick a role →" not in text and not any(c.key == "stage_box" for c in at.segmented_control)
    course = at.selectbox(key="course_box")
    assert course.value == "C04372" and "" not in course.options                       # MDSI by default, always a course
    assert at.segmented_control(key="goal_box").value == "A role"
    assert at.multiselect(key="taken_box") and at.segmented_control(key="resume_mode")
    assert at.button(key="chat_go")


def test_role_picker_lists_eleven_roles_by_family_with_their_source():
    at = open_app()
    assert sum(len(at.pills(key=f"role_f{n}").options) for n in range(5)) == 11
    assert at.pills(key="role_f0").options[0] == "Data Scientist" and chosen_roles(at) == ["Data Scientist"]
    assert "Data &amp; AI" in page_text(at) and "Cloud &amp; infrastructure" in page_text(at)   # family names, escaped
    assert "JobsPipe Data Scientist ads, Sep-Oct 2026, full text." in page_text(at)
    pick_role(at, "Cybersecurity Analyst")
    assert chosen_roles(at) == ["Cybersecurity Analyst"]                               # one role across the rows
    assert "JobsPipe Cybersecurity Analyst ads, Sep-Oct 2026, full text." in page_text(at)   # every role since C2
    assert "No Australian ad counts yet" not in page_text(at)


def test_role_mode_data_engineer():
    at = open_app()
    pick_role(at, "Data Engineer")
    assert "JobsPipe Data Engineer ads, Sep-Oct 2026, full text." in page_text(at)
    show_gaps(at)
    text = page_text(at)
    assert "Data Engineer" in text and "skills still to learn" in text
    assert at.segmented_control(key="results_tab").options == ["Skills", "Your path", "Outside UTS", "Certifications"]
    show_tab(at, "Outside UTS")
    assert "Outside UTS" in page_text(at)
    # the source sits on the heading, how to read the bars on hover (C, 17 Oct: no footnotes)
    assert "<span class='k-swatch'></span>" in text
    assert "<b>Each bar</b>: the share of these ads that name the skill." in text
    assert "JobsPipe Data Engineer ads, Sep-Oct 2026, full text." in text and not at.caption
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


def test_role_mode_without_ad_counts_shows_core_skills_without_bars(demand_sample):
    """The fallback page: the sample demand table has no block for Cybersecurity Analyst."""
    at = open_app()
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


def test_taken_subjects_count_for_a_role():
    at = open_app()
    pick_role(at, "Data Engineer")
    picker = at.multiselect(key="taken_box")                  # AppTest lists the options as shown: names, no codes
    assert picker.options[:2] == ["Data Science for Innovation", "Leading Data Science Initiatives"]   # MDSI first
    assert "Big Data Engineering" in picker.options and not any(o.startswith("94693") for o in picker.options)
    picker.set_value(["94693"]).run()
    show_gaps(at)
    assert "94693" not in [r["subject_code"] for r in at.session_state.result["recommendations"]]
    spark = next(s for s in at.session_state.result["skills"] if s["skill_label"] == "Spark")
    assert spark["status"] == "have" and spark["resume_evidence"].startswith("From 94693")
    # the tick on a path card joins the one list of subjects taken
    show_tab(at, "Your path")
    first = at.session_state.result["learning_path"]["subjects"][0]
    at.checkbox(key=f"wi_path_{first}").check().run()
    assert not at.exception, at.exception
    assert first in at.session_state.taken_keep and "whatif" not in at.session_state
    assert first not in at.session_state.result["learning_path"]["subjects"]


def test_certifications_are_cards_with_the_ad_count():
    # 8A (17 Oct): cards in rows of three, six at first; "hot" carries the ad count, the long reason moves to a note.
    # The counts come from certifications.csv, whose Adzuna counts are refreshed (D11), so they are read, not typed.
    import backend
    certs = backend.certifications("Software Engineer")
    hot = [c for c in certs[:6] if c["hot"].strip().lower() == "yes" and "AU ads" in c["hot_reason"]]
    assert len(certs) > 6 and hot, "the data no longer has a 'Show all' button or a counted hot card"
    at = open_app()
    pick_role(at, "Software Engineer")
    show_gaps(at)
    show_tab(at, "Certifications")
    text = page_text(at)
    assert text.count("class='k-cert'") == 6
    for c in hot:
        assert f"hot · {int(c['au_ads_count']):,} AU ads" in text, c["cert"]
    assert "top third of certificates for" not in text
    at.button(key="certs_all").click().run()
    assert page_text(at).count("class='k-cert'") == len(certs)


def test_skill_page_tells_its_facts_in_one_band():
    # 17 Oct, Quan's pick B: one band (then-and-now bars, coloured lines) instead of three grey cards, and
    # "new skill" in plain words; a student never reads "ESCO".
    at = open_app()
    pick_role(at, "Data Scientist")
    at.multiselect(key="taken_box").set_value(["36118"]).run()
    show_gaps(at)
    skills = at.session_state.result["skills"]
    open_skill(at, next(i for i, s in enumerate(skills) if s["skill_label"] == "Large language models"))
    text = page_text(at)
    assert "class='k-band'" in text and text.count("class='k-tbar'") == 2       # 2019-22 and now
    assert "✦ New skill" in text and "Too new for the EU's official skills list" in text
    assert "Employers barely asked for it before 2022." in text                 # 0% of the 2019-22 ads
    assert "You have it." in text
    assert "ESCO" not in text and "Emerging skill" not in text


def test_subject_picker_enter_picks_one_subject_not_every_match():
    # Typing "Statistical" + Enter added all 8 fuzzy matches via "Select 8 matches" (17 Oct UI check).
    from streamlit.proto.MultiSelect_pb2 import MultiSelect
    at = open_app()
    picker = at.multiselect(key="taken_box").proto
    assert picker.select_all == 0                                   # no "Select N matches" row
    assert picker.filter_mode == MultiSelect.DESCRIPTOR.fields_by_name["filter_mode"].enum_type \
        .values_by_name["FILTER_MODE_CONTAINS"].number              # "Statistical" no longer finds "Fundamentals of ..."


def test_skill_page_tells_apart_dropped_subjects_that_share_a_name():
    # Two "Database" subjects of other courses printed the same caption twice (17 Oct UI check).
    at = open_app()
    pick_role(at, "Data Scientist")
    at.segmented_control(key="resume_mode").set_value("No resume").run()       # SQL stays a gap
    at.multiselect(key="taken_box").set_value(["36103", "36118"]).run()
    show_gaps(at)
    open_skill(at, next(i for i, s in enumerate(at.session_state.result["skills"]) if s["skill_label"] == "SQL"))
    import re
    notes = re.findall(r"<div class='k-tipline'>(<b>[^<]*</b> also teaches it[^<]*)</div>", page_text(at))
    assert len(notes) >= 2 and len(set(notes)) == len(notes), notes      # up to five, each named apart


def scroll_scripts(at: AppTest) -> list:
    return [h for h in at.get("html") if "scrollTo" in h.proto.body]


def test_a_new_page_starts_at_the_top():
    # A skill opened from low in the list kept the list's scroll offset (17 Oct UI check).
    at = open_app()
    pick_role(at, "Data Engineer")
    show_gaps(at)
    assert scroll_scripts(at)                                       # inputs -> results
    show_tab(at, "Your path")
    assert not scroll_scripts(at)                                   # a tab of the same page stays where it is
    show_tab(at, "Skills")
    open_skill(at)
    assert scroll_scripts(at)                                       # results -> one skill
    at.segmented_control(key="cost_filter").set_value("Free only").run()
    assert not scroll_scripts(at)                                   # a filter on the same page too


def test_the_sample_ad_as_the_goal():
    at = aim_at_an_ad(open_app())
    assert at.segmented_control(key="ad_mode").value == "Try a sample"
    assert "Robert Walters" in at.session_state.ad_keep
    assert "Data Scientist · Robert Walters · Sydney CBD" in page_text(at)                  # the ad as a card
    show_gaps(at)
    text = page_text(at)
    assert "Data Scientist · Robert Walters · Sydney CBD" in text
    assert "Skills the ad asks for" in text
    assert "Certifications" not in at.segmented_control(key="results_tab").options   # no role for an ad
    at.button(key="toggle_ad").click().run()
    assert "<mark" in page_text(at)                                            # skills highlighted on the ad
    open_skill(at)
    text = page_text(at)
    assert "The ad says" in text and "Self-study" in text
    assert "class='k-band'" in text and ("Missing." in text or "Partly." in text)     # a gap: rose or amber line
    assert "class='k-dashed'" in text          # a self-study card; ui.CSS names .k-dashed, so not the bare word
    at.button(key="back_results").click().run()
    open_skill(at, next(i for i, s in enumerate(at.session_state.result["skills"]) if s["skill_label"] == "SQL"))
    assert "<b>You have it.</b> Your resume says: “" in page_text(at)        # the line names where it comes from


def test_terms_outside_the_vocabulary_are_shown_apart_and_not_counted():
    # What augment_with_llm() lists apart (no key in tests, so it is set by hand) gets one line, no rows.
    at = aim_at_an_ad(open_app())
    show_gaps(at)
    res = dict(at.session_state.result)
    n = len(res["skills"])
    at.session_state.result = {**res, "also_in_ad": ["Metaflow", "problem framing"]}
    at.run()
    assert not at.exception, at.exception
    text = page_text(at)
    assert "<b>2</b> outside our list" in text and "Also in the ad: Metaflow, problem framing." in text
    assert f"of {n}</span>" in text and "Metaflow" not in [b.label for b in at.button]


def test_self_study_filters_change_the_column():
    import backend
    import ui
    role = "Software Engineer"
    at = open_app()
    pick_role(at, role)
    show_gaps(at)
    skills = at.session_state.result["skills"]

    def titles(label, cost):
        return [r["title"] for r in backend.self_study(label, backend.LEVELS, backend.COST_CHOICES[cost], role)]
    # A gap whose column "Free only" changes; resources.csv decides which, so it is looked up, not typed.
    n = next((i for i, s in enumerate(skills) if s["status"] != "have"
              and titles(s["skill_label"], "Free only") != titles(s["skill_label"], "Include free-to-audit")), None)
    assert n is not None, "no gap of the role has a free-to-audit resource any more"
    label = skills[n]["skill_label"]
    open_skill(at, n)
    at.pills(key="level_filter").set_value([]).run()
    assert not at.exception
    assert "Nothing with these filters: widen the level or cost above." in page_text(at)
    at.pills(key="level_filter").set_value(list(backend.LEVELS)).run()
    at.segmented_control(key="cost_filter").set_value("Free only").run()
    assert not at.exception, at.exception
    text = page_text(at)
    free, audit = titles(label, "Free only"), titles(label, "Include free-to-audit")
    assert all(ui.esc(t) in text for t in free)
    assert not any(ui.esc(t) in text for t in set(audit) - set(free))


def test_taken_tick_reruns_the_path_and_shows_on_the_inputs_page():
    at = open_app()
    pick_role(at, "Data Engineer")
    show_gaps(at)
    path = at.session_state.result["learning_path"]["subjects"]
    assert path
    first = path[0]
    show_tab(at, "Your path")
    at.checkbox(key=f"wi_path_{first}").check().run()                           # "I've taken this" on the first card
    assert not at.exception, at.exception
    assert at.session_state.taken_keep == [first]
    assert first not in at.session_state.result["learning_path"]["subjects"]
    assert "1 subject taken" in page_text(at)                                   # the top bar says so
    at.button(key="back_inputs").click().run()
    assert at.multiselect(key="taken_box").value == [first]                     # the same list on the Inputs page


def test_browse_ads_opens_an_ad_in_place_and_uses_it():
    # C (17 Oct): family tabs with their counts, one line per ad; an ad opens under its line with "Use this ad",
    # the whole text in a dialog only on "Read the full ad". The ads are 2026 ones for all 11 roles.
    import re

    import ads
    import ui
    at = aim_at_an_ad(open_app())
    at.segmented_control(key="ad_mode").set_value("Browse ads").run()
    assert not at.exception
    assert "Pick a job ad" in page_text(at)
    tabs = at.segmented_control(key="job_family")
    n_cloud = len(ads.search(family="Cloud & infrastructure", limit=None))
    assert tabs.options[0] == f"All · {len(ads.load()):,}" and f"Cloud & infrastructure · {n_cloud:,}" in tabs.options
    tabs.set_value("Data & AI").run()
    at.selectbox(key="job_role").set_value("Data Scientist").run()
    assert not at.exception, at.exception
    # A job-board ad, whose text is in git, so the test does not need the JobsPipe fetch in data/raw/.
    first = next(a for a in ads.search(role="Data Scientist", limit=None) if a["skills"] is None)
    at.text_input(key="job_q").set_value(first["title"]).run()
    at.button(key=f"ad_{first['id']}").click().run()                            # opens the ad in place
    assert not at.exception, at.exception
    assert at.session_state.ad_open == first["id"] and at.button(key="use_job")
    assert not any("class='k-preview'" in m.value for m in at.markdown)         # no dialog yet
    at.button(key="ad_full_btn").click().run()                                  # the whole ad
    assert not at.exception, at.exception
    # The dialog folds runs of blank lines and escapes the text, so an ad with ' or & would miss the raw slice.
    shown = ui.esc(re.sub(r"\n\s*\n\s*\n+", "\n\n", first["text"]))[:80]
    assert any(shown in m.value for m in at.markdown)
    at.button(key="use_job").click().run()
    assert not at.exception, at.exception
    assert at.session_state.step == "inputs" and at.session_state.ad_full is None
    assert at.session_state.ad_keep == first["text"] and ui.esc(first["title"]) in page_text(at)   # the ad as a card
    show_gaps(at)
    assert "Skills the ad asks for" in page_text(at)
    assert "Robert Walters" not in page_text(at)


def test_browse_ads_lists_thirty_then_more():
    import ads
    at = aim_at_an_ad(open_app())
    at.segmented_control(key="ad_mode").set_value("Browse ads").run()
    assert sum((b.key or "").startswith("ad_") for b in at.button if b.key not in ("ad_full_btn",)) == 30
    text = page_text(at)
    assert f">{len(ads.load()):,} ads <span class='k-tip" in text and ", newest first (showing 30)" in text
    at.button(key="jobs_more").click().run()
    assert sum((b.key or "").startswith("ad_") for b in at.button) == 60


def test_a_jobspipe_ad_without_its_text_offers_the_original(monkeypatch, tmp_path):
    # A fresh clone or the deployed app has no data/raw/: the ad lists with its skills and link, and cannot be used.
    import ads
    monkeypatch.setattr(ads.paths, "RAW", tmp_path)
    ads.jobspipe_texts.cache_clear()
    ads.load.cache_clear()
    try:
        at = aim_at_an_ad(open_app())
        at.segmented_control(key="ad_mode").set_value("Browse ads").run()
        first = next(a for a in ads.search() if a["id"].startswith("jp-"))
        at.button(key=f"ad_{first['id']}").click().run()
        assert not at.exception, at.exception
        assert "The text of this ad is not on this machine" in page_text(at)
        assert not any(b.key in ("use_job", "ad_full_btn") for b in at.button)
    finally:
        ads.jobspipe_texts.cache_clear()
        ads.load.cache_clear()


def test_an_open_ad_closes_on_a_second_click():
    import ads
    at = aim_at_an_ad(open_app())
    at.segmented_control(key="ad_mode").set_value("Browse ads").run()
    first = ads.search()[0]
    at.button(key=f"ad_{first['id']}").click().run()
    assert at.session_state.ad_open == first["id"]
    at.button(key=f"ad_{first['id']}").click().run()
    assert at.session_state.ad_open is None and not any(b.key == "use_job" for b in at.button)


def test_browse_ads_says_1_ad():
    import ads
    # A company with exactly one ad in the committed file, found rather than typed: the file is rebuilt.
    query = next((a["company"].lower() for a in ads.load() if len(ads.search(a["company"].lower())) == 1), None)
    assert query, "no company has exactly one ad"
    at = aim_at_an_ad(open_app())
    at.segmented_control(key="ad_mode").set_value("Browse ads").run()
    at.text_input(key="job_q").set_value(query).run()
    assert ">1 ad <span class='k-tip" in page_text(at)


def test_handbook_chat_is_its_own_page_and_names_no_codes():
    # 6B (17 Oct): a page with a way back, not a column that squeezes the results; no subject codes.
    import re
    at = open_app()
    pick_role(at, "Data Engineer")
    show_gaps(at)
    show_tab(at, "Your path")
    at.button(key="chat_go").click().run()
    assert not at.exception, at.exception
    assert at.session_state.step == "chat"
    suggestions = [b.label for b in at.button if (b.key or "").startswith("chat_sug_")]
    assert len(suggestions) == 3 and not any(re.search(r"\b\d{5}\b", s) for s in suggestions)
    at.button(key="chat_sug_0").click().run()                                   # "Which subject teaches LLMs?"
    assert not at.exception, at.exception
    reply = at.session_state.messages[-1]
    assert reply["role"] == "assistant" and "Applied Natural Language Processing" in reply["content"]
    assert not re.search(r"\b\d{5}\b", reply["content"]), reply["content"]
    question, n = "Which subject teaches machine learning?", len(at.session_state.messages)
    at.chat_input(key="chat_in").set_value(question).run()
    assert not at.exception, at.exception
    new = at.session_state.messages[n:]                       # the suggestion's reply is already the last message
    assert [m["role"] for m in new] == ["user", "assistant"] and new[0]["content"] == question
    at.button(key="chat_back").click().run()
    assert at.session_state.step == "results" and at.session_state.results_tab == "Your path"


def test_taken_subjects_count_for_a_job_ad_and_ask_for_the_resume():
    # 17 Oct: a skill the student has from a subject counts as "have" for an ad too, flagged as not on the resume.
    at = aim_at_an_ad(open_app())
    at.multiselect(key="taken_box").set_value(["36120"]).run()                  # Advanced Machine Learning Application
    show_gaps(at)
    skills = at.session_state.result["skills"]
    ml = next(s for s in skills if s["skill_label"] == "Machine learning")
    assert ml["status"] == "have" and ml["resume_evidence"].startswith("From 36120")
    assert "36120" not in [r["subject_code"] for r in at.session_state.result["recommendations"]]
    text = page_text(at)
    assert "not on CV</span>" in text and "<b>machine learning</b> · from Advanced Machine Learning Application" in text
    # its row says so in amber, not as a plain "have" (17 Oct: the note under the list was easy to miss)
    from_subjects = sum((s["resume_evidence"] or "").endswith("(taken)") for s in skills)
    assert page_text(at).count("have · not on CV") == from_subjects >= 1
    open_skill(at, next(i for i, s in enumerate(skills) if s["skill_label"] == "Machine learning"))
    text = page_text(at)
    assert "you have it · not on your CV" in text
    assert "a subject you have taken. Your resume does not mention it: add it." in text


def test_a_skill_from_a_subject_without_a_resume_is_a_plain_have():
    at = open_app()
    at.segmented_control(key="resume_mode").set_value("No resume").run()
    at.multiselect(key="taken_box").set_value(["36120"]).run()
    show_gaps(at)
    assert any((s["resume_evidence"] or "").endswith("(taken)") for s in at.session_state.result["skills"])
    assert "not on CV" not in page_text(at) and "not on your resume" not in page_text(at)


def test_no_resume_counts_only_the_subjects():
    at = open_app()
    at.segmented_control(key="resume_mode").set_value("No resume").run()
    assert not at.exception, at.exception
    assert "No resume and no subject yet: every skill counts as a gap." in page_text(at)
    show_gaps(at)
    skills = at.session_state.result["skills"]
    assert at.session_state.resume_text == "" and all(s["status"] == "missing" for s in skills)
    assert "not on CV" not in page_text(at)


def test_start_over_clears_the_inputs():
    at = open_app()
    pick_role(at, "Data Engineer")
    at.multiselect(key="taken_box").set_value(["94693"]).run()
    show_gaps(at)
    at.button(key="start_over").click().run()
    assert not at.exception, at.exception
    assert at.session_state.step == "inputs" and at.session_state.result is None
    assert at.session_state.taken_keep == [] and at.session_state.role_keep == "Data Scientist"
    assert at.multiselect(key="taken_box").value == [] and chosen_roles(at) == ["Data Scientist"]


def test_no_footnotes_on_the_results_and_skill_pages():
    # C (17 Oct): counts and short labels on top, the details on hover; no caption under a list or a row of cards.
    at = open_app()
    pick_role(at, "Data Engineer")
    at.multiselect(key="taken_box").set_value(["94693"]).run()                   # Big Data Engineering
    show_gaps(at)
    for tab in ("Skills", "Your path", "Outside UTS", "Certifications"):
        show_tab(at, tab)
        assert not at.caption, (tab, [c.value for c in at.caption])
    text = page_text(at)
    assert "class='k-tip" in text and "<b>hot</b>: in the top third of certificates" in text
    show_tab(at, "Skills")
    open_skill(at)
    assert not at.caption, [c.value for c in at.caption]
    assert all(b.help for b in at.button if (b.key or "").startswith(("up_", "down_")))   # the votes say why on hover


def test_generic_one_word_skills_are_lower_case_in_running_text():
    src = (ROOT / "app" / "Home.py").read_text(encoding="utf-8")
    start, end = src.index("# One-word skills that are concepts"), src.index("def read_resume(")
    ns = {}
    exec(src[start:end], ns)
    assert ns["lc"]("Statistics") == "statistics" and ns["lc"]("Teamwork") == "teamwork"
    assert ns["lc"]("Python") == "Python" and ns["lc"]("Spring") == "Spring" and ns["lc"]("Tableau") == "Tableau"
    assert ns["lc"]("Machine learning") == "machine learning" and ns["lc"]("Power BI") == "Power BI"
