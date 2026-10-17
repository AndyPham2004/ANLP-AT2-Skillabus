"""Skillabus: which skills a role asks for that you lack, and where to learn each one.

Run from the repo root:  streamlit run app/Home.py

The look follows the v2 design in docs/design/ (Claude Design, 16 Oct 2026), reshaped with Quan on 16-17 Oct:
a top bar with the steps and the "Ask the Handbook" button (the chat is a page of its own), and one user, a UTS
student (no user modes): Inputs (what you have | your goal, a role or a job ad; or Browse ads) -> Results, one
tab at a time -> Evidence for one skill, plus a subject dialog. app/ui.py holds the CSS and the HTML helpers,
app/backend.py calls the pipeline, app/ads.py serves the ads to browse.
"""

from __future__ import annotations

import csv
import io
import os
import re
import threading

from datetime import date, datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
try:  # Streamlit Cloud keeps keys in st.secrets
    for key in ("OPENAI_API_KEY", "LIGHTCAST_CLIENT_ID", "LIGHTCAST_CLIENT_SECRET"):
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = st.secrets[key]
except Exception:
    pass

import backend  # noqa: E402  (puts src/ on sys.path; keep it first)
import ads  # noqa: E402
import baseline  # noqa: E402
import chat  # noqa: E402
import ui  # noqa: E402
from skillabus import paths  # noqa: E402

FEEDBACK_CSV = paths.FEEDBACK
SAMPLE_AD = paths.SAMPLE_AD.read_text(encoding="utf-8")
SAMPLE_RESUME = paths.SAMPLE_RESUME.read_text(encoding="utf-8")
SAMPLE_AD_TITLE = "Data Scientist · Robert Walters · Sydney CBD"
COURSES = backend.courses()                                    # (code, name) for all 44 courses, MDSI first
COURSE_NAME = dict(COURSES)
GOALS = ("A role", "A job ad")
AD_MODES = ("Browse ads", "Paste an ad", "Try a sample")
RESUME_MODES = ("No resume", "Upload a file", "Paste text", "Use a sample")
MIN_AD_WORDS = 20
FAMILIES = backend.role_families()
ROLE_LIST = [role for roles in FAMILIES.values() for role in roles]        # all 11 roles, family by family
ROLE_SHORT = {"Machine Learning Engineer": "ML Engineer"}                   # on its pill: a family fits one line
CORE_SOURCE = {"onet": "O*NET in-demand tool", "esco": "ESCO essential skill"}
CHAT_SUGGESTIONS = ("Which subject teaches LLMs?", "What does Applied NLP cover?", "Where can I learn SQL?")
STEP_OF = {"inputs": 1, "jobs": 1, "results": 2, "evidence": 2}     # the chat page shows the step it came from
CHAT_BACK = {"inputs": "← Back to your inputs", "jobs": "← Back to the ads",
             "results": "← Back to results", "evidence": "← Back to the skill"}
CERTS_SHOWN = 6                                                # then a "Show all" button
SUBJECT_NAME = dict(backend.subjects())                      # code -> name, all 360 subjects


def _subject_labels() -> dict[str, str]:
    """code -> label for the subject picker. A name UTS runs under several codes (the same subject in a
    bachelor, a master and an online master) gets the course that distinguishes it, never the code."""
    courses = backend.subject_courses()
    by_name: dict[str, list[str]] = {}
    for code, name in SUBJECT_NAME.items():
        by_name.setdefault(name, []).append(code)
    out = {}
    for name, codes in by_name.items():
        if len(codes) == 1:
            out[codes[0]] = name
            continue
        qual = {}
        for code in codes:
            first = next((COURSE_NAME[c] for c in courses.get(code, []) if c in COURSE_NAME), None)
            qual[code] = re.sub(r" \(C\d{5}\)$", "", first) if first else "another course"
        for code in codes:
            q = qual[code]
            if list(qual.values()).count(q) > 1:            # same first course too: say which code, last resort
                q = f"{q}, {code}"
            out[code] = f"{name} ({q})"
    return out


SUBJECT_LABEL = _subject_labels()

st.set_page_config(page_title="Skillabus", page_icon="🎓", layout="wide", initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- small helpers

# One-word skills that are concepts, not products: lower case in running text ("statistics", but "Python", "Spring").
GENERIC_ONE_WORD = {"Clustering", "Communication", "Documentation", "Econometrics", "Encryption", "Firewalls",
                    "Leadership", "Microservices", "Observability", "Optimisation", "Probability", "Serverless",
                    "Statistics", "Teamwork"}


def lc(label: str) -> str:
    """Lower-case a generic skill name for running text: "Machine learning" -> "machine learning",
    "Generative AI" -> "generative AI". Product and proper names keep their case ("Azure", "Microsoft Office",
    "SQL Server"): one-word names are left alone except the concepts in GENERIC_ONE_WORD ("Statistics"), and so
    are names whose second word starts with a capital followed by small letters."""
    words = label.split()
    if len(words) < 2:
        return label.lower() if label in GENERIC_ONE_WORD else label
    if not label[1:2].islower():
        return label
    second = words[1]
    if second[:1].isupper() and second[1:2].islower():
        return label
    # "Word ACRONYM" is a product (Power BI, Vertex AI, Azure ML, Argo CD) except these two concepts
    if second.isupper() and label not in ("Generative AI", "Responsible AI"):
        return label
    return label[:1].lower() + label[1:]


def read_resume(upload) -> str:
    if upload is None:
        return ""
    data = upload.getvalue()
    if upload.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    return data.decode("utf-8", errors="ignore")


def save_vote(subject_code: str, skill: str, vote: str, taken: bool) -> None:
    FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)
    new = not FEEDBACK_CSV.exists()
    with FEEDBACK_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "subject_code", "skill_label", "vote", "has_taken_subject"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), subject_code, skill, vote, "y" if taken else "n"])


def enrol_note(r: dict) -> str:
    """When a subject runs and what it needs first (recommend()'s offered, needs, unverified)."""
    parts = []
    if r.get("offered"):
        parts.append("Runs in " + ", ".join(r["offered"]))
    if r.get("needs"):
        parts.append("needs " + names(r["needs"]) + " first")
    elif r.get("unverified"):
        parts.append("prerequisites not confirmed")
    elif r.get("offered"):          # the baseline has no session data, so it claims nothing
        parts.append("no prerequisite")
    return " · ".join(parts)


def resource_html(r: dict) -> str:
    """One self-study resource as a dashed card: title linked, then provider, level, format, hours and cost."""
    hours = f"{r['hours']:g} h" if r["hours"] is not None else "hours not stated"
    cost = f"A${r['cost_aud']}" if r["cost"] == "paid" and r.get("cost_aud") else r["cost"]
    head = (f"<div style='display:flex;justify-content:space-between;gap:10px'>"
            f"<a href='{ui.esc(r['url'])}' target='_blank' style='font-weight:500;font-size:15px'>{ui.esc(r['title'])}</a>"
            f"<span class='k-small k-mute' style='white-space:nowrap'>{ui.esc(cost)} · {ui.esc(hours)}</span></div>")
    meta = (f"<div class='k-small k-mute'>{ui.esc(r['provider'])} · {ui.esc(r['level'])} · "
            f"{ui.esc(r['format'].replace('_', ' '))}</div>")
    return ui.card(head + meta, dashed=True)


HOT_TIP = ("<b>hot</b>: in the top third of certificates that live Australian ads for the role name (Adzuna, "
           "16 Oct 2026), or in the Robert Half 2027 Salary Guide.")
PRICE_TIP = "One exam attempt, from the vendor's page."


