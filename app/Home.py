"""Skillabus: which skills a role asks for that you lack, and which UTS subject fills each gap.

Run from the repo root:  streamlit run app/Home.py
"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
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

import backend  # noqa: E402
import chat  # noqa: E402
from skillabus import paths  # noqa: E402  (backend puts src/ on sys.path)

MOCK = paths.SAMPLES
FEEDBACK_CSV = paths.FEEDBACK
INK, BLUE, COPPER, PARTIAL, MUTED = "#0b1a2e", "#1f4e8c", "#c2410c", "#e9a27a", "#5b6678"
LAYER_LABEL = {
    "learning_objective": ("Learning objective", "taught and assessed"),
    "assessment": ("Assessment", "you are graded on it"),
    "weekly_topic": ("Topic", "covered in class"),
    "description": ("Description", "mentioned in the outline"),
}
ROLES = {
    "elective": ("Elective chooser", "Which subject moves me closest to my target role?"),
    "job": ("Job seeker", "What does my resume lack for this ad?"),
    "switch": ("Career switcher", "How far is my profile from a new role?"),
}
FAMILIES = backend.role_families()          # "Data & AI" -> ["Data Scientist", ...], all 11 target roles
FAMILY_OF = {role: family for family, roles in FAMILIES.items() for role in roles}
CORE_SOURCE = {"onet": "O*NET in-demand tool", "esco": "ESCO essential skill"}

st.set_page_config(page_title="Skillabus", page_icon="🎓", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Serif:ital@1&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, input, textarea { font-family: 'IBM Plex Sans', sans-serif; }
.block-container { padding-top: 3.2rem; max-width: 1200px; }
.hero { background: #0b1a2e; color: #fff; border-radius: 10px; padding: 22px 28px; margin-bottom: 18px; }
.hero h1 { color: #fff; font-size: 2.1rem; margin: 0; font-weight: 700; letter-spacing: -0.01em; }
.hero p { color: #c9d4e5; margin: 4px 0 0; font-size: 1.05rem; }
.hero.slim { padding: 10px 22px; }
.hero.slim h1 { font-size: 1.3rem; }
.layer-pill { display: inline-block; font-size: .78rem; padding: 1px 9px; border-radius: 999px; background: #eef2f7; color: #1f4e8c; margin: 2px 0 0; }
.eyebrow { font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: #8fa3c0; }
.role-q { color: #5b6678; min-height: 3.6em; line-height: 1.6; }
.big { font-size: 3rem; font-weight: 700; line-height: 1; }
.big-sub { color: #5b6678; margin-top: 4px; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-weight: 600; font-size: .85rem; margin-right: 6px; }
.pill.have { background: #d6e2f2; color: #1f4e8c; }
.pill.partial { background: #fbe6d9; color: #9a3412; }
.pill.missing { background: #f6dccd; color: #c2410c; }
.pill.new { background: #0b1a2e; color: #fff; }
.quote { font-family: 'IBM Plex Serif', serif; font-style: italic; font-size: 1.05rem; border-left: 3px solid #c2410c; padding: 4px 0 4px 14px; margin: 6px 0 10px; }
.quote.subject { border-left-color: #1f4e8c; }
.layer { font-size: .8rem; color: #5b6678; }
.path { border: 2px solid #1f4e8c; border-radius: 10px; padding: 16px 18px; }
.path h4 { margin: 0 0 6px; }
.muted { color: #5b6678; font-size: .9rem; }
.engine { font-size: .78rem; color: #5b6678; }
.core { list-style: none; padding-left: 0; margin: 4px 0 8px; }
.core li { margin: 7px 0; }
.col-head { font-size: .78rem; letter-spacing: .08em; text-transform: uppercase; color: #1f4e8c; font-weight: 600; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)


def lc(label: str) -> str:
    """Lower-case a skill name for running text, keeping acronyms: "Generative AI" -> "generative AI"."""
    return label[:1].lower() + label[1:] if len(label) > 1 and label[1].islower() else label


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


def gap_chart(skills: list[dict], share_of: str = "% of Seek ads") -> alt.Chart:
    df = pd.DataFrame(skills)
    df["label"] = df.skill_label + df.emerging.map({True: "  ✦", False: ""})
    df["pct_text"] = df.demand_pct.map(lambda v: f"{v:.0f}%")
    order = df.sort_values("demand_pct", ascending=False).label.tolist()
    y = alt.Y("label:N", sort=order, title=None,
              axis=alt.Axis(labelFontSize=14, labelLimit=260, labelColor=INK, ticks=False, domain=False))
    color = alt.Color("status:N", legend=None,
                      scale=alt.Scale(domain=["have", "partial", "missing"], range=[BLUE, PARTIAL, COPPER]))
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=22).encode(
        x=alt.X("demand_pct:Q", title=None, axis=None, scale=alt.Scale(domain=[0, max(100, df.demand_pct.max())])),
        y=y, color=color,
        tooltip=[alt.Tooltip("skill_label", title="Skill"), alt.Tooltip("status", title="Status"),
                 alt.Tooltip("demand_pct", title=share_of)])
    text = alt.Chart(df).mark_text(align="left", dx=6, fontSize=13, fontWeight="bold", color=INK).encode(
        x="demand_pct:Q", y=y, text="pct_text:N")
    return ((bars + text).properties(height=max(220, 38 * len(df)), usermeta={"embedOptions": {"actions": False}})
            .configure_view(stroke=None))


def core_list(skills: list[dict]) -> None:
    """The core skills of a role with no ad counts: have or missing and where each comes from, no bars."""
    items = "".join(
        f"<li><span class='pill {s['status']}'>{s['status'].capitalize()}</span> <b>{s['skill_label']}</b> "
        f"<span class='muted'>· {CORE_SOURCE.get(s.get('core_source'), '')}</span></li>"
        for s in skills)
    st.markdown(f"<ul class='core'>{items}</ul>", unsafe_allow_html=True)


def enrol_note(r: dict) -> str:
    """When a subject runs and what it needs first (recommend()'s offered, needs, unverified)."""
    parts = []
    if r.get("offered"):
        parts.append("Runs in " + ", ".join(r["offered"]))
    if r.get("needs"):
        parts.append("needs " + " and ".join(r["needs"]) + " first")
    elif r.get("unverified"):
        parts.append("prerequisites not confirmed")
    elif r.get("offered"):          # the baseline has no session data, so it claims nothing
        parts.append("no prerequisite")
    return " · ".join(parts)


def resource_line(r: dict) -> str:
    """One self-study resource: the title linked, then provider, level, format, hours and cost."""
    hours = f"{r['hours']:g} h" if r["hours"] is not None else "hours not stated"
    cost = f"A${r['cost_aud']}" if r["cost"] == "paid" and r.get("cost_aud") else r["cost"]
    title = r["title"].replace("[", "(").replace("]", ")")       # brackets would break the Markdown link
    return (f"**[{title}]({r['url']})**  \n"
            f"<span class='muted'>{r['provider']} · {r['level']} · {r['format'].replace('_', ' ')} · "
            f"{hours} · {cost}</span>")


def cert_line(c: dict) -> str:
    """One certification: name linked, vendor, exam code, level, exam price; "hot" only once it is measured."""
    price = f"A${c['cost_aud']}" if c["cost_aud"] and c["cost_aud"] != "varies" else "price varies by country"
    exam = f" · exam {c['exam_code']}" if c["exam_code"] else ""
    line = f"**[{c['cert']}]({c['official_url']})** · {c['vendor']}{exam} · {c['level']} · {price}"
    if c.get("hot", "").strip().lower() == "yes":    # blank until the Adzuna counts are in
        line += " · <span class='pill new'>hot</span>"
        if c.get("hot_reason"):
            line += f" <span class='muted'>{c['hot_reason']}</span>"
    return line


def show_uts(label: str, res: dict) -> None:
    """The "Learn at UTS" column for one skill: up to three subjects, the text that shows each teaches it, votes."""
    st.markdown("<div class='col-head'>Learn at UTS</div>", unsafe_allow_html=True)
    hits = [(r, e) for r in res["recommendations"] for e in r["evidence"] if e["skill_label"] == label]
    if not hits:
        st.markdown("<span class='muted'>No UTS subject you can take covers this skill in its Handbook text.</span>",
                    unsafe_allow_html=True)
    for i, (r, e) in enumerate(hits[:3]):
        layer, meaning = LAYER_LABEL.get(e["layer"], (e["layer"], ""))
        st.markdown(
            f"<b>{r['subject_code']} {r['subject_name']}</b><br>"
            f"<span class='layer-pill'>{layer}: {meaning}</span>"
            f"<div class='quote subject'>{e['text']}</div>", unsafe_allow_html=True)
        if enrol_note(r):
            st.caption(enrol_note(r))
        k = f"{r['subject_code']}_{label}_{i}"
        v1, v2, v3 = st.columns([1.3, 1.5, 2])
        took = v3.checkbox("I've taken it", key=f"took_{k}")
        if v1.button("👍 Teaches it", key=f"up_{k}"):
            save_vote(r["subject_code"], label, "up", took)
            st.toast("Thanks, your vote is saved.")
        if v2.button("👎 Not really", key=f"down_{k}"):
            save_vote(r["subject_code"], label, "down", took)
            st.toast("Thanks, your vote is saved.")
    # Subjects that teach it but the student cannot take (recommend()'s learning_path.dropped), the two strongest.
    dropped = [d for d in res["learning_path"].get("dropped", []) if label in d["covers"]]
    for d in dropped[:2]:
        st.caption(f"{d['subject_code']} {d['subject_name']} also teaches it, but {d['reason']}.")


def show_self_study(label: str, levels: list[str], cost: tuple, role: str | None) -> None:
    """The "Self-study" column for one skill: at most three resources that pass the level and cost filters."""
    st.markdown("<div class='col-head'>Self-study</div>", unsafe_allow_html=True)
    found = backend.self_study(label, levels, cost, role)
    if not found and backend.self_study(label, backend.LEVELS, backend.COST_CHOICES["Include paid"], role):
        st.markdown("<span class='muted'>Nothing with these filters: widen the level or cost above.</span>",
                    unsafe_allow_html=True)
    elif not found:
        st.markdown("<span class='muted'>No self-study resource in our list for this skill yet.</span>",
                    unsafe_allow_html=True)
    for r in found:
        st.markdown(resource_line(r), unsafe_allow_html=True)


def pick_family() -> None:
    """A new family was picked: start from its first role (the old role is not in the new list)."""
    ss.role_box = FAMILIES[ss.family_box][0]


# ---------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("step", "start")
ss.setdefault("role", None)
ss.setdefault("messages", [])


def go(step: str, **kw) -> None:
    ss.step = step
    for k, v in kw.items():
        ss[k] = v


# ---------------------------------------------------------------- header
if ss.step == "start":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">36118 Applied NLP · UTS Master of Data Science and Innovation</div>
      <h1>Skillabus</h1>
      <p>See which skills a role asks for that you don't have yet, and where to learn each one: a UTS subject or self-study.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<div class='hero slim'><h1>Skillabus</h1></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- sidebar chat
with st.sidebar:
    st.subheader("Ask about subjects")
    st.caption("Answers come from the UTS Handbook 2026 text. Your resume is never sent to the model.")
    if not chat.has_llm():
        st.caption("No OpenAI key set: showing the matching Handbook passages instead of a written answer.")
    for m in ss.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q = st.chat_input("e.g. Which subject teaches LLMs?")
    if q:
        ss.messages.append({"role": "user", "content": q})
        reply, sources = chat.answer(q, ss.get("result"))
        if sources and chat.has_llm():
            reply += "\n\n" + "\n".join(f"[{i + 1}] {s['source']}" for i, s in enumerate(sources))
        ss.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# ---------------------------------------------------------------- step 1: who are you
if ss.step == "start":
    st.markdown("### What would you like to find out?")
    cols = st.columns(3, gap="medium")
    for col, (key, (name, question)) in zip(cols, ROLES.items()):
        with col, st.container(border=True):
            st.markdown(f"**{name}**")
            st.markdown(f"<div class='role-q'>{question}</div>", unsafe_allow_html=True)
            st.button("Start", key=f"role_{key}", type="primary", width="stretch",
                      on_click=go, args=("input",), kwargs={"role": key})
    st.markdown(
        f"<p class='muted'>{len(FAMILY_OF)} data and IT roles, built on Australian job ads (Seek 2019-22, "
        "data_jobs 2023), the ESCO and O*NET occupation skills and the UTS Handbook 2026. "
        "Results are suggestions, not advice.</p>",
        unsafe_allow_html=True)

# ---------------------------------------------------------------- step 2: inputs
elif ss.step == "input":
    name, question = ROLES[ss.role]
    st.button("← Back", on_click=go, args=("start",))
    st.markdown(f"### {name}: {question}")
    sample_cv = (MOCK / "sample_resume.txt").read_text(encoding="utf-8")
    ad_text, taken = None, []
    # Streamlit forgets a widget's value once it is off screen, so inputs are kept in *_keep
    # and restored when the user comes back from the results.
    if "ad_box" not in ss:
        ss.ad_box = ss.get("ad_keep", "")
    if "taken_box" not in ss:
        ss.taken_box = ss.get("taken_keep", [])
    if "role_box" not in ss:
        ss.role_box = ss.get("role_keep", backend.DEFAULT_ROLE)
    if "family_box" not in ss:
        ss.family_box = FAMILY_OF[ss.role_box]

    left, right = st.columns(2, gap="large")
    with left:
        if ss.role == "job":
            st.markdown("**The job ad**")
            if st.button("Use the sample ad (Robert Walters, Data Scientist, Sydney)"):
                ss.ad_box = (MOCK / "sample_ad.txt").read_text(encoding="utf-8")
            ad_text = st.text_area("Paste the full ad", key="ad_box", height=320,
                                   placeholder="Paste the job title, responsibilities and requirements here.")
            ss.ad_keep = ad_text
        else:
            st.markdown("**Your target role**")
            family = st.radio("Field", list(FAMILIES), key="family_box", horizontal=True, on_change=pick_family)
            target = st.selectbox("Role", FAMILIES[family], key="role_box")
            ss.role_keep = target
            if backend.has_ad_counts(target):
                st.caption(f"The role is the 15 skills most often asked for in {backend.role_source(target)}")
            else:
                st.caption(f"{backend.role_source(target)} No percentages for this role.")
            if ss.role == "elective":
                options = backend.subjects()
                label = {c: f"{c} {n}" for c, n in options}
                taken = st.multiselect("Subjects you have taken (they count as skills you have)",
                                       [c for c, _ in options], format_func=lambda c: label[c], key="taken_box")
                ss.taken_keep = taken
    with right:
        st.markdown("**Your resume**")
        upload = st.file_uploader("PDF or text file", type=["pdf", "txt", "md"])
        if upload:
            ss.resume_keep = (upload.name, read_resume(upload))
        kept = ss.get("resume_keep")
        use_kept = False
        if kept and not upload:
            use_kept = st.checkbox(f"Use {kept[0]} (uploaded earlier)", value=True)
        use_sample = st.checkbox("Use the sample resume (synthetic early-career MDSI student)",
                                 value=not (upload or use_kept), disabled=bool(upload or use_kept))
        st.caption("Your resume stays in memory for this session and is never stored.")
    resume = kept[1] if (upload or use_kept) else (sample_cv if use_sample else "")

    ready = bool(resume or taken) and (ss.role != "job" or bool((ad_text or "").strip()))
    if st.button("Show my gaps", type="primary", disabled=not ready, key="show_gaps"):
        with st.spinner("Reading the ad and your resume..." if ss.role == "job" else "Reading your resume..."):
            result, engine = backend.analyse(resume, ad_text if ss.role == "job" else None, taken,
                                             role=ss.get("role_keep", backend.DEFAULT_ROLE))
        go("results", result=result, engine=engine)
        st.rerun()
    if not ready:
        st.caption("Add a resume" + (" and an ad" if ss.role == "job" else "") + " to continue.")

# ---------------------------------------------------------------- step 3: results
elif ss.step == "results":
    res = ss.result
    skills = res["skills"]
    by = {s["skill_label"]: s for s in skills}
    n_have = sum(s["status"] == "have" for s in skills)
    n_part = sum(s["status"] == "partial" for s in skills)
    n_miss = sum(s["status"] == "missing" for s in skills)
    target_role = res.get("role")                     # None in Job seeker mode
    counted = target_role is None or backend.has_ad_counts(target_role)    # False: core skills, no percentages
    target = "this ad" if ss.role == "job" else f"a {target_role} role"

    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.button("← Change inputs", on_click=go, args=("input",))
    with top_r:
        st.button("Start over", on_click=go, args=("start",), kwargs={"messages": []}, width="stretch")

    if not skills:
        if ss.engine.startswith("none"):
            st.error(f"The pipeline could not analyse this role: {ss.engine}")
        else:
            st.warning("I couldn't find any technical skills in that ad. Is it the full text?")
        st.stop()

    st.markdown(
        f"<div class='big'>{n_miss + n_part} of {len(skills)}</div>"
        f"<div class='big-sub'>skills {target} asks for are missing or partial in your profile</div>",
        unsafe_allow_html=True)
    pills = f"<span class='pill have'>Have · {n_have}</span>"
    if n_part:
        pills += f"<span class='pill partial'>Partial · {n_part}</span>"
    pills += f"<span class='pill missing'>Missing · {n_miss}</span>"
    st.markdown(f"<p style='margin-top:10px'>{pills}</p>", unsafe_allow_html=True)

    chart_col, path_col = st.columns([3, 2], gap="large")
    with chart_col:
        if counted:
            st.markdown("#### How often employers ask for each skill")
            st.altair_chart(gap_chart(skills, "% of Seek ads" if target_role is None else "% of the role's ads"),
                            width="stretch")
            if target_role is None:
                cap = "Bar = share of 3,204 Seek Australia Data Scientist ads (2019-22) naming the skill."
            else:
                cap = f"Bar = share of the role's ads naming the skill: {backend.role_source(target_role)}"
        else:
            st.markdown("#### Core skills of the role")
            core_list(skills)
            onet = backend.occupation(target_role, "onet")
            esco = backend.occupation(target_role, "esco")
            cap = (f"No percentages: there are no Australian ad counts for {target_role} yet. These are the O*NET "
                   f"in-demand tools of {onet['occupation_title']} ({onet['occupation_code']}), then the essential "
                   f"digital skills of the ESCO occupation '{esco['occupation_title']}', at most "
                   f"{backend.MAX_CORE_SKILLS}. Have = your resume names the skill.")
        if any(s["emerging"] for s in skills):
            cap += " ✦ = no ESCO concept yet, kept as an emerging skill."
        if target_role in (None, backend.DEFAULT_ROLE) and any(
                s["skill_label"] in ("Large language models", "Generative AI") for s in skills):
            cap += (" LLMs and generative AI are 0% in these ads because the ads predate ChatGPT; "
                    "15.8% of 247 US Data Scientist ads in 2023-24 ask for LLMs.")
        if any(s.get("found_by") == "llm" for s in skills):
            cap += (" Skills outside our dictionary were found by GPT-4o-mini; their bars are 0% "
                    "because the dictionary never counted them.")
        if res.get("soft_skills"):
            cap += f" The ad also asks for: {', '.join(lc(s) for s in res['soft_skills'])}."
        st.caption(cap)

    recs = {r["subject_code"]: r for r in res["recommendations"]}
    with path_col:
        lp = res["learning_path"]
        st.markdown("#### Your shortest path")
        if lp["subjects"]:
            items = "".join(
                f"<li><b>{c}</b> {recs[c]['subject_name']}<br><span class='muted'>covers "
                f"{', '.join(lc(s) for s in recs[c]['covers']) or 'no gap itself: a prerequisite'}</span></li>"
                for c in lp["subjects"] if c in recs)
            # Roles without ad counts have no demand shares, so only the gap count is shown.
            demand = (f"<span class='muted'>{lp['demand_covered_pct']:.0f}% of the employer demand behind your "
                      "gaps.</span>" if counted else "")
            st.markdown(
                f"<div class='path'><h4>{len(lp['subjects'])} subject{'s' if len(lp['subjects']) > 1 else ''}"
                f" close {lp['gaps_closed']} of {lp['gaps_total']} gaps</h4>"
                f"<ol style='padding-left:18px;margin:8px 0'>{items}</ol>{demand}</div>",
                unsafe_allow_html=True)
        else:
            st.info("No subject in the Handbook text covers these gaps." if n_miss + n_part
                    else "You already have every skill on the list.")
        open_gaps = [k for k in by if by[k]["status"] != "have"
                     and not any(k in recs[c]["covers"] for c in lp["subjects"] if c in recs)]
        no_subject = [k for k in open_gaps if not any(k in r["covers"] for r in res["recommendations"])]
        later = [k for k in open_gaps if k not in no_subject]
        if later:
            st.caption(f"Still open after this path: {', '.join(lc(u) for u in later)}. "
                       "Other subjects that teach them are listed below.")
        if no_subject:
            st.caption(f"No subject text names: {', '.join(lc(u) for u in no_subject)}.")
        # Second tier of recommend(): outside courses for the gaps the UTS path leaves open.
        outside = lp.get("outside", {})
        if outside.get("courses"):
            names = {r["subject_code"]: r["subject_name"] for r in res.get("outside_recommendations", [])}
            st.caption(f"Outside UTS, no credit: {'; '.join(names.get(c, c) for c in outside['courses'])} "
                       f"close {outside['gaps_closed']} of the {outside['gaps_open_before']} gaps the path leaves open.")

    st.divider()
    st.markdown("#### Where to learn each missing skill")
    gaps = [s for s in skills if s["status"] != "have"]
    if not gaps:
        st.markdown("<span class='muted'>Nothing missing: you already have every skill on the list.</span>",
                    unsafe_allow_html=True)
    else:
        f_level, f_cost = st.columns([3, 2], gap="large")
        levels = f_level.multiselect("Self-study level", list(backend.LEVELS), default=list(backend.LEVELS),
                                     key="level_filter")
        cost_choice = f_cost.radio("Self-study cost", list(backend.COST_CHOICES), index=1, horizontal=True,
                                   key="cost_filter")
        for i, s in enumerate(gaps):
            label = s["skill_label"]
            with st.expander(f"{label} · {s['status']}", expanded=i == 0):
                says = ("The ad says" if ss.role == "job" else "Employers say" if counted
                        else "Why it is a core skill")
                st.markdown(f"**{says}** <div class='quote'>{s['ad_evidence']}</div>", unsafe_allow_html=True)
                if s["status"] == "partial":
                    st.markdown(f"**Your resume says** <div class='quote subject'>{s['resume_evidence']}</div>",
                                unsafe_allow_html=True)
                if s["emerging"]:
                    st.markdown("<span class='pill new'>✦ outside ESCO</span> <span class='muted'>no ESCO concept "
                                "yet; kept and tracked as an emerging skill</span>", unsafe_allow_html=True)
                uts_col, self_col = st.columns(2, gap="large")
                with uts_col:
                    show_uts(label, res)
                with self_col:
                    show_self_study(label, levels, backend.COST_CHOICES[cost_choice], target_role)
        st.caption("Learn at UTS: subjects whose Handbook text names or closely matches the skill; your vote helps "
                   "us check they really teach it. Self-study: easiest and shortest first, at most three.")

    if target_role:
        st.divider()
        st.markdown("#### Certifications worth having")
        certs = backend.certifications(target_role)
        if certs:
            st.markdown("\n".join(f"- {cert_line(c)}" for c in certs), unsafe_allow_html=True)
            st.caption("Foundational first, then associate, professional and expert. Exam price for one attempt, "
                       "from the vendor's page. A \"hot\" tag appears once live Australian ads have been counted.")
        else:
            st.markdown("<span class='muted'>No certification in our list for this role yet.</span>",
                        unsafe_allow_html=True)

    with st.expander("All recommended subjects"):
        for r in res["recommendations"]:
            st.markdown(f"**{r['subject_code']} {r['subject_name']}** · score {r['score']:.2f} · "
                        f"covers {', '.join(lc(c) for c in r['covers']) or 'no gap itself: a prerequisite'} · "
                        f"[Handbook]({r['source_url']})")

    st.markdown(
        f"<p class='engine'>Engine: {ss.engine}. Skills matched with our {backend.dictionary_size()}-skill dictionary; "
        "subjects matched on Handbook learning objectives, assessments, topics and descriptions. "
        "Results are suggestions, not advice.</p>", unsafe_allow_html=True)
