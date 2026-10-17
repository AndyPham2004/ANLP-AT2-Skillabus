"""The look of the app: the v2 design tokens (docs/design/README.md) as CSS and small HTML helpers.

Everything visual that Streamlit widgets cannot do on their own lives here, so app/Home.py reads
as the flow of the app, not as markup.
"""

from __future__ import annotations

import html
import re

INK, MUTE, DIM, DARK = "#e8e6e1", "#9a9a94", "#6b6c68", "#0a0b0c"
PAGE, PANEL, ASIDE, SOFT = "#121416", "#1b1e22", "#0e1012", "#c9c8c2"
HAVE, PARTIAL, MISSING, EMERGING, LINK = "#4fd1b8", "#f2b74f", "#f06d84", "#b89cff", "#8fbcff"
STATUS = {"have": HAVE, "partial": PARTIAL, "missing": MISSING}
STATUS_TEXT = {"have": "you have it", "partial": "partly covered", "missing": "missing"}
LAYER = {   # subject-profile layer -> (label, colour, what it means for the student)
    "assessment": ("Assessment", HAVE, "you are graded on it"),
    "learning_objective": ("Learning objective", LINK, "taught and assessed"),
    "weekly_topic": ("Weekly topic", EMERGING, "covered in class"),
    "description": ("Description", MUTE, "mentioned in the outline"),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Literata:ital,opsz,wght@0,7..72,400;0,7..72,500;0,7..72,600;1,7..72,400&family=Public+Sans:ital,wght@0,400;0,500;0,600;1,400&family=DM+Mono:wght@400;500&display=swap');
html, body, .stMarkdown, .stMarkdown p, .stMarkdown li, .stCaption, input, textarea, button, label,
[data-testid="stWidgetLabel"] p { font-family: 'Public Sans', system-ui, sans-serif; }
/* The design is drawn for 1280 x 820. Type and padding scale down with the viewport (clamp), so a
   laptop at 275% display scaling (1152 x 720 CSS px) still shows a whole screen at a time. */
header[data-testid="stHeader"] { background: transparent !important; height: 2.4rem !important; }
.block-container { max-width: 1240px; padding: 1.1rem 3rem 3rem; }
@media (max-width: 1200px) { .block-container { padding: 1.2rem 1.6rem 2.4rem; } }
section[data-testid="stSidebar"] { border-right: 1px solid rgba(255,255,255,.07); }
section[data-testid="stSidebar"] .block-container { padding: 1rem 1rem 1rem; }
h1, h2, h3, .k-h1, .k-h2, .k-serif { font-family: 'Literata', Georgia, serif; }
.k-mark { font-family: 'Literata', Georgia, serif; font-size: 22px; font-weight: 500; margin: 0 0 14px; }
.k-step { display: flex; flex-direction: column; align-items: center; padding-top: 7px; }
.k-step-dot { width: 22px; height: 22px; border-radius: 50%; border: 1.5px solid; display: grid; place-items: center; font: 500 11px 'DM Mono', monospace; box-sizing: border-box; }
.k-step-line { display: block; height: 30px; border-left: 1.5px dashed rgba(255,255,255,.16); margin-top: 4px; }
.k-step-sub { font-size: 11.5px; color: #6b6c68; line-height: 1.35; margin: -4px 0 8px 2px; }
.k-ctx { border-left: 2px solid rgba(255,255,255,.12); padding: 3px 10px; font-size: 12px; color: #9a9a94; line-height: 1.6; margin-top: 4px; }
.k-ctx b { color: #e8e6e1; font-weight: 500; }
.k-legend { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: #9a9a94; margin-top: 12px; }
.k-legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; vertical-align: middle; }
/* the top bar (no sidebar): name, horizontal stepper, context, chat button */
.k-hsteps { display: flex; align-items: center; gap: 10px; font-size: 13px; white-space: nowrap; overflow: hidden; }
.k-hstep { display: inline-flex; align-items: center; gap: 6px; }
.k-hdot { width: 18px; height: 18px; border-radius: 50%; border: 1.5px solid; display: inline-grid; place-items: center; font: 500 10px 'DM Mono', monospace; box-sizing: border-box; }
.k-hline { display: inline-block; width: 22px; border-top: 1.5px dashed rgba(255,255,255,.16); }
.k-hctx { font-size: 12px; color: #6b6c68; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.k-rule { border-top: 1px solid rgba(255,255,255,.08); margin: 4px 0 18px; }
section[data-testid="stSidebar"], div[data-testid="stSidebarCollapsedControl"], button[data-testid="stExpandSidebarButton"] { display: none !important; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] { padding-left: 2px; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-secondary"] { background: rgba(255,255,255,.07); border-color: transparent; }
.k-eyebrow { font-size: 13.5px; color: #9a9a94; margin: 0 0 6px; }
.k-h1 { font-family: 'Literata', Georgia, serif; font-weight: 400; letter-spacing: -.015em; line-height: 1.15; text-wrap: pretty; color: #e8e6e1; }
.k-h1.xl { font-size: clamp(26px, 3.3vw, 46px); max-width: 920px; }
.k-h1.lg { font-size: clamp(23px, 2.9vw, 38px); line-height: 1.2; }
.k-h1.md { font-size: clamp(21px, 2.5vw, 34px); letter-spacing: -.01em; }
.k-h2 { font-family: 'Literata', Georgia, serif; font-weight: 500; font-size: clamp(17px, 1.6vw, 21px); color: #e8e6e1; }
.k-card-title { font-family: 'Literata', Georgia, serif; font-size: clamp(18px, 1.8vw, 24px); font-weight: 500; }
.k-accent { width: 34px; height: 3px; border-radius: 2px; margin: 2px 0 12px; }
/* the Inputs page: what you have | your goal, a hairline between the two columns */
.k-big { font: 500 12.5px/1 'Public Sans', system-ui, sans-serif; letter-spacing: .07em; text-transform: uppercase; color: #c9c8c2; margin: 14px 0 6px; }
.st-key-goal_col { border-left: 1px solid rgba(255,255,255,.08); padding-left: clamp(18px, 2.4vw, 32px); }
/* Streamlit 1.65 scrolls a pills row sideways; the role rows wrap instead, with smaller pills */
.st-key-goal_col [role="radiogroup"] { flex-wrap: wrap !important; overflow: visible !important; row-gap: 6px; }
.st-key-goal_col [data-testid="stVerticalBlock"] { gap: .55rem; }
.st-key-goal_col button[data-variant="pills"] { min-height: 0 !important; padding: 2px 11px !important; }
.st-key-goal_col button[data-variant="pills"] p { font-size: 13px !important; }
div[data-testid="stVerticalBlockBorderWrapper"] { transition: border-color .15s; }
div[data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: rgba(255,255,255,.3); }
/* Streamlit centres a button's label through two inner flex wrappers; the sidebar steps read left to right. */
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"],
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] div,
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] span { justify-content: flex-start; text-align: left; }
section[data-testid="stSidebar"] button[data-testid^="stBaseButton"] { padding-left: 10px; }
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] div[data-testid="stMarkdownContainer"],
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] p { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.35; }
.k-mute { color: #9a9a94; } .k-dim { color: #6b6c68; } .k-soft { color: #c9c8c2; }
/* st.caption fades notes with opacity .6, which sinks them into the charcoal on a laptop screen:
   full opacity, soft ink. */
[data-testid="stCaptionContainer"] { opacity: 1 !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #c9c8c2 !important; }
.k-small { font-size: 13px; } .k-body { font-size: 15px; line-height: 1.5; }
.k-mono { font-family: 'DM Mono', monospace; }
.k-card { background: #1b1e22; border: 1px solid rgba(255,255,255,.07); border-radius: 6px; padding: 16px 18px; margin-bottom: 10px; }
.k-dashed { border: 1px dashed rgba(255,255,255,.2); border-radius: 6px; padding: 16px 18px; margin-bottom: 10px; }
.k-counts { display: flex; gap: 10px; font-size: 15px; flex-wrap: wrap; margin: 14px 0 6px; }
.k-count { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; }
.k-count b { font-family: 'DM Mono', monospace; font-weight: 500; }
.k-chip { display: inline-block; font-size: 13px; padding: 3px 9px; border-radius: 999px; margin: 0 6px 6px 0; }
.k-bar { height: 12px; background: rgba(255,255,255,.06); border-radius: 2px; overflow: hidden; }
.k-bar > span { display: block; height: 100%; }
.k-status { font-size: 14px; display: inline-flex; align-items: center; gap: 7px; white-space: nowrap; }
.k-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }
.k-quote { margin: 0 0 8px; padding: 16px 18px; background: #1b1e22; border-left: 3px solid #3a3c3e; font-family: 'Literata', Georgia, serif; font-size: 17px; line-height: 1.6; color: #c9c8c2; }
.k-note { margin: 0 0 8px; padding: 16px 18px; background: #1b1e22; border-left: 3px solid #3a3c3e; font-size: 15px; color: #c9c8c2; line-height: 1.55; }
.k-ad { font-family: 'Literata', Georgia, serif; font-size: 16px; line-height: 1.7; color: #c9c8c2; white-space: pre-line; padding: 6px 10px 0; }
.k-ad mark { color: #e8e6e1; padding: 0 2px; border-radius: 2px 2px 0 0; border-bottom: 2px solid; }
.k-layer { font-size: 13px; padding: 2px 9px; border-radius: 999px; white-space: nowrap; }
.k-preview { font-family: 'Literata', Georgia, serif; font-size: 16px; line-height: 1.65; color: #c9c8c2; white-space: pre-line; max-height: 380px; overflow: auto; }
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] div,
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] span { justify-content: flex-start; text-align: left; }
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] { padding-left: 0; padding-right: 0; }
div[data-testid="stButton"] button[data-testid="stBaseButton-tertiary"] p { font-size: 15px; }
button[data-testid="stBaseButton-primary"] { color: #0a0b0c !important; transition: transform .12s, filter .15s; }
button[data-testid="stBaseButton-primary"] p { font-weight: 500; font-size: 16px; color: #0a0b0c !important; }
button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); }
button[data-testid="stBaseButton-primary"]:active { transform: translateY(1px); }
button[data-testid="stBaseButton-primary"]:disabled { background: #2a2d31 !important; border-color: #2a2d31 !important; }
button[data-testid="stBaseButton-primary"]:disabled p { color: #6b6c68 !important; }
/* Chosen pill / segment: a quiet tinted fill with the accent as its border, not a solid light block. */
button[data-testid="stBaseButton-pillsActive"], button[data-testid="stBaseButton-segmented_controlActive"] {
  background: rgba(143,188,255,.14) !important; border-color: #8fbcff !important; color: #e8e6e1 !important; }
button[data-testid="stBaseButton-pillsActive"] p, button[data-testid="stBaseButton-segmented_controlActive"] p { color: #e8e6e1 !important; font-weight: 500; }
button[data-testid="stBaseButton-pills"], button[data-testid="stBaseButton-segmented_control"] { transition: border-color .15s, background .15s; }
button[data-testid="stBaseButton-pills"]:hover, button[data-testid="stBaseButton-segmented_control"]:hover { border-color: rgba(255,255,255,.4) !important; }
.k-mono, .k-count b { font-variant-numeric: tabular-nums; }
div[data-testid="stDataFrame"] { border-radius: 6px; overflow: hidden; }
div[data-testid="stTextArea"] textarea { font-family: 'Literata', Georgia, serif; font-size: 16px; line-height: 1.6; }
/* A chosen item in a multiselect: Streamlit paints it in the (light) primary colour with light text. Dark chip instead.
   Streamlit 1.65 marks each chip with data-tag (it was BaseWeb's span[data-baseweb="tag"] before). */
div[data-testid="stMultiSelect"] [data-tag] { background: #2a2d31 !important; border: 1px solid rgba(255,255,255,.14); }
div[data-testid="stMultiSelect"] [data-tag] * { color: #e8e6e1 !important; fill: #e8e6e1 !important; }
div[data-testid="stChatMessage"] { background: transparent; padding: 4px 0; }
/* The chat page: one reading width; avatars in the page's colours, not Streamlit's red and orange squares. */
.st-key-chat_box { max-width: 860px; }
div[data-testid="stChatMessageAvatarUser"], div[data-testid="stChatMessageAvatarAssistant"] {
  background: #1b1e22 !important; border: 1px solid rgba(255,255,255,.18); border-radius: 50%; color: #9a9a94 !important; }
div[data-testid="stChatMessageAvatarAssistant"] { border-color: #8fbcff; color: #8fbcff !important; }
div[data-testid="stChatMessageAvatarUser"] svg, div[data-testid="stChatMessageAvatarAssistant"] svg { fill: currentColor; color: inherit; }
/* Skill page: one band. Left, the share of ads then and now on one 0-100% scale; right, a coloured line per fact. */
.k-band { display: grid; grid-template-columns: minmax(220px, 300px) minmax(0, 1fr); gap: 32px; align-items: center;
  background: #1b1e22; border: 1px solid rgba(255,255,255,.1); border-radius: 8px; padding: 18px 22px; margin: 6px 0 18px; }
@media (max-width: 760px) { .k-band { grid-template-columns: 1fr; gap: 18px; } }
.k-bars, .k-bars-x { display: grid; grid-template-columns: repeat(var(--n), 96px); gap: 16px; padding: 0 12px; }
.k-bars { height: 112px; align-items: end; border-bottom: 1px solid rgba(255,255,255,.16); margin-top: 8px; }
.k-tbar { display: grid; justify-items: center; align-content: end; gap: 4px; }
.k-tbar span { font-family: 'DM Mono', monospace; font-size: 16px; color: #e8e6e1; font-variant-numeric: tabular-nums; }
.k-tbar b { width: 44px; background: var(--c); border-radius: 3px 3px 0 0; }
.k-bars-x div { text-align: center; font-size: 12.5px; color: #9a9a94; line-height: 1.35; padding-top: 6px; }
.k-lines { display: grid; gap: 12px; }
.k-line { display: grid; grid-template-columns: 26px minmax(0, 1fr); gap: 10px; align-items: start; font-size: 15px;
  line-height: 1.5; color: #c9c8c2; }
.k-line b { font-weight: 500; }
.k-line q { font-family: 'Literata', Georgia, serif; quotes: none; }
.k-ic { width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center; font-size: 13px; font-weight: 600;
  background: rgba(255,255,255,.06); color: #9a9a94; }
.k-line.have .k-ic { background: rgba(79,209,184,.14); color: #4fd1b8; } .k-line.have b { color: #4fd1b8; }
.k-line.partial .k-ic { background: rgba(242,183,79,.14); color: #f2b74f; } .k-line.partial b { color: #f2b74f; }
.k-line.missing .k-ic { background: rgba(240,109,132,.14); color: #f06d84; } .k-line.missing b { color: #f06d84; }
.k-line.new .k-ic { background: rgba(184,156,255,.15); color: #b89cff; } .k-line.new b { color: #b89cff; }
/* Certifications: cards in rows of three, like the path's subject cards. */
.k-certs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 4px 0 6px; }
.k-cert { background: #1b1e22; border: 1px solid rgba(255,255,255,.1); border-radius: 6px; padding: 14px 16px;
  display: grid; gap: 6px; align-content: start; }
.k-cert a { color: #e8e6e1; font-weight: 500; text-decoration: none; line-height: 1.35; }
.k-cert a:hover { text-decoration: underline; text-decoration-color: #8fbcff; }
.k-cert .k-mono { font-family: 'DM Mono', monospace; font-size: 15px; color: #e8e6e1; }
.k-cert .k-chip { justify-self: start; }
div[data-testid="stElementContainer"]:has(.k-top) { display: none; }
</style>
"""


def esc(text) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def eyebrow(text: str) -> str:
    """Small muted label above a block; `text` may hold inline HTML."""
    return f"<div class='k-eyebrow'>{text}</div>"


def h1(text: str, size: str = "lg") -> str:
    """Serif headline: xl (start page), lg (results), md (inputs). `text` may hold inline HTML.

    A div, not <h1>: Streamlit's Markdown rebuilds heading tags (anchor link, its own size) and drops the class.
    """
    return f"<div class='k-h1 {size}' role='heading' aria-level='1'>{text}</div>"


def h2(text: str, aside: str = "") -> str:
    right = f"<span class='k-small k-dim' style='text-align:right'>{aside}</span>" if aside else ""
    return (f"<div style='display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:8px'>"
            f"<div class='k-h2' role='heading' aria-level='2'>{text}</div>{right}</div>")


def counts(have: int, partial: int, missing: int) -> str:
    def pill(n, word, colour):
        return f"<span class='k-count' style='background:{colour}1f;color:{colour}'><b>{n}</b> {word}</span>"
    return ("<div class='k-counts'>" + pill(have, "have", HAVE) + pill(partial, "partial", PARTIAL)
            + pill(missing, "missing", MISSING) + "</div>")


def chip(label: str, status: str | None = None, colour: str | None = None) -> str:
    c = colour or STATUS.get(status or "", MUTE)
    return f"<span class='k-chip' style='background:{c}24;color:{c}'>{esc(label)}</span>"


def status_html(status: str, text: str | None = None) -> str:
    c = STATUS.get(status, MUTE)
    return (f"<span class='k-status' style='color:{c}'><span class='k-dot' style='background:{c}'></span>"
            f"{esc(text or status)}</span>")


def bar(pct: float | None, status: str, hatched: bool = False, title: str = "") -> str:
    """One demand bar, 0-100. Hatched = a skill the older ads never named (new since 2022), as in the design.
    `title` is the hover text (the numbers behind the bar)."""
    if pct is None:
        return "<div class='k-bar'></div>"
    c = STATUS.get(status, MUTE)
    fill = f"repeating-linear-gradient(135deg,{c} 0 3px,transparent 3px 6px)" if hatched else c
    tip = f" title='{esc(title)}'" if title else ""
    return (f"<div class='k-bar'{tip}><span style='width:{max(0.0, min(100.0, pct)):.1f}%;background:{fill}'>"
            "</span></div>")


def quote(text: str, colour: str = "#3a3c3e") -> str:
    return f"<blockquote class='k-quote' style='border-left-color:{colour}'>“{esc(text)}”</blockquote>"


def note(text: str) -> str:
    return f"<div class='k-note'>{esc(text)}</div>"


def layer_pill(layer: str) -> str:
    label, colour, _ = LAYER.get(layer, (layer, MUTE, ""))
    return f"<span class='k-layer' style='background:{colour}1f;color:{colour}'>{esc(label)}</span>"


def scroll_top(n: int) -> str:
    """A script that scrolls the page to the top. Streamlit keeps the scroll offset across reruns, so a
    skill opened from low in the list opened half-way down its page. `n` makes each copy different, so
    the browser runs it again on the next new page."""
    return (f"<span class='k-top'></span><script>/* {n} */ "
            "document.querySelector('[data-testid=\"stMain\"]')?.scrollTo(0, 0);</script>")


def card(inner: str, dashed: bool = False) -> str:
    return f"<div class='{'k-dashed' if dashed else 'k-card'}'>{inner}</div>"


def highlight(text: str, skills: list[dict], regex_for) -> str:
    """The ad text with every skill mention marked in its status colour (issue #58).

    skills: gap rows (skill_label, status); regex_for(label) -> compiled pattern or None. Overlapping
    matches keep the longest; text outside the marks is HTML-escaped.
    """
    spans: list[tuple[int, int, str]] = []
    for s in skills:
        rx = regex_for(s["skill_label"])
        if rx is None:
            continue
        for m in rx.finditer(text):
            if m.end() > m.start():
                spans.append((m.start(), m.end(), s["status"]))
    spans.sort(key=lambda t: (t[0], -(t[1] - t[0])))
    out, pos = [], 0
    for start, end, status in spans:
        if start < pos:
            continue
        c = STATUS.get(status, MUTE)
        out.append(esc(text[pos:start]))
        out.append(f"<mark style='background:{c}38;border-bottom-color:{c}'>{esc(text[start:end])}</mark>")
        pos = end
    out.append(esc(text[pos:]))
    return "<div class='k-ad'>" + "".join(out) + "</div>"


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text or ""))