def cert_card(c: dict) -> str:
    """One certification as a card: name linked, vendor, level, exam code, exam price, and "hot" with its ad count.
    What "hot" means and where the price comes from show on hover (no note under the cards)."""
    if c["cost_aud"] and c["cost_aud"] != "varies":
        price = "<div>" + ui.tip(f"<span class='k-mono'>A${ui.esc(c['cost_aud'])}</span>", PRICE_TIP) + "</div>"
    else:
        price = "<div class='k-small k-mute'>Exam price varies by country</div>"
    exam = f" · exam {c['exam_code']}" if c["exam_code"] else ""
    hot = ""
    if c.get("hot", "").strip().lower() == "yes":
        n = re.search(r"\((\d[\d,]*) AU ads", c.get("hot_reason") or "")
        hot = ui.tip(ui.chip(f"hot · {n.group(1)} AU ads" if n else "hot · salary guide", colour=ui.PARTIAL), HOT_TIP)
    return (f"<div class='k-cert'><a href='{ui.esc(c['official_url'])}' target='_blank'>{ui.esc(c['cert'])}</a>"
            f"<div class='k-small k-mute'>{ui.esc(c['vendor'])} · {ui.esc(c['level'])}{ui.esc(exam)}</div>"
            f"{price}{hot}</div>")


def subject_name(code: str) -> str:
    """The subject's name; the code is shown only where it is needed (the design hides codes)."""
    return SUBJECT_NAME.get(code, code)


def subject_label(code: str) -> str:
    """Name, plus the course when another subject has the same name."""
    return SUBJECT_LABEL.get(code, subject_name(code))


def names(codes) -> str:
    return " and ".join(subject_name(c) for c in codes)


def regex_for(label: str):
    """The pattern that finds a skill in text: the dictionary's aliases, or the label itself."""
    return baseline.skill_regex(label)


# ---------------------------------------------------------------- state

ss = st.session_state
DEFAULTS = {
    "step": "inputs", "messages": [], "chat_from": "inputs", "ad_open": None, "ad_full": None, "certs_more": False,
    "show_ad": False,
    "show_details": False, "goal_keep": "A role", "ad_keep": "", "ad_mode_keep": "Try a sample", "ad_pick": None,
    "taken_keep": [], "result": None, "engine": "", "ran": False, "gap": None, "resume_text": "",
    "resume_label": None, "role_keep": backend.DEFAULT_ROLE, "course_keep": backend.HOME_COURSE,
    "gpt_keep": backend.llm_enabled(),
    "level_keep": list(backend.LEVELS), "toast": None,
}
for k, v in DEFAULTS.items():
    ss.setdefault(k, v)


def go(step: str, **kw) -> None:
    ss.step = step
    for k, v in kw.items():
        ss[k] = v


def toggle(key: str) -> None:
    ss[key] = not ss[key]


@st.cache_resource(show_spinner=False)
def warm_up() -> threading.Lock:
    """Load the pipeline (embedding model, subject index: about a minute) once per server, in the
    background from the moment the app starts, so the first "Find my gaps" does not pay for it.
    Analyses take the same lock, so one started early simply waits for the load to finish."""
    lock = threading.Lock()

    def load() -> None:
        with lock:
            try:
                backend.analyse(SAMPLE_RESUME, SAMPLE_AD, [], use_llm=False)
            except Exception:
                pass
    threading.Thread(target=load, name="skillabus-warm-up", daemon=True).start()
    return lock


WARM = warm_up()


@st.cache_data(show_spinner=False, max_entries=64, ttl=3600)
def cached_analyse(resume_text: str, ad_text: str | None, taken: tuple[str, ...], role: str,
                   home_course: str | None, use_llm: bool) -> tuple[dict, str]:
    """backend.analyse() once per distinct input, so going back and forth or undoing a what-if is instant.
    Kept in the server's memory for an hour at most; nothing is written to disk."""
    with WARM:
        return backend.analyse(resume_text, ad_text, list(taken), role=role, home_course=home_course,
                               use_llm=use_llm)


def run_analysis() -> None:
    """Run the pipeline on what the Inputs page kept: the resume and the subjects taken against the goal."""
    ad = ss.ad_keep if ss.goal_keep == "A job ad" else None
    # an ad picked from Browse carries its role; backend.analyse reads a pasted ad's role from its first line
    pick = ss.get("ad_pick")
    role = pick["role"] if ad and pick and pick.get("role") and ad.strip() == pick["text"].strip() else ss.role_keep
    result, engine = cached_analyse(ss.resume_text, ad, tuple(sorted(ss.taken_keep)), role,
                                    ss.course_keep or backend.HOME_COURSE, bool(ss.gpt_keep))
    ss.update(result=result, engine=engine, ran=True)


def set_taken(code: str, on: bool) -> None:
    """"I've taken this" on a subject: it joins (or leaves) the one list of subjects taken from the Inputs
    page, and the gaps and the path are recomputed (issue #60)."""
    taken = set(ss.taken_keep)
    (taken.add if on else taken.discard)(code)
    ss.taken_keep = sorted(taken)
    ss.taken_box = list(ss.taken_keep)          # the Inputs page picker shows the same list
    run_analysis()


def taken_from_tick(code: str, key: str) -> None:
    set_taken(code, bool(ss[key]))


def taken_tick(code: str, key: str) -> None:
    """The tick box for one subject; every copy of it shows the same state."""
    ss[key] = code in ss.taken_keep
    st.checkbox("I've taken this", key=key, on_change=taken_from_tick, args=(code, key))


def open_gap(label: str) -> None:
    go("evidence", gap=label)


def vote(code: str, skill: str, value: str) -> None:
    save_vote(code, skill, value, code in ss.taken_keep)
    ss.toast = "Thanks, your vote is saved."


def is_ad(res: dict) -> bool:
    """The result answers a job ad (no role), not a role."""
    return res.get("role") is None


def ad_title() -> str:
    text = (ss.ad_keep or "").strip()
    if text == SAMPLE_AD.strip():
        return SAMPLE_AD_TITLE
    pick = ss.ad_pick
    if pick and text == pick["text"].strip():
        return f"{pick['title']} · {pick['company']} · {pick['location']}"
    return "Pasted ad"


def ad_mode_changed() -> None:
    mode = ss.ad_mode
    if mode is None:                      # a segmented control can be deselected; keep the last choice
        ss.ad_mode = ss.ad_mode_keep
        return
    ss.ad_mode_keep = mode
    if mode == "Browse ads" and not ss.ad_pick:
        ss.step = "jobs"


def keep_goal() -> None:
    if ss.goal_box is None:               # a segmented control can be deselected; a goal is always needed
        ss.goal_box = ss.goal_keep
    ss.goal_keep = ss.goal_box


def pick_role(n: int) -> None:
    """One pills row per role family: a pick in one row clears the others, so one role stays chosen."""
    role = ss[f"role_f{n}"]
    if role is None:                      # pills can be deselected; a role is always needed
        ss[f"role_f{n}"] = ss.role_keep
        return
    ss.role_keep = role
    for i in range(len(FAMILIES)):
        if i != n:
            ss[f"role_f{i}"] = None


def ask(question: str) -> None:
    ss.messages.append({"role": "user", "content": question})
    reply, sources = chat.answer(question, ss.result)
    if sources and chat.has_llm():
        reply += "\n\n" + "  \n".join(f"[{i + 1}] {chat.source_name(s)}" for i, s in enumerate(sources))
    ss.messages.append({"role": "assistant", "content": reply})


def open_chat() -> None:
    if ss.step != "chat":
        ss.chat_from = ss.step
    ss.step = "chat"


# ---------------------------------------------------------------- top bar: steps and the chat button

def inputs_note() -> str:
    """What the Inputs page holds, in a few words for the top bar: the goal, the resume, the subjects."""
    parts = [(ad_title() if ss.ad_keep.strip() else "an ad") if ss.goal_keep == "A job ad" else ss.role_keep]
    if ss.resume_label:
        parts.append(ss.resume_label.lower() if ss.resume_label.endswith(" resume") else ss.resume_label)
    n = len(ss.taken_keep)
    parts.append(f"{n} subject{'' if n == 1 else 's'} taken")
    return " · ".join(parts)


