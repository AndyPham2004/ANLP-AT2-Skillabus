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

MOCK = ROOT / "app" / "mock"
FEEDBACK_CSV = ROOT / "data" / "processed" / "feedback.csv"
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


def gap_chart(skills: list[dict]) -> alt.Chart:
    df = pd.DataFrame(skills)
    df["label"] = df.skill_label + df.emerging.map({True: "  ✦ new", False: ""})
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
                 alt.Tooltip("demand_pct", title="% of Seek ads")])
    text = alt.Chart(df).mark_text(align="left", dx=6, fontSize=13, fontWeight="bold", color=INK).encode(
        x="demand_pct:Q", y=y, text="pct_text:N")
    return ((bars + text).properties(height=max(220, 38 * len(df)), usermeta={"embedOptions": {"actions": False}})
            .configure_view(stroke=None))


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
      <p>See which skills a role asks for that you don't have yet, and which UTS subject teaches each one.</p>
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
            st.button("Start", key=f"role_{key}", type="primary", use_container_width=True,
                      on_click=go, args=("input",), kwargs={"role": key})
    st.markdown(
        "<p class='muted'>Built on 3,204 Seek Australia Data Scientist ads (2019-22), the ESCO skills "
        "vocabulary and the UTS Handbook 2026. Results are suggestions, not advice.</p>",
        unsafe_allow_html=True)

# ---------------------------------------------------------------- step 2: inputs
elif ss.step == "input":
    name, question = ROLES[ss.role]
    st.button("← Back", on_click=go, args=("start",))
    st.markdown(f"### {name}: {question}")
    sample_cv = (MOCK / "sample_resume.txt").read_text(encoding="utf-8")
    ad_text, taken = None, []

    left, right = st.columns(2, gap="large")
    with left:
        if ss.role == "job":
            st.markdown("**The job ad**")
            if st.button("Use the sample ad (Robert Walters, Data Scientist, Sydney)"):
                ss.ad_box = (MOCK / "sample_ad.txt").read_text(encoding="utf-8")
            ad_text = st.text_area("Paste the full ad", key="ad_box", height=320,
                                   placeholder="Paste the job title, responsibilities and requirements here.")
        else:
            st.markdown("**Your target role**")
            st.selectbox("Role", ["Data Scientist"], help="More roles once the 2026 ads are in.")
            st.caption("The role is the 15 skills most often asked for in 3,204 Seek Data Scientist ads.")
            if ss.role == "elective":
                options = backend.subjects()
                label = {c: f"{c} {n}" for c, n in options}
                taken = st.multiselect("Subjects you have taken (they count as skills you have)",
                                       [c for c, _ in options], format_func=lambda c: label[c])
    with right:
        st.markdown("**Your resume**")
        upload = st.file_uploader("PDF or text file", type=["pdf", "txt", "md"])
        use_sample = st.checkbox("Use the sample resume (synthetic early-career MDSI student)", value=upload is None)
        st.caption("Your resume stays in memory for this session and is never stored.")
    resume = read_resume(upload) if upload else (sample_cv if use_sample else "")

    ready = bool(resume or taken) and (ss.role != "job" or bool((ad_text or "").strip()))
    if st.button("Show my gaps", type="primary", disabled=not ready):
        with st.spinner("Reading the ad and your resume..."):
            result, engine = backend.analyse(resume, ad_text if ss.role == "job" else None, taken)
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
    target = "this ad" if ss.role == "job" else "a Data Scientist role"

    top_l, top_r = st.columns([3, 1])
    with top_l:
        st.button("← Change inputs", on_click=go, args=("input",))
    with top_r:
        st.button("Start over", on_click=go, args=("start",), kwargs={"messages": []}, use_container_width=True)

    if not skills:
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
        st.markdown("#### How often employers ask for each skill")
        st.altair_chart(gap_chart(skills), use_container_width=True)
        cap = "Bar = share of 3,204 Seek Australia Data Scientist ads (2019-22) naming the skill."
        if any(s["emerging"] for s in skills):
            cap += (" ✦ new: LLMs and generative AI are 0% in these ads because they predate ChatGPT; "
                    "15.8% of 247 US Data Scientist ads in 2023-24 ask for LLMs.")
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
                f"{', '.join(lc(s) for s in recs[c]['covers'])}</span></li>"
                for c in lp["subjects"] if c in recs)
            st.markdown(
                f"<div class='path'><h4>{len(lp['subjects'])} subject{'s' if len(lp['subjects']) > 1 else ''}"
                f" close {lp['gaps_closed']} of {lp['gaps_total']} gaps</h4>"
                f"<ol style='padding-left:18px;margin:8px 0'>{items}</ol>"
                f"<span class='muted'>{lp['demand_covered_pct']:.0f}% of the employer demand behind your gaps.</span></div>",
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

    st.divider()
    st.markdown("#### Why these subjects?")
    gaps = [s for s in skills if s["status"] != "have"]
    if gaps:
        pick = st.selectbox("Pick a skill to see the evidence", [g["skill_label"] for g in gaps])
        s = by[pick]
        ev_ad, ev_sub = st.columns(2, gap="large")
        with ev_ad:
            st.markdown("**The ad says**" if ss.role == "job" else "**Employers say**")
            st.markdown(f"<div class='quote'>{s['ad_evidence']}</div>", unsafe_allow_html=True)
            if s["status"] == "partial":
                st.markdown(f"**Your resume says** <div class='quote subject'>{s['resume_evidence']}</div>",
                            unsafe_allow_html=True)
            if s["emerging"]:
                st.markdown("<span class='pill new'>✦ new skill</span> <span class='muted'>not yet a concept "
                            "in ESCO; tracked as an emerging skill</span>", unsafe_allow_html=True)
        with ev_sub:
            st.markdown("**The subject says** <span class='muted'>· does it really teach this? Your vote helps us check.</span>", unsafe_allow_html=True)
            hits = [(r, e) for r in res["recommendations"] for e in r["evidence"] if e["skill_label"] == pick]
            if not hits:
                st.markdown("<span class='muted'>No subject text names this skill.</span>", unsafe_allow_html=True)
            for i, (r, e) in enumerate(hits[:3]):
                layer, meaning = LAYER_LABEL.get(e["layer"], (e["layer"], ""))
                st.markdown(
                    f"<b>{r['subject_code']} {r['subject_name']}</b><br>"
                    f"<span class='layer-pill'>{layer}: {meaning}</span>"
                    f"<div class='quote subject'>{e['text']}</div>", unsafe_allow_html=True)
                k = f"{r['subject_code']}_{pick}_{i}"
                v1, v2, v3 = st.columns([1.3, 1.5, 2])
                took = v3.checkbox("I've taken it", key=f"took_{k}")
                if v1.button("👍 Teaches it", key=f"up_{k}"):
                    save_vote(r["subject_code"], pick, "up", took)
                    st.toast("Thanks, your vote is saved.")
                if v2.button("👎 Not really", key=f"down_{k}"):
                    save_vote(r["subject_code"], pick, "down", took)
                    st.toast("Thanks, your vote is saved.")

    with st.expander("All recommended subjects"):
        for r in res["recommendations"]:
            st.markdown(f"**{r['subject_code']} {r['subject_name']}** · score {r['score']:.2f} · "
                        f"covers {', '.join(lc(c) for c in r['covers'])} · [Handbook]({r['source_url']})")

    st.markdown(
        f"<p class='engine'>Engine: {ss.engine}. Skills matched with our 138-skill dictionary; "
        "subjects matched on Handbook learning objectives, topics and descriptions. "
        "Results are suggestions, not advice.</p>", unsafe_allow_html=True)
