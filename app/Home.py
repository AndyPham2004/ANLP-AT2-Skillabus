"""Skillabus: which skills a role asks for that you lack, and where to learn each one.

Run from the repo root:  streamlit run app/Home.py

The layout and flow follow the v2 design in docs/design/ (Claude Design, 16 Oct 2026): a sidebar
with the three steps and the Handbook chat; then Start -> Inputs (or Browse ads) -> Results ->
Evidence for one skill, plus a subject dialog. app/ui.py holds the CSS and the HTML helpers,
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
USER_TYPES = {   # key -> card label, the question it answers, the call to action (the design's start page)
    "elective": ("UTS student", "Which elective moves me closest to the job I want?", "Pick a role →"),
    "job": ("Job seeker", "What does my resume lack for this ad?", "Add ad and resume →"),
    "switch": ("Career switcher", "How far am I from a new field?", "Pick role, add resume →"),
}
CARD_ACCENT = {"elective": ui.HAVE, "job": ui.LINK, "switch": ui.PARTIAL}   # one colour per card and its CTA
INPUT_TITLES = {"job": "The ad and your resume", "elective": "The role and your subjects",
                "switch": "The role and your resume"}
STAGES = ("About to enrol", "Studying at UTS", "Already working")
NOT_ENROLLED = ""                                              # the course picker's "not enrolled" value
COURSES = backend.courses()                                    # (code, name) for all 44 courses, MDSI first
COURSE_NAME = dict(COURSES)
AD_MODES = ("Browse ads", "Paste an ad", "Try a sample")
RESUME_MODES = ("Upload a file", "Paste text", "Use a sample")
MIN_AD_WORDS = 20
FAMILIES = backend.role_families()
ROLE_LIST = [role for roles in FAMILIES.values() for role in roles]        # all 11 roles, family by family
CORE_SOURCE = {"onet": "O*NET in-demand tool", "esco": "ESCO essential skill"}
CHAT_SUGGESTIONS = ("Which subject teaches LLMs?", "What does Applied NLP cover?", "Where can I learn SQL?")
STEP_OF = {"start": 1, "inputs": 2, "jobs": 2, "results": 3, "evidence": 3}     # the chat page shows the step it came from
CHAT_BACK = {"start": "← Back", "inputs": "← Back to your inputs", "jobs": "← Back to the ads",
             "results": "← Back to results", "evidence": "← Back to the skill"}
CERTS_SHOWN = 6                                                # then "Show all 11"
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

def lc(label: str) -> str:
    """Lower-case a generic skill name for running text: "Machine learning" -> "machine learning",
    "Generative AI" -> "generative AI". Product and proper names keep their case ("Azure", "Microsoft Office",
    "SQL Server"): one-word names are left alone, and so are names whose second word starts with a capital
    followed by small letters."""
    words = label.split()
    if len(words) < 2 or not label[1:2].islower():
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


def cert_card(c: dict) -> str:
    """One certification as a card: name linked, vendor, level, exam code, exam price, and "hot" with its ad count.
    The long reason behind "hot" is in one note under the cards."""
    price = (f"<div class='k-mono'>A${ui.esc(c['cost_aud'])}</div>" if c["cost_aud"] and c["cost_aud"] != "varies"
             else "<div class='k-small k-mute'>Exam price varies by country</div>")
    exam = f" · exam {c['exam_code']}" if c["exam_code"] else ""
    hot = ""
    if c.get("hot", "").strip().lower() == "yes":
        n = re.search(r"\((\d[\d,]*) AU ads", c.get("hot_reason") or "")
        hot = ui.chip(f"hot · {n.group(1)} AU ads" if n else "hot · salary guide", colour=ui.PARTIAL)
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
    "step": "start", "user_type": None, "messages": [], "chat_from": "start", "ad_open": None, "certs_more": False,
    "show_ad": False,
    "show_details": False, "ad_keep": "", "ad_mode_keep": "Try a sample", "ad_pick": None, "taken_keep": [],
    "whatif": [], "result": None, "engine": "", "ran": False, "gap": None, "resume_text": "", "resume_label": None,
    "role_keep": backend.DEFAULT_ROLE, "stage_keep": "Studying at UTS", "course_keep": backend.HOME_COURSE,
    "gpt_keep": backend.llm_enabled(),
    "level_keep": list(backend.LEVELS), "cost_keep": "Include free-to-audit", "toast": None,
}
for k, v in DEFAULTS.items():
    ss.setdefault(k, v)


def go(step: str, **kw) -> None:
    ss.step = step
    for k, v in kw.items():
        ss[k] = v


def toggle(key: str) -> None:
    ss[key] = not ss[key]


def pick_type(key: str) -> None:
    if key != ss.user_type:        # a new kind of question: the old result no longer answers it
        ss.update(result=None, ran=False, whatif=[], gap=None)
    ss.user_type = key
    ss.step = "inputs"


def start_over() -> None:
    ss.update(step="start", user_type=None, result=None, ran=False, whatif=[], gap=None,
              show_ad=False, show_details=False)


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
    """Run the pipeline on what the Inputs page kept; subjects ticked as taken (what-if) count as taken."""
    taken = tuple(sorted(set(ss.taken_keep) | set(ss.whatif)))
    ad = ss.ad_keep if ss.user_type == "job" else None
    result, engine = cached_analyse(ss.resume_text, ad, taken, ss.role_keep, ss.course_keep or None,
                                    bool(ss.gpt_keep))
    ss.update(result=result, engine=engine, ran=True)


def set_whatif(code: str, on: bool) -> None:
    """'Already taken' on a subject: count it as taken and redo the gaps and the path (what-if, issue #60).

    A UTS student keeps one list, the subjects taken on the Inputs page, so the tick edits that list;
    the other two kinds of user have no such list and get a separate what-if set with a reset.
    """
    if ss.user_type == "elective":
        taken = set(ss.taken_keep)
        (taken.add if on else taken.discard)(code)
        ss.taken_keep = sorted(taken)
        ss.taken_box = list(ss.taken_keep)          # the Inputs page picker shows the same list
    else:
        codes = set(ss.whatif)
        (codes.add if on else codes.discard)(code)
        ss.whatif = sorted(codes)
    run_analysis()


def whatif_from_box(code: str, key: str) -> None:
    set_whatif(code, bool(ss[key]))


def reset_whatif() -> None:
    ss.whatif = []
    run_analysis()


def whatif_box(code: str, key: str, label: str = "Already taken") -> None:
    """The tick box for one subject; every copy of it shows the same state."""
    taken = ss.taken_keep if ss.user_type == "elective" else ss.whatif
    ss[key] = code in taken
    st.checkbox("I've taken this" if ss.user_type == "elective" else label, key=key,
                on_change=whatif_from_box, args=(code, key))


def open_gap(label: str) -> None:
    go("evidence", gap=label)


def vote(code: str, skill: str, value: str) -> None:
    save_vote(code, skill, value, code in ss.whatif)
    ss.toast = "Thanks, your vote is saved."


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
    if mode == "Browse ads":
        ss.step = "jobs"
    elif mode == "Try a sample":
        ss.ad_box, ss.ad_pick = SAMPLE_AD, None
    elif mode == "Paste an ad":
        ss.ad_box, ss.ad_pick = "", None


def stage_changed() -> None:
    """Already working: not enrolled, unless a course was picked; a student without a course gets MDSI."""
    if ss.stage_box == "Already working":
        ss.course_box = NOT_ENROLLED
    elif not ss.course_box:
        ss.course_box = backend.HOME_COURSE


def keep_role() -> None:
    if ss.role_box is None:               # pills can be deselected; a role is always needed
        ss.role_box = ss.role_keep
    ss.role_keep = ss.role_box


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


# ---------------------------------------------------------------- sidebar: steps and the chat button

def step_note(n: int) -> str:
    """The small line under a step of the sidebar: what was chosen there."""
    ut = ss.user_type
    if n == 1:
        return USER_TYPES[ut][0] if ut else ""
    if n == 2:
        if not ut:
            return ""
        parts = [(ad_title() if ss.ad_keep.strip() else "an ad") if ut == "job" else ss.role_keep]
        if ut != "elective" and ss.resume_label:
            parts.append(ss.resume_label.lower() if ss.resume_label.endswith(" resume") else ss.resume_label)
        return " · ".join(parts)
    if ss.ran and ss.result and ss.result.get("skills"):
        gaps = sum(x["status"] != "have" for x in ss.result["skills"])
        return f"{gaps} of {len(ss.result['skills'])} skills to learn"
    return ""


def top_bar() -> None:
    """One strip above every page: the name, the three steps, what was chosen so far, the chat button."""
    current = STEP_OF[ss.chat_from if ss.step == "chat" else ss.step]
    parts = []
    for n, label in enumerate(("Who you are", "Your inputs", "Results"), start=1):
        done, active = current > n, current == n
        colour = ui.HAVE if done else (ui.INK if active else ui.DIM)
        dot = (f"<span class='k-hdot' style='border-color:{colour};background:{ui.HAVE if done else 'transparent'};"
               f"color:{ui.DARK if done else colour}'>{'✓' if done else n}</span>")
        parts.append(f"<span class='k-hstep' style='color:{colour};font-weight:{500 if active else 400}'>{dot}{label}</span>")
    stepper = "<span class='k-hline'></span>".join(parts)
    ctx = " · ".join(x for x in (step_note(1), step_note(2)) if x)
    if ss.whatif:
        ctx = " · ".join(x for x in (ctx, "Counting as taken: " + ", ".join(subject_name(c) for c in ss.whatif)) if x)
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


# ---------------------------------------------------------------- step 1: who you are

def page_start() -> None:
    st.markdown(ui.h1(f"Find the skills a job wants that <span style='color:{ui.MISSING}'>you don't have yet</span>"
                      f" — and the <span style='color:{ui.HAVE}'>UTS subject</span> that teaches each one.", "xl"),
                unsafe_allow_html=True)
    st.markdown("<div class='k-eyebrow' style='margin-top:36px'>I am a…</div>", unsafe_allow_html=True)
    for col, (key, (label, question, cta)) in zip(st.columns(3, gap="medium"), USER_TYPES.items()):
        with col, st.container(border=True):
            st.markdown(f"<div class='k-accent' style='background:{CARD_ACCENT[key]}'></div>"
                        f"<div class='k-card-title'>{label}</div>"
                        f"<div class='k-soft k-body' style='min-height:3em;margin:6px 0 10px'>{question}</div>",
                        unsafe_allow_html=True)
            st.button(cta, key=f"role_{key}", width="stretch", on_click=pick_type, args=(key,))


# ---------------------------------------------------------------- step 2: your inputs

def job_ad_block() -> None:
    st.markdown(ui.eyebrow("The job ad"), unsafe_allow_html=True)
    # Widgets forget their value once off screen, so each keeps a *_keep twin that survives the other pages.
    ss.setdefault("ad_mode", ss.ad_mode_keep)
    if "ad_box" not in ss:
        ss.ad_box = ss.ad_keep or (SAMPLE_AD if ss.ad_mode == "Try a sample" else "")
    st.segmented_control("Where the ad comes from", AD_MODES, key="ad_mode", label_visibility="collapsed",
                         on_change=ad_mode_changed)
    st.caption(f"Browse: {len(ads.load())} Australian ads 2024-26 · Paste: copy the full text · "
               "Sample: Data Scientist, Sydney")
    if ss.ad_mode == "Browse ads" and ss.ad_pick:
        st.markdown(f"<div class='k-small k-mute'>Using <span style='color:{ui.INK}'>{ui.esc(ad_title())}"
                    "</span></div>", unsafe_allow_html=True)
    st.text_area("The ad", key="ad_box", height=190, label_visibility="collapsed",
                 placeholder="Paste the full job ad here…")
    ss.ad_keep = ss.ad_box or ""


def role_block() -> None:
    st.markdown(ui.eyebrow("The role you want"), unsafe_allow_html=True)
    ss.setdefault("role_box", ss.role_keep)
    st.pills("Role", ROLE_LIST, key="role_box", label_visibility="collapsed", on_change=keep_role)
    role = ss.role_box or ss.role_keep
    ss.role_keep = role
    if backend.has_ad_counts(role):
        st.caption(f"The role is the 15 skills most often asked for in {backend.role_source(role)}")
    else:
        st.caption(f"{backend.role_source(role)} No percentages for this role.")


def taken_block() -> None:
    mine = backend.course_subjects(ss.course_keep or backend.HOME_COURSE)   # the student's course first
    options = mine + [c for c in SUBJECT_NAME if c not in set(mine)]
    ss.setdefault("taken_box", [c for c in ss.taken_keep if c in SUBJECT_NAME])
    st.markdown(ui.eyebrow(f"Subjects you've already taken <span style='color:{ui.HAVE}'>· {len(ss.taken_box)}"
                           "</span>"), unsafe_allow_html=True)
    # No "Select N matches" row: it sat first, so Enter after typing a name ticked every match.
    st.multiselect("Subjects taken", options, key="taken_box", format_func=subject_label,
                   placeholder="Type a subject name (your course's subjects come first)",
                   label_visibility="collapsed", select_all=False, filter_mode="contains")
    ss.taken_keep = list(ss.taken_box)


def resume_block() -> str:
    """Upload a file, paste the text, or use the sample. Returns the resume text ("" when there is none yet)."""
    st.markdown(ui.eyebrow("Your resume <span class='k-dim'>· stays in memory for this session, never stored</span>"),
                unsafe_allow_html=True)
    ss.setdefault("resume_mode", ss.get("resume_mode_keep", "Use a sample"))
    st.segmented_control("Where the resume comes from", RESUME_MODES, key="resume_mode", label_visibility="collapsed")
    mode = ss.resume_mode or ss.get("resume_mode_keep", "Use a sample")
    ss.resume_mode_keep = mode
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
    ut = ss.user_type
    st.markdown(ui.h1(INPUT_TITLES[ut], "md"), unsafe_allow_html=True)

    stages = list(STAGES[:2]) if ut == "elective" else list(STAGES)     # a UTS student is not "already working"
    if ss.get("stage_box") not in stages:
        ss.stage_box = ss.stage_keep if ss.stage_keep in stages else "Studying at UTS"
    ss.setdefault("course_box", ss.course_keep)
    if ut == "elective" and not ss.course_box:
        ss.course_box = backend.HOME_COURSE
    stage_col, course_col = st.columns([1.1, 1], gap="large", vertical_alignment="bottom")
    with stage_col:
        st.markdown(ui.eyebrow("Where are you in your studies?"), unsafe_allow_html=True)
        st.segmented_control("Stage", stages, key="stage_box", label_visibility="collapsed",
                             on_change=stage_changed)
    ss.stage_keep = ss.stage_box or ss.stage_keep
    with course_col:
        st.markdown(ui.eyebrow("Your course <span class='k-dim'>· decides which subjects are open to you</span>"),
                    unsafe_allow_html=True)
        st.selectbox("Course", [NOT_ENROLLED] + [c for c, _ in COURSES], key="course_box",
                     format_func=lambda c: "Not enrolled at UTS" if c == NOT_ENROLLED else COURSE_NAME[c],
                     label_visibility="collapsed")
    ss.course_keep = ss.course_box or NOT_ENROLLED

    resume = ""
    if ut == "job":                     # ad and resume side by side: both in view on a short screen
        ad_col, cv_col = st.columns([1.35, 1], gap="large")
        with ad_col:
            job_ad_block()
        with cv_col:
            resume = resume_block()
    else:
        role_block()
        if ut == "elective":
            taken_block()
        else:
            resume = resume_block()
    ss.resume_text = resume

    if ut == "job":
        enough_ad = ui.word_count(ss.ad_keep) > MIN_AD_WORDS
        ready = enough_ad and bool(resume)
        hint = "" if ready else ("Add a job ad first: the full text." if not enough_ad else "Add a resume first.")
    elif ut == "switch":
        ready = bool(resume)
        hint = "" if ready else "Add a resume first."
    else:
        ready = True
        hint = "" if ss.taken_keep else "No subject ticked yet: every skill of the role counts as a gap."

    run_col, hint_col = st.columns([1, 3], vertical_alignment="center")
    if run_col.button("Find my gaps", type="primary", key="show_gaps", disabled=not ready, width="stretch"):
        waiting = ("Loading the language model for the first time, up to a minute…" if WARM.locked()
                   else "One moment: reading your inputs and matching 360 UTS subjects…")
        with st.spinner(waiting):
            run_analysis()
        go("results", show_ad=False, results_tab_keep="Skills")
        st.rerun()
    hint_col.markdown(f"<span class='k-mute'>{ui.esc(hint)}</span>", unsafe_allow_html=True)
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


def open_ad(ad_id: str) -> None:
    ss.ad_open = ad_id


def close_ad() -> None:
    ss.ad_open = None


def page_jobs() -> None:
    """One full-width list of ads; an ad opens in a dialog with "Use this ad" (Quan's pick, 17 Oct: the list and
    the ad side by side cut the company names)."""
    st.button("← Back", key="jobs_back", type="tertiary", on_click=go, args=("inputs",), kwargs={"ad_open": None})
    st.markdown(ui.h1("Pick a job ad", "md"), unsafe_allow_html=True)
    search_col, _ = st.columns([1.2, 1])
    query = search_col.text_input("Search", key="job_q", placeholder="Search a title, company or skill",
                                  label_visibility="collapsed")
    role = st.pills("Role", ads.ROLE_CHIPS, key="job_role", default="All roles", label_visibility="collapsed")
    loc = st.pills("Location", ads.LOCATIONS, key="job_loc", default="Anywhere", label_visibility="collapsed")
    rows = ads.search(query, role or "All roles", loc or "Anywhere")
    if not rows:
        st.markdown("<div class='k-serif k-mute' style='font-size:18px;padding:24px 0'>No ads match. "
                    "Try a broader role or location.</div>", unsafe_allow_html=True)
        return
    n = len(rows)
    st.caption(f"{n} ad{'' if n == 1 else 's'}, newest first" + (" (the first 30)" if n == 30 else "")
               + " · click one to read it")
    for a in rows:
        title_col, where_col, meta_col = st.columns([2.8, 2.2, 1.6], vertical_alignment="center")
        title_col.button(a["title"], key=f"ad_{a['id']}", type="tertiary", on_click=open_ad, args=(a["id"],))
        where_col.markdown(f"<span class='k-mute'>{ui.esc(a['company'])} · {ui.esc(a['location'])}</span>",
                           unsafe_allow_html=True)
        meta_col.markdown(f"<span class='k-small k-dim'>{posted(a['posted'])}</span> "
                          + (ui.chip(a["role"], colour=ui.LINK) if a["role"] != "Other" else ""),
                          unsafe_allow_html=True)
    ad = ads.by_id(ss.ad_open) if ss.ad_open else None
    if ad:
        st.dialog(ad["title"], width="large", on_dismiss=close_ad)(ad_body)(ad)


def ad_body(ad: dict) -> None:
    """The ad in its dialog; the button comes before the text, so a short screen shows it without scrolling."""
    st.markdown(f"<div class='k-mute' style='font-size:14px;margin:-4px 0 4px'>{ui.esc(ad['company'])} · "
                f"{ui.esc(ad['location'])} · {posted(ad['posted'])} · {ui.esc(ad['source'])}</div>",
                unsafe_allow_html=True)
    use_col, link_col = st.columns([1, 3], vertical_alignment="center")
    if ad["url"]:
        link_col.markdown(f"<a href='{ui.esc(ad['url'])}' target='_blank' class='k-small'>Open the original ↗</a>",
                          unsafe_allow_html=True)
    if use_col.button("Use this ad", key="use_job", type="primary"):
        ss.update(ad_box=ad["text"], ad_keep=ad["text"], ad_pick=ad, ad_mode_keep="Browse ads", ad_open=None)
        ss.toast = f"Using “{ad['title']} — {ad['company']}”."
        go("inputs")
        st.rerun()
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", ad["text"])           # scraped ads carry runs of blank lines
    st.markdown(f"<div class='k-preview'>{ui.esc(text)}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------- step 3: results

def bars_note(skills: list[dict], counted: bool, role: str | None) -> str:
    """One line on where the bars come from (the only data note left on the page)."""
    if not counted:
        return backend.role_source(role)
    who = backend.DEFAULT_ROLE if role is None else role      # a pasted ad is weighed by the Data Scientist ads
    note = "Bars: share of " + backend.role_source(who, skills[0].get("demand_source"), skills[0].get("demand_period"))
    if backend.source_2019_22(role):
        note += " Hover a bar for the 2019-22 share; a hatched bar is a skill those older ads never named."
    return note


def skills_section(skills: list[dict], counted: bool, noun: str, role: str | None = None) -> None:
    aside = "bar = how often employers ask" if counted else "core skills · no Australian ad counts yet"
    st.markdown(ui.h2(f"Skills the {noun} asks for", aside), unsafe_allow_html=True)
    for i, s in enumerate(skills):
        name_col, bar_col, status_col = st.columns([2.4, 4.4, 1.1], vertical_alignment="center")
        name_col.button(s["skill_label"] + (" ✦" if s["emerging"] else ""), key=f"open_{i}", type="tertiary",
                        on_click=open_gap, args=(s["skill_label"],))
        if counted:
            pct, old = s.get("demand_pct"), s.get("demand_pct_2019_22")
            new_since_2022 = old is not None and old < 1 <= (pct or 0)     # the 2019-22 ads never named it
            tip = ""
            if pct is not None:
                when = f" ({s['demand_period']})" if s.get("demand_period") else ""
                tip = f"{pct:.0f}% of {s.get('total_ads') or 'the'} ads{when}"
                if old is not None:
                    tip += f"; {old:.0f}% of the 2019-22 Seek ads"
            bar_col.markdown(ui.bar(pct, s["status"], new_since_2022, tip), unsafe_allow_html=True)
        else:
            bar_col.markdown(f"<span class='k-small k-mute'>{CORE_SOURCE.get(s.get('core_source'), '')}</span>",
                             unsafe_allow_html=True)
        status_col.markdown(ui.status_html(s["status"]), unsafe_allow_html=True)
    also = ss.result.get("also_in_ad") or []       # GPT-4o-mini found them; the vocabulary has no count for them
    if also:
        st.caption(f"Also in the ad, outside our skills list: {', '.join(also)}. Found by GPT-4o-mini; "
                   "not counted above.")
    st.caption(bars_note(skills, counted, role) + " Click a skill for the evidence and where to learn it.")
    if ss.user_type == "job" and ss.ad_keep.strip():
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
        whatif_box(code, f"wi_path_{code}")


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
    aside = (f"<span style='color:{ui.HAVE}'>closes {lp['gaps_closed']} of {lp['gaps_total']} gaps</span>"
             if lp["gaps_total"] else "")
    st.markdown(ui.h2("Your path", aside), unsafe_allow_html=True)
    plan = {p["subject_code"]: p for p in lp.get("plan", []) if isinstance(p, dict)}
    subjects = [code for code in lp["subjects"] if code in recs]
    if not subjects:
        msg = ("You already have every skill on the list." if not lp["gaps_total"]
               else "No subject in the Handbook text covers these gaps; see the Outside UTS tab.")
        st.markdown(f"<div class='k-serif k-mute' style='font-size:18px;line-height:1.5'>{msg}</div>",
                    unsafe_allow_html=True)
    for i in range(0, len(subjects), 3):                    # three cards to a row, in path order
        for col, code in zip(st.columns(3, gap="medium"), subjects[i:i + 3]):
            with col:
                path_card(code, recs[code], by, plan)
    open_gaps = [k for k in by if by[k]["status"] != "have"
                 and not any(k in recs[c]["covers"] for c in lp["subjects"] if c in recs)]
    no_subject = [k for k in open_gaps if not any(k in r["covers"] for r in res["recommendations"])]
    later = [k for k in open_gaps if k not in no_subject]
    notes = []
    if later:
        notes.append(f"Still open after this path: {', '.join(lc(u) for u in later)}. "
                     "Click a skill for the other subjects that teach it.")
    if no_subject:
        notes.append(f"No subject text names: {', '.join(lc(u) for u in no_subject)}.")
    if counted and lp["subjects"]:
        notes.append(f"The path covers {lp['demand_covered_pct']:.0f}% of the employer demand behind your gaps.")
    if notes:
        st.caption(" ".join(notes))
    if ss.user_type == "elective":
        if subjects:
            st.caption("Tick \"I've taken this\" on a subject and it joins your subjects from the Inputs page; "
                       "the gaps and the path are recomputed.")
    elif ss.whatif:
        st.button("Reset: count no subject as taken", key="whatif_reset", type="tertiary", on_click=reset_whatif)
    elif subjects:
        st.caption("Tick \"Already taken\" on a subject to see how your gaps and the path change.")


def outside_section(res: dict, by: dict) -> None:
    """The second tier of the path: outside courses for the gaps no UTS subject the student can take covers."""
    block = res["learning_path"].get("outside") or {}
    names = {r["subject_code"]: r for r in res.get("outside_recommendations", [])}
    chosen = [c for c in block.get("courses", []) if c in names]
    left_open = block.get("gaps_open_before", 0)
    aside = (f"<span style='color:{ui.HAVE}'>closes {block.get('gaps_closed', 0)} of the {left_open} gaps the UTS path "
             "leaves open</span>" if chosen else "")
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
        st.caption("Also teach these gaps: " + "; ".join(
            f"{r['subject_name']} ({r.get('provider', '')})" for r in others[:3]) + ".")
    st.caption("Free or free-to-audit where marked; none of these count for UTS credit.")


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
        st.caption("\"hot\": in the top third of certificates that live Australian ads for the role name "
                   "(Adzuna, 16 Oct 2026), or in the Robert Half 2027 Salary Guide. Exam price for one attempt, "
                   "from the vendor's page.")
    else:
        st.markdown("<span class='k-mute'>No certification in our list for this role yet.</span>",
                    unsafe_allow_html=True)


def page_results() -> None:
    res = ss.result
    skills = res["skills"]
    role = res.get("role")                                          # None in Job seeker mode
    counted = role is None or backend.has_ad_counts(role)           # False: core skills, no percentages
    by = {s["skill_label"]: s for s in skills}
    n_have = sum(s["status"] == "have" for s in skills)
    n_part = sum(s["status"] == "partial" for s in skills)
    gaps = [s for s in skills if s["status"] != "have"]

    top_l, top_r = st.columns([5, 1])
    top_l.button("← Change inputs", key="back_inputs", type="tertiary", on_click=go, args=("inputs",))
    top_r.button("Start over", key="start_over", type="tertiary", on_click=start_over)

    if not skills:
        if ss.engine.startswith("none"):
            st.error(f"The pipeline could not analyse this role: {ss.engine}")
        else:
            st.warning("I couldn't find any technical skills in that ad. Is it the full text?")
        return

    target = ad_title() if ss.user_type == "job" else role
    st.markdown(ui.eyebrow(ui.esc(target)), unsafe_allow_html=True)
    colour = ui.HAVE if not gaps else (ui.MISSING if len(gaps) >= 4 else ui.PARTIAL)
    if not gaps:
        tail = "skills — you already have them all."
    else:
        top = [lc(g["skill_label"]) for g in gaps if not g["emerging"]][:3] or [lc(g["skill_label"]) for g in gaps[:3]]
        tail = f"skills still to learn. Biggest gaps: {', '.join(top)}."
    st.markdown(ui.h1(f"<span style='color:{colour};font-weight:500'>{len(gaps)} of {len(skills)}</span> "
                      f"{ui.esc(tail)}", "lg"), unsafe_allow_html=True)
    st.markdown(ui.counts(n_have, n_part, len(gaps) - n_part), unsafe_allow_html=True)

    # One section at a time, full width (Quan's pick): the tabs below the verdict.
    tabs = ["Skills", "Your path", "Outside UTS"] + (["Certifications"] if role else [])
    if ss.get("results_tab") not in tabs:
        ss.results_tab = ss.get("results_tab_keep") if ss.get("results_tab_keep") in tabs else "Skills"
    st.segmented_control("Section", tabs, key="results_tab", label_visibility="collapsed")
    tab = ss.results_tab or "Skills"
    ss.results_tab_keep = tab
    if tab == "Skills":
        skills_section(skills, counted, "ad" if ss.user_type == "job" else "role", role)
    elif tab == "Your path":
        path_section(res, by, counted)
    elif tab == "Outside UTS":
        outside_section(res, by)
    else:
        certs_section(role)


# ---------------------------------------------------------------- step 3b: the evidence for one skill

def resume_note(s: dict) -> str:
    label = s["skill_label"]
    if s["status"] == "have":
        ev = s.get("resume_evidence") or ""
        taken = re.match(r"From (\d{5,6}) (.+?) \(taken\)$", ev)      # credit_taken(): "From 94692 Data Science Practice (taken)"
        if taken:
            return f"Covered by {taken.group(2)}, a subject you have taken."
        return ev or f"Your resume mentions {lc(label)}."
    if s["status"] == "partial":
        return f"Your resume says: \u201c{s.get('resume_evidence', '')}\u201d. Related, not quite the same skill."
    if ss.user_type == "elective":
        return f"No subject you ticked names {lc(label)}."
    return f"Nothing in your resume mentions {lc(label)}."


def short(text: str, n: int = 160) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n - 1].rstrip() + "\u2026"


def fact(label: str, value: str, sub: str = "", serif: bool = False) -> str:
    """One of the fact cards at the top of a skill page; `value` is already HTML-safe."""
    style = "font-family:'Literata',Georgia,serif;font-size:16px" if serif else "font-size:15px"
    html = (f"<div class='k-small k-dim'>{label}</div>"
            f"<div class='k-soft' style='{style};line-height:1.45;margin-top:3px'>{value}</div>")
    if sub:
        html += f"<div class='k-small k-mute' style='margin-top:6px'>{ui.esc(sub)}</div>"
    return ui.card(html)


def demand_fact(s: dict, counted: bool, role: str | None) -> tuple[str, str, str, bool]:
    """How often employers ask for the skill, as a fact card (label, value, sub, serif)."""
    if not counted:
        return ("Core skill", ui.esc(CORE_SOURCE.get(s.get("core_source"), "core skill of the role")),
                "no Australian ad counts for this role yet", False)
    pct, old = s.get("demand_pct"), s.get("demand_pct_2019_22")
    who = role or backend.DEFAULT_ROLE
    value = f"{pct:.0f}% of {s.get('total_ads') or 'the'} {ui.esc(who)} ads" if pct is not None else "no count"
    from skillabus.match import SOURCE_NAMES        # "jobspipe_2026" -> ("JobsPipe", "Sep-Oct 2026")
    when = SOURCE_NAMES.get(s.get("demand_source"), ("", s.get("demand_period") or ""))[1]
    sub = " · ".join(x for x in (when, f"{old:.0f}% in 2019-22" if old is not None else "") if x)
    return ("Employers ask", value, sub, False)


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
                v1.button(f"👍 {up}", key=f"up_{i}", width="stretch", on_click=vote, args=(r["subject_code"], label, "up"))
                v2.button(f"👎 {down}", key=f"down_{i}", width="stretch", on_click=vote,
                          args=(r["subject_code"], label, "down"))
                whatif_box(r["subject_code"], f"wi_ev_{i}")
        st.caption("👍 / 👎: does the subject really teach this? Your vote helps us check the matcher.")
    for d in [d for d in res["learning_path"].get("dropped", []) if label in d["covers"]][:2]:
        reason = re.sub(r"\b\d{5,6} (?=[A-Z])", "", d["reason"])          # names, not codes
        reason = reason if len(reason) <= 120 else reason[:117].rstrip() + "\u2026"
        st.caption(f"{SUBJECT_LABEL.get(d['subject_code'], d['subject_name'])} also teaches it, but {reason}.")


@st.fragment
def self_study_cards(label: str, role: str | None) -> None:
    """Self-study: the filters on one line, then up to three resources as cards. A fragment: a filter redraws this only."""
    ss.setdefault("level_filter", list(ss.level_keep))
    ss.setdefault("cost_filter", ss.cost_keep)
    head, f1, f2 = st.columns([1.1, 1.4, 1.7], vertical_alignment="center", gap="medium")
    head.markdown(ui.eyebrow("Self-study <span class='k-dim'>· not for credit</span>"), unsafe_allow_html=True)
    f1.pills("Level", list(backend.LEVELS), key="level_filter", selection_mode="multi", label_visibility="collapsed")
    f2.segmented_control("Cost", list(backend.COST_CHOICES), key="cost_filter", label_visibility="collapsed")
    levels = list(ss.level_filter or [])
    cost = ss.cost_filter or ss.cost_keep
    ss.level_keep, ss.cost_keep = levels, cost
    found = backend.self_study(label, levels, backend.COST_CHOICES[cost], role)
    if not found and backend.self_study(label, backend.LEVELS, backend.COST_CHOICES["Include paid"], role):
        st.markdown("<span class='k-mute'>Nothing with these filters: widen the level or cost above.</span>",
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
    st.markdown("<div style='display:flex;align-items:baseline;gap:16px;flex-wrap:wrap'>"
                + ui.h1(ui.esc(s["skill_label"]), "lg") + ui.status_html(s["status"], ui.STATUS_TEXT[s["status"]])
                + "</div>", unsafe_allow_html=True)

    facts = [demand_fact(s, counted, role)]
    if ss.user_type == "job":
        facts.append(("The ad says", f"\u201c{ui.esc(short(s['ad_evidence'], 170))}\u201d", "", True))
    facts.append(("Your resume" if ss.user_type != "elective" else "Your subjects", ui.esc(resume_note(s)), "", False))
    if s["emerging"]:
        facts.append(("✦ Emerging skill", "No ESCO concept yet", "kept and tracked as an emerging skill", False))
    for col, f in zip(st.columns(len(facts), gap="medium"), facts):
        col.markdown(fact(*f), unsafe_allow_html=True)

    if s["status"] == "have":
        st.markdown("<div class='k-serif k-soft' style='font-size:18px;line-height:1.5;margin-top:8px'>You already have "
                    "this skill, so it is not part of your path. Pick a missing or partial skill to see where to learn it."
                    "</div>", unsafe_allow_html=True)
        return
    uts_cards(s["skill_label"], res)
    self_study_cards(s["skill_label"], role)


# ---------------------------------------------------------------- the subject dialog

def subject_dialog(code: str) -> None:
    """Open the subject dialog; the title is the code, as a dialog's title is fixed when it is declared."""
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
        whatif_box(code, f"wi_dlg_{code}", "I've already taken this")


# ---------------------------------------------------------------- routing

if ss.toast:
    st.toast(ss.toast)
    ss.toast = None
if ss.step in ("results", "evidence") and not ss.result:
    ss.step = "inputs" if ss.user_type else "start"
if ss.step in ("inputs", "jobs") and not ss.user_type:
    ss.step = "start"
PAGES = {"start": page_start, "inputs": page_inputs, "jobs": page_jobs, "results": page_results,
         "evidence": page_evidence, "chat": page_chat}
top_bar()
PAGES[ss.step]()
view = (ss.step, ss.gap if ss.step == "evidence" else None)
if ss.get("view_shown") != view:          # a new page starts at the top; a tab, tick or filter keeps the place
    ss.view_shown = view
    ss.view_n = ss.get("view_n", 0) + 1
    st.html(ui.scroll_top(ss.view_n), unsafe_allow_javascript=True)