def top_bar() -> None:
    """One strip above every page: the name, the two steps, what was chosen so far, the chat button."""
    current = STEP_OF[ss.chat_from if ss.step == "chat" else ss.step]
    parts = []
    for n, label in enumerate(("Your inputs", "Results"), start=1):
        done, active = current > n, current == n
        colour = ui.HAVE if done else (ui.INK if active else ui.DIM)
        dot = (f"<span class='k-hdot' style='border-color:{colour};background:{ui.HAVE if done else 'transparent'};"
               f"color:{ui.DARK if done else colour}'>{'✓' if done else n}</span>")
        parts.append(f"<span class='k-hstep' style='color:{colour};font-weight:{500 if active else 400}'>{dot}{label}</span>")
    stepper = "<span class='k-hline'></span>".join(parts)
    ctx = inputs_note() if current > 1 else ""
    name_col, steps_col, ctx_col, chat_col = st.columns([1.1, 3.3, 2.6, 1.3], vertical_alignment="center", gap="small")
    name_col.markdown(f"<div class='k-mark' style='margin:0'><span class='k-dot' style='background:{ui.HAVE};"
                      "margin-right:8px;vertical-align:2px'></span>Skillabus</div>", unsafe_allow_html=True)
    steps_col.markdown(f"<div class='k-hsteps'>{stepper}</div>", unsafe_allow_html=True)
    ctx_col.markdown(f"<div class='k-hctx' title='{ui.esc(ctx)}'>{ui.esc(ctx)}</div>", unsafe_allow_html=True)
    chat_col.button("Ask the Handbook", key="chat_go", width="stretch", on_click=open_chat, disabled=ss.step == "chat")
    st.markdown("<div class='k-rule'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- the chat page

def page_chat() -> None:
    """Ask the Handbook as a page of its own (Quan's pick, 17 Oct): a column beside the results squeezed them."""
    st.button(CHAT_BACK.get(ss.chat_from, "← Back"), key="chat_back", type="tertiary", on_click=go, args=(ss.chat_from,))
    st.markdown(ui.h1("Ask the Handbook", "md"), unsafe_allow_html=True)
    st.caption("Answers quote the UTS Handbook 2026. Your resume is never sent to the model."
               + ("" if chat.has_llm() else " No OpenAI key set: the matching passages are shown instead of a written answer."))
    chat_thread()


@st.fragment
def chat_thread() -> None:
    """Suggestions or messages, then the input. A fragment: a question redraws the chat, not the whole page."""
    with st.container(key="chat_box"):           # one reading width (ui.CSS)
        thread = st.container()                  # filled after the input is read, so a new answer shows at once
        question = st.chat_input("Ask a question", key="chat_in")
        if question:
            ask(question)
        with thread:
            if not ss.messages:
                for col, (i, text) in zip(st.columns(3, gap="small"), enumerate(CHAT_SUGGESTIONS)):
                    col.button(text, key=f"chat_sug_{i}", width="stretch", on_click=ask, args=(text,))
            for m in ss.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])


# ---------------------------------------------------------------- step 1: your inputs

def ad_excerpt(text: str, n: int = 210) -> str:
    """The ad's first sentences, skipping a header block of short lines (title, company, place, source)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    start = next((i for i, ln in enumerate(lines) if len(ln.split()) >= 8), 0)
    return short(" ".join(lines[start:]), n)


def ad_card(title: str, meta: str, text: str) -> None:
    st.markdown(ui.card(f"<div style='font-weight:500;font-size:15.5px'>{ui.esc(title)}</div>"
                        + (f"<div class='k-small k-mute'>{ui.esc(meta)}</div>" if meta else "")
                        + f"<div class='k-small k-soft' style='margin-top:6px;line-height:1.5'>"
                          f"{ui.esc(ad_excerpt(text))}</div>"), unsafe_allow_html=True)


def job_ad_block() -> None:
    """Browse the 160 ads (the chosen one as a card), paste one, or use the sample."""
    # Widgets forget their value once off screen, so each keeps a *_keep twin that survives the other pages.
    ss.setdefault("ad_mode", ss.ad_mode_keep)
    st.segmented_control("Where the ad comes from", AD_MODES, key="ad_mode", label_visibility="collapsed",
                         on_change=ad_mode_changed)
    mode = ss.ad_mode or ss.ad_mode_keep
    pick = ss.ad_pick
    if mode == "Browse ads" and pick:
        ad_card(pick["title"], f"{pick['company']} · {pick['location']} · {posted(pick['posted'])}", pick["text"])
        st.button(f"Pick another of the {len(ads.load()):,} ads", key="ads_again", type="tertiary", on_click=go,
                  args=("jobs",))
        ss.ad_keep = pick["text"]
    elif mode == "Browse ads":
        st.button(f"Browse {len(ads.load()):,} Australian ads from 2026 →", key="ads_go", on_click=go, args=("jobs",))
        ss.ad_keep = ""
    elif mode == "Try a sample":
        ad_card(SAMPLE_AD_TITLE, "", SAMPLE_AD)
        ss.ad_keep = SAMPLE_AD
    else:
        if "ad_box" not in ss:
            ss.ad_box = ss.get("ad_text_keep", "")
        st.text_area("The ad", key="ad_box", height=170, label_visibility="collapsed",
                     placeholder="Paste the full job ad here…")
        ss.ad_keep = ss.ad_text_keep = ss.ad_box or ""


def role_block() -> None:
    """The 11 roles, one pills row per family with the family's name on the left."""
    rows = st.container(key="role_rows")
    for n, (family, roles) in enumerate(FAMILIES.items()):
        ss.setdefault(f"role_f{n}", ss.role_keep if ss.role_keep in roles else None)
        name_col, pills_col = rows.columns([1, 3.6], vertical_alignment="center", gap="small")
        name_col.markdown(f"<span class='k-small k-mute k-fam'>{ui.esc(family)}</span>", unsafe_allow_html=True)
        pills_col.pills(family, roles, key=f"role_f{n}", label_visibility="collapsed", on_change=pick_role, args=(n,),
                        format_func=lambda r: ROLE_SHORT.get(r, r))
    role = ss.role_keep
    if backend.has_ad_counts(role):
        st.caption(f"The role is the 15 skills most often asked for in {backend.role_source(role)}")
    else:
        st.caption(f"{backend.role_source(role)} No percentages for this role.")


def taken_block() -> None:
    mine = backend.course_subjects(ss.course_keep or backend.HOME_COURSE)   # the student's course first
    options = mine + [c for c in SUBJECT_NAME if c not in set(mine)]
    ss.setdefault("taken_box", [c for c in ss.taken_keep if c in SUBJECT_NAME])
    st.markdown(ui.eyebrow(f"Subjects you've taken <span style='color:{ui.HAVE}'>· {len(ss.taken_box)}"
                           "</span>"), unsafe_allow_html=True)
    # No "Select N matches" row: it sat first, so Enter after typing a name ticked every match.
    st.multiselect("Subjects taken", options, key="taken_box", format_func=subject_label,
                   placeholder="Type a subject name (your course's subjects come first)",
                   label_visibility="collapsed", select_all=False, filter_mode="contains")
    ss.taken_keep = list(ss.taken_box)


def resume_block() -> str:
    """None, a file, pasted text, or the sample. Returns the resume text ("" when there is none)."""
    st.markdown(ui.eyebrow("Your resume <span class='k-dim'>· optional, kept for this session only</span>"),
                unsafe_allow_html=True)
    ss.setdefault("resume_mode", ss.get("resume_mode_keep", "Use a sample"))
    st.segmented_control("Where the resume comes from", RESUME_MODES, key="resume_mode", label_visibility="collapsed")
    mode = ss.resume_mode or ss.get("resume_mode_keep", "Use a sample")
    ss.resume_mode_keep = mode
    if mode == "No resume":
        st.caption("The gaps then count only what your subjects teach.")
        ss.resume_label = None
        return ""
    if mode == "Upload a file":
        upload = st.file_uploader("PDF or text file", type=["pdf", "txt", "md"], key="resume_upload",
                                  label_visibility="collapsed")
        if upload:
            ss.resume_keep = (upload.name, read_resume(upload))
        kept = ss.get("resume_keep")           # the uploader forgets its file off screen; the text is kept
        if kept:
            st.caption(f"Using {kept[0]}" + ("" if upload else " (uploaded earlier)"))
            ss.resume_label = kept[0]
            return kept[1]
        ss.resume_label = None
        return ""
    if mode == "Paste text":
        if "resume_box" not in ss:
            ss.resume_box = ss.get("resume_text_keep", "")
        st.text_area("Resume text", key="resume_box", height=200, label_visibility="collapsed",
                     placeholder="Paste your resume here: skills, experience, projects, education…")
        text = (ss.resume_box or "").strip()
        ss.resume_text_keep = text
        ss.resume_label = "Pasted resume" if text else None
        return text
    st.caption("A synthetic early-career MDSI student: SQL, Python, dashboards, no machine learning yet.")
    ss.resume_label = "Sample resume"
    return SAMPLE_RESUME


def page_inputs() -> None:
    """Left what you have (course, subjects, resume), right your goal (a role or a job ad): Quan's pick A, 17 Oct."""
    st.markdown(ui.h1("What you have and where you are heading", "md"), unsafe_allow_html=True)
    you_col, goal_col = st.columns([1.1, 1.45], gap="large")   # 1.1: the four resume choices fit on one line
    with you_col:
        st.markdown("<div class='k-big'>You</div>", unsafe_allow_html=True)
        st.markdown(ui.eyebrow("Your course <span class='k-dim'>· decides which subjects are open to you</span>"),
                    unsafe_allow_html=True)
        ss.setdefault("course_box", ss.course_keep or backend.HOME_COURSE)
        st.selectbox("Course", [c for c, _ in COURSES], key="course_box", format_func=COURSE_NAME.get,
                     label_visibility="collapsed")
        ss.course_keep = ss.course_box or backend.HOME_COURSE
        taken_block()
        ss.resume_text = resume_block()
    with goal_col, st.container(key="goal_col"):
        st.markdown("<div class='k-big'>Your goal</div>", unsafe_allow_html=True)
        ss.setdefault("goal_box", ss.goal_keep)
        st.segmented_control("Goal", GOALS, key="goal_box", label_visibility="collapsed", on_change=keep_goal)
        ss.goal_keep = ss.goal_box or ss.goal_keep
        if ss.goal_keep == "A job ad":
            job_ad_block()
        else:
            role_block()
        find_gaps_row()


def find_gaps_row() -> None:
    """The button, what is still missing, and the GPT-4o-mini switch."""
    if ss.goal_keep == "A job ad" and ui.word_count(ss.ad_keep) <= MIN_AD_WORDS:
        ready, hint = False, ("Pick an ad first." if (ss.ad_mode_keep == "Browse ads") else "Paste the full ad first.")
    elif not ss.resume_text and not ss.taken_keep:
        ready, hint = True, "No resume and no subject yet: every skill counts as a gap."
    else:
        ready, hint = True, ""
    run_col, hint_col = st.columns([1, 1.6], vertical_alignment="center")
    if run_col.button("Find my gaps", type="primary", key="show_gaps", disabled=not ready, width="stretch"):
        waiting = ("Loading the language model for the first time, up to a minute…" if WARM.locked()
                   else "One moment: reading your inputs and matching 360 UTS subjects…")
        with st.spinner(waiting):
            run_analysis()
        go("results", show_ad=False, results_tab_keep="Skills")
        st.rerun()
    hint_col.markdown(f"<span class='k-small k-mute'>{ui.esc(hint)}</span>", unsafe_allow_html=True)
    if backend.llm_enabled():
        ss.setdefault("gpt_box", ss.gpt_keep)
        st.toggle("GPT-4o-mini tier: also finds skills outside our dictionary", key="gpt_box")
        ss.gpt_keep = bool(ss.gpt_box)
    else:
        st.caption("GPT-4o-mini tier off: no OpenAI key on this machine, so only the dictionary tiers run.")


# ---------------------------------------------------------------- step 2b: browse ads

def posted(day: str) -> str:
    """'2026-09-15' -> '15 Sep 2026'."""
    try:
        d = date.fromisoformat(day)
    except ValueError:
        return day
    return f"{d.day} {d:%b %Y}"


def day(day_iso: str) -> str:
    """'2026-10-13' -> '13 Oct' this year, 'Mar 2025' before: the date column of the ads list."""
    try:
        d = date.fromisoformat(day_iso)
    except ValueError:
        return day_iso
    return f"{d.day} {d:%b}" if d.year == date.today().year else f"{d:%b %Y}"


def toggle_ad(ad_id: str) -> None:
    ss.ad_open = None if ss.ad_open == ad_id else ad_id


def read_full_ad(ad_id: str) -> None:
    ss.ad_full = ad_id


def close_full_ad() -> None:
    ss.ad_full = None


def use_ad(ad_id: str) -> None:
    """The ad becomes the goal on the Inputs page, shown there as a card."""
    ad = ads.by_id(ad_id)
    ss.update(ad_keep=ad["text"], ad_pick=ad, ad_mode_keep="Browse ads", goal_keep="A job ad", ad_open=None,
              ad_full=None, step="inputs", toast=f"Using “{ad['title']} — {ad['company']}”.")


FAMILY_ALL = "All"
ADS_SOURCE = ("<b>JobsPipe</b>: LinkedIn, Indeed and job boards, posted 1 Sep to 16 Oct 2026; a role's skill bars "
              "count these same ads. <b>Employers' own job boards</b>: 65 of them, Aug to Oct 2026.")
JOBS_PAGE = 30                                                  # ads listed at a time, then "Show 30 more"


def family_tab(family: str) -> str:
    """'Data & AI' -> 'Data & AI · 702': the family tabs carry their ad counts."""
    return f"{family} · {len(ads.search(family=None if family == FAMILY_ALL else family, limit=None)):,}"


def md_plain(text: str) -> str:
    """Text for a button label, which Streamlit reads as Markdown: punctuation that would format is escaped."""
    return re.sub(r"([\\`*_\[\]<>#|~:$])", r"\\\1", text)


@st.cache_data(show_spinner=False, max_entries=200)
def ad_tools(ad_id: str) -> list[str]:
    """The technical skills of the dictionary an ad names, most in-demand first (soft skills left out): found at
    fetch time for a JobsPipe ad, found here in the text for a job-board ad."""
    ad = ads.by_id(ad_id)
    res = baseline.resources()
    found = ad["skills"] if ad["skills"] is not None else baseline.find_skills(ad["text"])
    return [k for k in found if res.category.get(k) not in baseline.SOFT_CATEGORIES]


def show_more_ads() -> None:
    ss.jobs_shown += JOBS_PAGE


def page_jobs() -> None:
    """Family tabs with their counts, then one line per ad; an ad opens in place with "Use this ad" (Quan's pick C,
    17 Oct). The ads are the 2026 ones for all 11 roles (app/ads.py), newest first, 30 at a time."""
    st.button("← Back", key="jobs_back", type="tertiary", on_click=go, args=("inputs",),
              kwargs={"ad_open": None, "ad_full": None})
    st.markdown(ui.h1("Pick a job ad", "md"), unsafe_allow_html=True)
    ss.setdefault("job_family", FAMILY_ALL)
    st.segmented_control("Family", [FAMILY_ALL, *ads.FAMILIES], key="job_family", format_func=family_tab,
                         label_visibility="collapsed")
    family = None if ss.job_family in (FAMILY_ALL, None) else ss.job_family
    roles = [ads.ALL, *ads.roles_of(family)]
    if ss.get("job_role") not in roles:                  # a role of another family: back to all of this one
        ss.job_role = ads.ALL
    search_col, role_col, loc_col = st.columns([2.6, 1.3, 1], vertical_alignment="center")
    query = search_col.text_input("Search", key="job_q", placeholder="Search a title, company or skill",
                                  label_visibility="collapsed")
    role = role_col.selectbox("Role", roles, key="job_role", label_visibility="collapsed")
    loc = loc_col.selectbox("Location", ads.LOCATIONS, key="job_loc", label_visibility="collapsed")
    found = ads.search(query, role or ads.ALL, loc or "Anywhere", limit=None, family=family)
    if not found:
        st.markdown("<div class='k-serif k-mute' style='font-size:18px;padding:24px 0'>No ads match. "
                    "Try a broader role or location.</div>", unsafe_allow_html=True)
        return
    filters = (ss.job_family, role, loc, query)
    if ss.get("jobs_filters") != filters:                # new filters: back to the first 30
        ss.jobs_filters, ss.jobs_shown = filters, JOBS_PAGE
    rows = found[:ss.jobs_shown]
    n = len(found)
    # The sources show on hover over "from 2026" (no note under the list: Quan's pick C, 17 Oct).
    from_2026 = ui.tip("<span class='k-dotted'>from 2026</span>", ADS_SOURCE)
    st.markdown(f"<div class='k-small k-soft'>{n:,} ad{'' if n == 1 else 's'} {from_2026}, newest first"
                + (f" (showing {len(rows)})" if n > len(rows) else "") + " · click an ad to read it here</div>",
                unsafe_allow_html=True)
    with st.container(key="ad_list"):
        for a in rows:
            is_open = ss.ad_open == a["id"]
            date_col, title_col, where_col = st.columns([0.6, 4.4, 1.4], vertical_alignment="center", gap="small")
            date_col.markdown(f"<span class='k-mono k-small k-mute'>{day(a['posted'])}</span>", unsafe_allow_html=True)
            title_col.button(f"{md_plain(a['title'])} :gray[· {md_plain(a['company'])}]", key=f"ad_{a['id']}",
                             type="tertiary", on_click=toggle_ad, args=(a["id"],))
            where_col.markdown(f"<div class='k-small k-mute' style='text-align:right'>{ui.esc(a['location'])}"
                               f"<span class='k-chev{' open' if is_open else ''}'>›</span></div>",
                               unsafe_allow_html=True)
            if is_open:
                ad_panel(a)
    if n > len(rows):
        st.button(f"Show {min(JOBS_PAGE, n - len(rows))} more", key="jobs_more", type="tertiary",
                  on_click=show_more_ads)
    ad = ads.by_id(ss.get("ad_full")) if ss.get("ad_full") else None
    if ad:
        st.dialog(ad["title"], width="large", on_dismiss=close_full_ad)(ad_body)(ad)


def ad_panel(ad: dict) -> None:
    """The opened ad, under its line: the opening, the tools it names, then use it, read it all, or the original."""
    with st.container(key="ad_panel"):
        tools = ad_tools(ad["id"])[:8]
        chips = ("<div style='margin-top:8px'>" + "".join(ui.chip(t, colour=ui.SOFT) for t in tools) + "</div>"
                 if tools else "")
        if ad["text"]:
            opening = ui.esc(ad_excerpt(ad["text"], 420))
        else:                                            # a JobsPipe ad on a machine without the raw fetch
            opening = ("The text of this ad is not on this machine (JobsPipe's terms keep it out of the repository). "
                       "Open the original and paste it under &ldquo;Paste an ad&rdquo;.")
        st.markdown(f"<div class='k-soft' style='font-size:14px;line-height:1.55;max-width:80ch'>{opening}</div>"
                    + chips, unsafe_allow_html=True)
        use_col, full_col, link_col = st.columns([0.8, 0.9, 3.5], vertical_alignment="center", gap="small")
        if ad["text"]:
            use_col.button("Use this ad", key="use_job", type="primary", on_click=use_ad, args=(ad["id"],))
            full_col.button("Read the full ad", key="ad_full_btn", type="tertiary", on_click=read_full_ad,
                            args=(ad["id"],))
        if ad["url"]:
            link_col.markdown(f"<a href='{ui.esc(ad['url'])}' target='_blank' class='k-small'>Open the original ↗</a>",
                              unsafe_allow_html=True)


def ad_body(ad: dict) -> None:
    """The whole ad in a dialog; the button comes before the text, so a short screen shows it without scrolling."""
    st.markdown(f"<div class='k-mute' style='font-size:14px;margin:-4px 0 4px'>{ui.esc(ad['company'])} · "
                f"{ui.esc(ad['location'])} · {posted(ad['posted'])} · {ui.esc(ad['source'])}</div>",
                unsafe_allow_html=True)
    if st.button("Use this ad", key="use_job_full", type="primary"):
        use_ad(ad["id"])
        st.rerun()
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", ad["text"])           # scraped ads carry runs of blank lines
    st.markdown(f"<div class='k-preview'>{ui.esc(text)}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- step 3: results

def bars_aside(skills: list[dict], counted: bool, role: str | None, hatched: bool) -> str:
    """Where the bars come from, on the right of the skills heading; how to read them on hover (no footnote)."""
    click = "Click a skill for the evidence and where to learn it."
    if not counted:
        return ui.tip("core skills · no Australian ad counts yet", ui.tip_lines([ui.esc(backend.role_source(role)), click]),
                      "right")
    who = backend.DEFAULT_ROLE if role is None else role      # a pasted ad is weighed by the Data Scientist ads
    source = backend.role_source(who, skills[0].get("demand_source"), skills[0].get("demand_period"))
    lines = [f"<b>Each bar</b>: the share of these ads that name the skill. {ui.esc(source)}"]
    if backend.source_2019_22(role):
        from skillabus.match import trend_period
        lines.append(f"Hover a bar for its {trend_period(who)} share."
                     + (f" A hatched bar: a skill the {trend_period(who)} ads never named." if hatched else ""))
    lines.append(click)
    face = f"<span class='k-swatch'></span><span style='color:{ui.MUTE}'>share of {ui.esc(source.split(', full text')[0].rstrip('.'))}</span>"
    return ui.tip(face, ui.tip_lines(lines), "right")


def skills_section(skills: list[dict], counted: bool, noun: str, role: str | None = None) -> None:
    from skillabus.match import trend_period
    period = trend_period(role or backend.DEFAULT_ROLE)      # "2019-22" for Data Scientist, "2020-21" for the others
    hatched = counted and any(s.get("demand_pct_2019_22") is not None and s["demand_pct_2019_22"] < 1
                              <= (s.get("demand_pct") or 0) for s in skills)
    st.markdown(ui.h2(f"Skills the {noun} asks for", bars_aside(skills, counted, role, hatched)), unsafe_allow_html=True)
    for i, s in enumerate(skills):
        name_col, bar_col, status_col = st.columns([2.4, 4.4, 1.1], vertical_alignment="center")
        name_col.button(s["skill_label"] + (" ✦" if s["emerging"] else ""), key=f"open_{i}", type="tertiary",
                        on_click=open_gap, args=(s["skill_label"],))
        if counted:
            pct, old = s.get("demand_pct"), s.get("demand_pct_2019_22")
            new_since_2022 = old is not None and old < 1 <= (pct or 0)     # the pre-2022 ads never named it
            tip = ""
            if pct is not None:
                when = f" ({s['demand_period']})" if s.get("demand_period") else ""
                tip = f"{pct:.0f}% of {s.get('total_ads') or 'the'} ads{when}"
                if old is not None:
                    tip += f"; {old:.0f}% of the {period} Seek ads"
            bar_col.markdown(ui.bar(pct, s["status"], new_since_2022, tip), unsafe_allow_html=True)
        else:
            bar_col.markdown(f"<span class='k-small k-mute'>{CORE_SOURCE.get(s.get('core_source'), '')}</span>",
                             unsafe_allow_html=True)
        status_col.markdown(status_cell(s), unsafe_allow_html=True)
    if is_ad(ss.result) and ss.ad_keep.strip():
        st.button("Hide the ad" if ss.show_ad else "Show where these appear in the ad", key="toggle_ad",
                  type="tertiary", on_click=toggle, args=("show_ad",))
        if ss.show_ad:
            st.markdown(ui.highlight(ss.ad_keep, skills, regex_for), unsafe_allow_html=True)


def path_card(code: str, r: dict, by: dict, plan: dict) -> None:
    """One UTS subject of the path: name, the gaps it closes, when it runs, the what-if tick box."""
    session = (plan.get(code) or {}).get("session") or ", ".join(r.get("offered") or [])
    with st.container(border=True):
        if st.button(r["subject_name"], key=f"path_{code}", type="tertiary", width="stretch"):
            subject_dialog(code)
        chips = "".join(ui.chip(lc(c), by.get(c, {}).get("status", "missing")) for c in r["covers"])
        st.markdown(chips or ui.chip("a prerequisite, no gap itself"), unsafe_allow_html=True)
        note = enrol_note(r)
        when = " · ".join(x for x in (session, note) if x)
        if when:
            colour = ui.PARTIAL if r.get("needs") else ui.MUTE
            st.markdown(f"<div class='k-small' style='color:{colour}'>{ui.esc(when)}</div>", unsafe_allow_html=True)
        taken_tick(code, f"wi_path_{code}")


def outside_card(o: dict, by: dict) -> None:
    """One outside course (the second tier of the path): a full-width dashed card, title first."""
    url = o.get("source_url") or ""
    title = (f"<a href='{ui.esc(url)}' target='_blank' style='font-weight:500;font-size:16px;color:{ui.INK}'>"
             f"{ui.esc(o['subject_name'])}</a>" if url.startswith("http")
             else f"<span style='font-weight:500;font-size:16px'>{ui.esc(o['subject_name'])}</span>")
    meta = " · ".join(x for x in (o.get("provider", ""), o.get("cost", "")) if x)
    inner = (f"<div style='display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline'>{title}"
             f"<span class='k-small k-mute'>{ui.esc(meta)}</span></div>"
             f"<div style='margin-top:8px'>"
             + "".join(ui.chip(lc(c), by.get(c, {}).get("status", "missing")) for c in o["covers"])
             + "</div>")
    st.markdown(ui.card(inner, dashed=True), unsafe_allow_html=True)


def path_section(res: dict, by: dict, counted: bool) -> None:
    lp, recs = res["learning_path"], {r["subject_code"]: r for r in res["recommendations"]}
    plan = {p["subject_code"]: p for p in lp.get("plan", []) if isinstance(p, dict)}
    subjects = [code for code in lp["subjects"] if code in recs]
    aside = (ui.tip(f"<span style='color:{ui.HAVE}'>closes {lp['gaps_closed']} of {lp['gaps_total']} gaps</span>",
                    "Tick &ldquo;I've taken this&rdquo; on a subject: it joins your subjects on the Inputs page, and "
                    "the gaps and the path are recomputed.", "right") if lp["gaps_total"] else "")
    st.markdown(ui.h2("Your path", aside), unsafe_allow_html=True)
    open_gaps = [k for k in by if by[k]["status"] != "have"
                 and not any(k in recs[c]["covers"] for c in lp["subjects"] if c in recs)]
    no_subject = [k for k in open_gaps if not any(k in r["covers"] for r in res["recommendations"])]
    later = [k for k in open_gaps if k not in no_subject]
    items = []
    if counted and lp["subjects"]:
        items.append(ui.count_pill(f"{lp['demand_covered_pct']:.0f}%", "of the demand", ui.HAVE,
                                   "The path covers this share of the employer demand behind your gaps."))
    if later:
        items.append(ui.count_pill(len(later), "still open", ui.PARTIAL, ui.tip_lines(
            [f"Still open after this path: <b>{ui.esc(', '.join(lc(u) for u in later))}</b>.",
             "Other subjects teach them: click the skill on the Skills tab."])))
    if no_subject:
        items.append(ui.count_pill(len(no_subject), "no UTS subject", ui.MISSING, ui.tip_lines(
            [f"No subject's Handbook text names <b>{ui.esc(', '.join(lc(u) for u in no_subject))}</b>.",
             "See the Outside UTS tab."])))
    st.markdown(ui.pills(items), unsafe_allow_html=True)
    if not subjects:
        msg = ("You already have every skill on the list." if not lp["gaps_total"]
               else "No subject in the Handbook text covers these gaps; see the Outside UTS tab.")
        st.markdown(f"<div class='k-serif k-mute' style='font-size:18px;line-height:1.5'>{msg}</div>",
                    unsafe_allow_html=True)
    for i in range(0, len(subjects), 3):                    # three cards to a row, in path order
        for col, code in zip(st.columns(3, gap="medium"), subjects[i:i + 3]):
            with col:
                path_card(code, recs[code], by, plan)


def outside_section(res: dict, by: dict) -> None:
    """The second tier of the path: outside courses for the gaps no UTS subject the student can take covers."""
    block = res["learning_path"].get("outside") or {}
    names = {r["subject_code"]: r for r in res.get("outside_recommendations", [])}
    chosen = [c for c in block.get("courses", []) if c in names]
    left_open = block.get("gaps_open_before", 0)
    aside = (f"<span style='color:{ui.HAVE}'>closes {block.get('gaps_closed', 0)} of the {left_open} gaps the UTS path "
             "leaves open</span> · not for UTS credit" if chosen else "not for UTS credit")
    st.markdown(ui.h2("Outside UTS", aside), unsafe_allow_html=True)
    if not chosen:
        msg = ("The UTS path covers every gap: nothing to add from outside." if not left_open
               else "No course in our list covers the gaps the UTS path leaves open.")
        st.markdown(f"<div class='k-serif k-mute' style='font-size:18px;line-height:1.5'>{msg}</div>",
                    unsafe_allow_html=True)
        return
    for code in chosen:
        outside_card(names[code], by)
    others = [r for c, r in names.items() if c not in chosen]
    if others:
        st.markdown(ui.pills([ui.count_pill(f"+{len(others)}", "more courses teach these gaps", ui.MUTE, ui.tip_lines(
            [f"<b>{ui.esc(r['subject_name'])}</b> · {ui.esc(r.get('provider', ''))}" for r in others[:6]]))]),
                    unsafe_allow_html=True)


def certs_section(role: str) -> None:
    st.markdown(ui.h2("Certifications worth having", "foundational first, then associate, professional, expert"),
                unsafe_allow_html=True)
    certs = backend.certifications(role)
    if certs:
        shown = certs if ss.certs_more else certs[:CERTS_SHOWN]
        st.markdown("<div class='k-certs'>" + "".join(cert_card(c) for c in shown) + "</div>", unsafe_allow_html=True)
        if len(certs) > CERTS_SHOWN:
            st.button("Show fewer" if ss.certs_more else f"Show all {len(certs)}", key="certs_all", type="tertiary",
                      on_click=toggle, args=("certs_more",))
    else:
        st.markdown("<span class='k-mute'>No certification in our list for this role yet.</span>",
                    unsafe_allow_html=True)


def result_pills(res: dict) -> tuple[str, ...]:
    """The outlined counts after have / partial / missing: skills not on the resume, terms outside the list."""
    out = []
    off_cv = [s for s in res["skills"] if not_on_cv(s)]
    if off_cv:
        out.append(ui.count_pill(len(off_cv), "not on CV", ui.PARTIAL, ui.tip_lines(
            [f"<b>{ui.esc(lc(s['skill_label']))}</b> · from {ui.esc(from_subject(s).group(2))}" for s in off_cv]
            + ["You have these from your subjects, but employers read your resume, not your transcript: add them."])))
    also = res.get("also_in_ad") or []             # GPT-4o-mini found them; the vocabulary has no count for them
    if also:
        out.append(ui.count_pill(len(also), "outside our list", ui.MUTE, ui.tip_lines(
            [f"Also in the ad: {ui.esc(', '.join(also))}.",
             "Found by GPT-4o-mini; our skills list has no ad counts for them, so they are not counted."])))
    return tuple(out)


def page_results() -> None:
    res = ss.result
    skills = res["skills"]
    role = res.get("role")                                          # None for a job ad
    counted = role is None or backend.has_ad_counts(role)           # False: core skills, no percentages
    by = {s["skill_label"]: s for s in skills}
    n_have = sum(s["status"] == "have" for s in skills)
    n_part = sum(s["status"] == "partial" for s in skills)
    gaps = [s for s in skills if s["status"] != "have"]

    st.button("← Change inputs", key="back_inputs", type="tertiary", on_click=go, args=("inputs",))

    if not skills:
        if ss.engine.startswith("none"):
            st.error(f"The pipeline could not analyse this role: {ss.engine}")
        else:
            st.warning("I couldn't find any technical skills in that ad. Is it the full text?")
        return

    target = ad_title() if is_ad(res) else role
    st.markdown(ui.eyebrow(ui.esc(target)), unsafe_allow_html=True)
    colour = ui.HAVE if not gaps else (ui.MISSING if len(gaps) >= 4 else ui.PARTIAL)
    if not gaps:
        tail = "skills — you already have them all."
    else:
        top = [lc(g["skill_label"]) for g in gaps if not g["emerging"]][:3] or [lc(g["skill_label"]) for g in gaps[:3]]
        tail = f"skills still to learn. Biggest gaps: {', '.join(top)}."
    st.markdown(ui.h1(f"<span style='color:{colour};font-weight:500'>{len(gaps)} of {len(skills)}</span> "
                      f"{ui.esc(tail)}", "lg"), unsafe_allow_html=True)
    st.markdown(ui.counts(n_have, n_part, len(gaps) - n_part, result_pills(res)), unsafe_allow_html=True)

    # One section at a time, full width (Quan's pick): the tabs below the verdict.
    tabs = ["Skills", "Your path", "Outside UTS"] + (["Certifications"] if role else [])
    if ss.get("results_tab") not in tabs:
        ss.results_tab = ss.get("results_tab_keep") if ss.get("results_tab_keep") in tabs else "Skills"
    st.segmented_control("Section", tabs, key="results_tab", label_visibility="collapsed")
    tab = ss.results_tab or "Skills"
    ss.results_tab_keep = tab
    if tab == "Skills":
        skills_section(skills, counted, "ad" if is_ad(res) else "role", res.get("weigh_role") or role)
    elif tab == "Your path":
        path_section(res, by, counted)
    elif tab == "Outside UTS":
        outside_section(res, by)
    else:
        certs_section(role)


# ---------------------------------------------------------------- step 3b: the evidence for one skill

TAKEN_EVIDENCE = re.compile(r"From (\d{5,6}) (.+?) \(taken\)$")    # credit_taken(): "From 94692 Data Science Practice (taken)"


def from_subject(s: dict) -> re.Match | None:
    """A skill the student has only because a subject they took teaches it, not because the resume says so."""
    return TAKEN_EVIDENCE.match(s.get("resume_evidence") or "") if s["status"] == "have" else None


def not_on_cv(s: dict) -> bool:
    """Had from a subject, but the resume the student gave does not show it: an employer would not see it."""
    return bool(from_subject(s)) and bool(ss.resume_text)


def status_cell(s: dict, long: bool = False) -> str:
    """A skill's status; amber "not on CV" for one the student has from a subject but not on the resume (Quan, 17 Oct:
    the note under the list was easy to miss)."""
    if not_on_cv(s):
        face = ui.status_html("partial", "you have it · not on your CV" if long else "have · not on CV")
        return ui.tip(face, f"<b>From {ui.esc(from_subject(s).group(2))}</b>, a subject you have taken. Your resume "
                            "does not mention it: add it.", "" if long else "right")
    return ui.status_html(s["status"], ui.STATUS_TEXT[s["status"]] if long else None)


def resume_note(s: dict) -> str:
    label = s["skill_label"]
    if s["status"] == "have":
        taken = from_subject(s)
        if taken:
            tail = " Your resume does not mention it: add it." if ss.resume_text else ""
            return f"Covered by {taken.group(2)}, a subject you have taken.{tail}"
        ev = s.get("resume_evidence") or ""
        # The skill page shows this after "You have it." with no label above it, so it says where it comes from.
        return f"Your resume says: “{ev}”." if ev else f"Your resume mentions {lc(label)}."
    if s["status"] == "partial":
        return f"Your resume says: \u201c{s.get('resume_evidence', '')}\u201d. Related, not quite the same skill."
    if not ss.resume_text:
        return f"No subject you ticked names {lc(label)}."
    return f"Nothing in your resume or the subjects you ticked mentions {lc(label)}."


def short(text: str, n: int = 160) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "\u2026"


BAR_PX = 80                      # a 100% bar on the skill page; every bar on the same 0-100% scale


def demand_chart(s: dict, counted: bool, role: str | None) -> str:
    """Left of the skill page's band: the share of ads that ask for the skill before 2022 next to now."""
    if not counted:
        return (f"<div class='k-small k-dim'>Core skill</div>"
                f"<div class='k-soft' style='margin-top:4px'>{ui.esc(CORE_SOURCE.get(s.get('core_source'), 'core skill of the role'))}</div>"
                "<div class='k-small k-mute' style='margin-top:4px'>no Australian ad counts for this role yet</div>")
    pct, old = s.get("demand_pct"), s.get("demand_pct_2019_22")
    who = role or backend.DEFAULT_ROLE
    if pct is None:
        return f"<div class='k-small k-dim'>Employers ask</div><div class='k-soft'>No count in the {ui.esc(who)} ads</div>"
    from skillabus.match import SOURCE_NAMES, block_2019_22, trend_period   # "jobspipe_2026" -> ("JobsPipe", "Sep-Oct 2026")
    when = SOURCE_NAMES.get(s.get("demand_source"), ("", s.get("demand_period") or "now"))[1]
    bars = []
    if old is not None:
        then_ads = (block_2019_22(who) or {}).get("total_ads")
        bars.append((old, trend_period(who) or "before 2022", f"{then_ads:,} ads" if then_ads else "", "rgba(143,188,255,.4)"))
    bars.append((pct, when, f"{s['total_ads']:,} ads" if s.get("total_ads") else "", ui.LINK))
    cols = "".join(f"<div class='k-tbar' style='--c:{c}'><span>{v:.0f}%</span>"
                   f"<b style='height:{max(2, v / 100 * BAR_PX):.0f}px'></b></div>" for v, _, _, c in bars)
    labels = "".join(f"<div>{ui.esc(w)}<br><span class='k-dim'>{n}</span></div>" for _, w, n, _ in bars)
    return (f"<div class='k-small k-dim'>Employers ask · share of {ui.esc(who)} ads</div>"
            f"<div class='k-bars' style='--n:{len(bars)}'>{cols}</div>"
            f"<div class='k-bars-x' style='--n:{len(bars)}'>{labels}</div>")


STATUS_LINE = {"have": ("✓", "You have it."), "partial": ("~", "Partly."), "missing": ("✕", "Missing.")}


def fact_lines(s: dict) -> str:
    """Right of the band: what the ad says (for an ad), the student's status, and "new skill" in plain words."""
    lines = []
    if is_ad(ss.result):
        lines.append(("ad", "“", f"The ad says <q>“{ui.esc(short(s['ad_evidence'], 170))}”</q>"))
    icon, word = STATUS_LINE[s["status"]]
    lines.append((s["status"], icon, f"<b>{word}</b> {ui.esc(resume_note(s))}"))
    if s["emerging"]:                          # no concept in ESCO, the EU's skills list the matcher uses
        old = s.get("demand_pct_2019_22")
        before = "Employers barely asked for it before 2022. " if old is not None and old < 1 else ""
        lines.append(("new", "✦", f"<b>New skill.</b> {before}Too new for the EU's official skills list, "
                                  "so Skillabus tracks it itself."))
    return "".join(f"<div class='k-line {kind}'><span class='k-ic'>{icon}</span><span>{html}</span></div>"
                   for kind, icon, html in lines)


VOTE_HELP = "Does this subject really teach the skill? Your vote helps us check the matcher."


def uts_cards(label: str, res: dict) -> None:
    """Learn at UTS: up to three subjects whose Handbook text names the skill, as a row of cards."""
    hits = [(r, e) for r in res["recommendations"] for e in r["evidence"] if e["skill_label"] == label][:3]
    tail = "" if hits else " <span class='k-dim'>· no subject you can take names it in its Handbook text</span>"
    st.markdown(ui.eyebrow("Learn at UTS" + tail), unsafe_allow_html=True)
    votes = backend.vote_counts()
    if hits:
        for col, (i, (r, e)) in zip(st.columns(3, gap="medium"), enumerate(hits)):
            with col, st.container(border=True):
                if st.button(r["subject_name"], key=f"ev_{i}", type="tertiary", width="stretch"):
                    subject_dialog(r["subject_code"])
                st.markdown(ui.layer_pill(e["layer"])
                            + f"<div class='k-serif k-soft' style='font-size:14.5px;line-height:1.45;margin:8px 0 6px'>"
                            f"\u201c{ui.esc(short(e['text']))}\u201d</div>", unsafe_allow_html=True)
                note = enrol_note(r)
                if note:
                    colour = ui.PARTIAL if r.get("needs") else ui.MUTE
                    st.markdown(f"<div class='k-small' style='color:{colour}'>{ui.esc(note)}</div>",
                                unsafe_allow_html=True)
                up, down = votes.get((r["subject_code"], label), [0, 0])
                v1, v2 = st.columns(2, gap="small")
                v1.button(f"👍 {up}", key=f"up_{i}", width="stretch", on_click=vote, help=VOTE_HELP,
                          args=(r["subject_code"], label, "up"))
                v2.button(f"👎 {down}", key=f"down_{i}", width="stretch", on_click=vote, help=VOTE_HELP,
                          args=(r["subject_code"], label, "down"))
                taken_tick(r["subject_code"], f"wi_ev_{i}")
    dropped = [d for d in res["learning_path"].get("dropped", []) if label in d["covers"]][:5]
    if dropped:
        lines = []
        for d in dropped:
            reason = re.sub(r"\b\d{5,6} (?=[A-Z])", "", d["reason"])          # names, not codes
            reason = reason if len(reason) <= 120 else reason[:117].rstrip() + "\u2026"
            lines.append(f"<b>{ui.esc(SUBJECT_LABEL.get(d['subject_code'], d['subject_name']))}</b> also teaches it, "
                         f"but {ui.esc(reason)}.")
        st.markdown(ui.pills([ui.count_pill(f"+{len(dropped)}", "more teach it, not open to you", ui.MUTE,
                                            ui.tip_lines(lines))]), unsafe_allow_html=True)


@st.fragment
def self_study_cards(label: str, role: str | None) -> None:
    """Self-study: the level filter, then up to three resources as cards. A fragment: a filter redraws this only.

    No cost filter (Quan, 17 Oct): free and free-to-audit resources, and paid ones only for a skill no free one
    teaches (Econometrics); each card shows its cost."""
    ss.setdefault("level_filter", list(ss.level_keep))
    head, f1 = st.columns([1.1, 3.1], vertical_alignment="center", gap="medium")
    head.markdown(ui.eyebrow("Self-study <span class='k-dim'>· not for credit</span>"), unsafe_allow_html=True)
    f1.pills("Level", list(backend.LEVELS), key="level_filter", selection_mode="multi", label_visibility="collapsed")
    levels = list(ss.level_filter or [])
    ss.level_keep = levels
    found = (backend.self_study(label, levels, backend.COST_CHOICES["Include free-to-audit"], role)
             or backend.self_study(label, levels, backend.COST_CHOICES["Include paid"], role))
    if not found and backend.self_study(label, backend.LEVELS, backend.COST_CHOICES["Include paid"], role):
        st.markdown("<span class='k-mute'>Nothing at these levels: pick another level above.</span>",
                    unsafe_allow_html=True)
    elif not found:
        st.markdown("<span class='k-mute'>No self-study resource in our list for this skill yet.</span>",
                    unsafe_allow_html=True)
    else:
        for col, r in zip(st.columns(3, gap="medium"), found[:3]):
            col.markdown(resource_html(r), unsafe_allow_html=True)


def page_evidence() -> None:
    res = ss.result
    by = {s["skill_label"]: s for s in res["skills"]}
    s = by.get(ss.gap) or next(iter(by.values()))
    role = res.get("role")
    counted = role is None or backend.has_ad_counts(role)
    st.button("← All skills", key="back_results", type="tertiary", on_click=go, args=("results",))
    new = ui.chip("✦ New skill", colour=ui.EMERGING) if s["emerging"] else ""
    st.markdown("<div style='display:flex;align-items:baseline;gap:16px;flex-wrap:wrap'>"
                + ui.h1(ui.esc(s["skill_label"]), "lg") + status_cell(s, long=True)
                + new + "</div>", unsafe_allow_html=True)
    # One band, not three grey cards (Quan's pick, 17 Oct): the trend as bars, the rest as coloured lines.
    st.markdown(f"<div class='k-band'><div>{demand_chart(s, counted, res.get('weigh_role') or role)}</div>"
                f"<div class='k-lines'>{fact_lines(s)}</div></div>", unsafe_allow_html=True)

    if s["status"] == "have":
        st.markdown("<div class='k-serif k-soft' style='font-size:18px;line-height:1.5;margin-top:8px'>You already have "
                    "this skill, so it is not part of your path. Pick a missing or partial skill to see where to learn it."
                    "</div>", unsafe_allow_html=True)
        return
    uts_cards(s["skill_label"], res)
    self_study_cards(s["skill_label"], role)


# ---------------------------------------------------------------- the subject dialog

def subject_dialog(code: str) -> None:
    """Open the subject dialog, titled with the subject's name: a dialog's title is fixed when it is declared,
    so the dialog is declared here, per subject."""
    st.dialog(subject_name(code), width="large")(subject_body)(code)


def subject_body(code: str) -> None:
    res = ss.result
    recs = {r["subject_code"]: r for r in res["recommendations"]}
    recs |= {r["subject_code"]: r for r in res.get("outside_recommendations", [])}
    r = recs.get(code)
    dropped = next((d for d in res["learning_path"].get("dropped", []) if d["subject_code"] == code), None)
    info = r or dropped or {}
    plan = {p["subject_code"]: p for p in res["learning_path"].get("plan", []) if isinstance(p, dict)}
    when = (plan.get(code) or {}).get("session") or ", ".join(info.get("offered") or []) or "not in the 2026 sessions we have"
    before = names(info.get("needs") or []) or ("not confirmed" if info.get("unverified") else "no prerequisite")
    if dropped:
        access, colour = dropped["reason"], ui.PARTIAL
    elif r and r.get("needs"):
        access, colour = f"Needs {names(r['needs'])} first", ui.PARTIAL
    elif r and r.get("provider"):
        access, colour = f"Outside UTS ({r['provider']}, {r['cost']}) · not for credit", ui.MUTE
    else:
        access, colour = "Open to you", ui.HAVE
    st.markdown(
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:14px 24px;font-size:15px;margin:12px 0 18px'>"
        f"<div><div class='k-small k-dim'>When</div><div>{ui.esc(when)}</div></div>"
        f"<div><div class='k-small k-dim'>Before it</div><div>{ui.esc(before)}</div></div>"
        f"<div style='grid-column:1/-1'><div class='k-small k-dim'>For you</div><div style='color:{colour}'>{ui.esc(access)}</div></div>"
        "</div>", unsafe_allow_html=True)
    by = {s["skill_label"]: s for s in res["skills"]}
    chips = "".join(ui.chip(lc(c), by.get(c, {}).get("status", "missing")) for c in info.get("covers", []))
    st.markdown(ui.eyebrow("Closes these gaps") + (chips or "<span class='k-mute'>none of your gaps: a prerequisite</span>"),
                unsafe_allow_html=True)
    if info.get("evidence"):
        st.markdown(ui.eyebrow("From the Handbook"), unsafe_allow_html=True)
        for e in info["evidence"][:4]:
            name, lcolour, _ = ui.LAYER.get(e["layer"], (e["layer"], ui.MUTE, ""))
            st.markdown(f"<div class='k-small' style='color:{lcolour}'>{ui.esc(name)} · {ui.esc(e['skill_label'])}</div>"
                        + ui.quote(e["text"], lcolour), unsafe_allow_html=True)
    if info.get("source_url"):
        st.markdown(f"<a href='{ui.esc(info['source_url'])}' target='_blank'>Open in UTS Handbook ↗</a> "
                    f"<span class='k-mono k-small k-dim'>{ui.esc(code)}</span>", unsafe_allow_html=True)
    if not (r and r.get("provider")):
        taken_tick(code, f"wi_dlg_{code}")


# ---------------------------------------------------------------- routing

if ss.toast:
    st.toast(ss.toast)
    ss.toast = None
if ss.step in ("results", "evidence") and not ss.result:
    ss.step = "inputs"
PAGES = {"inputs": page_inputs, "jobs": page_jobs, "results": page_results,
         "evidence": page_evidence, "chat": page_chat}
top_bar()
PAGES[ss.step]()
view = (ss.step, ss.gap if ss.step == "evidence" else None)
if ss.get("view_shown") != view:          # a new page starts at the top; a tab, tick or filter keeps the place
    ss.view_shown = view
    ss.view_n = ss.get("view_n", 0) + 1
    st.html(ui.scroll_top(ss.view_n), unsafe_allow_javascript=True)
