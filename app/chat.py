"""Chat about subjects and skills, grounded in the subject profiles.

Retrieval: skillabus.rag.retrieve() when Van Thong's FAISS index exists, otherwise TF-IDF
over the same subject text. Answer: GPT-4o-mini when OPENAI_API_KEY is set, otherwise the
retrieved passages themselves. Resumes are never sent to the model.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache

import numpy as np

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import backend  # noqa: F401  (puts src/ on the path)
import baseline

MODEL = "gpt-4o-mini"
# Words every question and every subject description share ("Which subject teaches ...",
# "This subject teaches you ..."): left in, they rank 49016's description first for any question.
STOP_WORDS = sorted(ENGLISH_STOP_WORDS | {"subject", "subjects", "teach", "teaches", "teaching", "taught",
                                          "course", "courses", "student", "students", "uts"})
LAYER_NAME = {"learning_objective": "learning objective", "assessment": "assessment",
              "weekly_topic": "topic", "description": "description"}
POOL = 15              # passages retrieved, so the answer can draw on several subjects
MAX_SUBJECTS = 4       # subjects shown and cited
MAX_CHOICES = 10       # subjects the model may choose from when the student asks what to take
PER_SUBJECT = 2        # passages kept per subject
HISTORY = 6            # earlier chat messages the model sees
FOLLOW_ON = re.compile(r"\b(it|its|that|this|those|these|them|they|more|else|another|other|others|again|instead|"
                       r"what about|how about|full plan|the plan)\b", re.I)
FOLLOW_UP = "FOLLOW-UP:"   # how the model marks a question back to the student
# "I took ..., which one more should I pick?": a request for a choice, so the student's own course subjects
# join the retrieved ones (words of the question alone found the subjects already taken).
ADVICE = re.compile(r"\b(took|taken|completed|already|planning|plan to|next semester|last semester|one more|"
                    r"another|pick|choose|elective|recommend|advise|advice|should i)\b", re.I)


@lru_cache(maxsize=1)
def _index():
    lay = baseline.resources().layers
    docs = (lay.subject_code + " " + lay.subject_name + ": " + lay.text).tolist()
    vec = TfidfVectorizer(stop_words=STOP_WORDS, ngram_range=(1, 2), sublinear_tf=True)
    return lay, vec, vec.fit_transform(docs)


def retrieve(question: str, k: int = 5) -> list[dict]:
    try:
        from skillabus.rag import retrieve as rag_retrieve
        return rag_retrieve(question, k=k)
    except Exception:
        pass
    lay, vec, mat = _index()
    sims = cosine_similarity(vec.transform([question]), mat).ravel()
    # TF-IDF cannot match a subject code; a question naming one ("what does 36118 teach?") searches that subject only.
    codes = set(re.findall(r"\b\d{5}\b", question)) & set(lay.subject_code.astype(str))
    if codes:
        inside = lay.subject_code.astype(str).isin(codes).to_numpy()
        sims = np.where(inside, sims + 1e-6, 0.0)  # + 1e-6 keeps that subject's rows even with no shared word
    out = []
    for i in sims.argsort()[::-1][:k]:
        if sims[i] <= 0:
            break
        r = lay.iloc[i]
        out.append({"text": r.text, "score": float(sims[i]),
                    "source": f"{r.subject_code} {r.subject_name} ({LAYER_NAME.get(r.layer, r.layer)})",
                    "url": r.source_url, "subject_code": r.subject_code, "subject_name": r.subject_name,
                    "layer": r.layer})
    return out


@lru_cache(maxsize=1)
def _rules():
    from skillabus.requisites import load_rules
    return load_rules()


def availability(code: str | None, home_course: str | None) -> tuple[bool, list[str]]:
    """(can this student ever take it, the sessions it runs in). Only reasons that do not depend on what the student
    has passed close a subject here (Bachelor-only for a postgraduate, not taught in 2026): the chat may not know
    every subject taken, and a missing prerequisite would wrongly hide, say, the capstone."""
    if not code:
        return True, []
    try:
        from skillabus.requisites import enrolment, sessions_offered
        rules = _rules()
        e = enrolment(code, set(), rules, home_course)
        closed = e["status"] == "closed" and e["reason"].startswith(("undergraduate", "not taught"))
        return not closed, sessions_offered(code, rules)
    except Exception:
        return True, []


def subject_passages(codes: list[str], exclude: set[str]) -> list[dict]:
    """One description sentence for each subject in `codes` (the path, the student's course), for a request to choose."""
    lay = baseline.resources().layers
    out = []
    for code in codes:
        if code in exclude:
            continue
        rows = lay[(lay.subject_code.astype(str) == code) & (lay.layer == "description")]
        if len(rows):
            r = rows.iloc[0]
            out.append({"text": r.text, "source": f"{code} {r.subject_name}", "url": r.source_url,
                        "subject_code": code, "subject_name": r.subject_name, "layer": "description"})
    return out


NAME_STOP = set(STOP_WORDS) | {"want", "give", "need", "help", "best", "good", "list", "year", "years", "semester",
                                "autumn", "spring", "plan", "study", "full", "take", "which", "what", "like", "know"}


def name_matches(question: str, k: int = 3) -> list[dict]:
    """Subjects whose name holds every topic word of a short question ("Which subject teaches Python?" -> 36122 Python
    Programming): the search ranks a subject's text, and 36118's Python exercises came first. Only for questions of
    one to three topic words; a long one names too many."""
    words = [w for w in _words(spell_out(question)) if w not in NAME_STOP and len(w) > 2 and not w.isdigit()]
    if not 1 <= len(words) <= 3:
        return []
    hits = [c for c, n in backend.subjects() if all(re.search(rf"\b{w}", n.lower()) for w in words)]
    return subject_passages(hits[:k], set())


def by_subject(passages: list[dict], exclude: set[str] = frozenset(), home_course: str | None = None,
               limit: int = MAX_SUBJECTS) -> list[dict]:
    """One source per subject, best first: '36118 Applied Natural Language Processing' with up to PER_SUBJECT
    passages, the layers they come from and the sessions it runs in. Five passages of one subject were five
    identical citations; a subject listed under two codes (42028 and 421028) counts once; subjects taken or
    closed to the student are left out."""
    groups: dict[str, dict] = {}
    for p in passages:
        code, name = p.get("subject_code"), p.get("subject_name")
        key = (name or code or p["source"]).strip().lower()
        if key not in groups:
            if len(groups) == limit or code in exclude:
                continue
            ok, sessions = availability(code, home_course)
            if not ok:
                continue
            groups[key] = {"subject_code": code, "subject_name": name, "source": p["source"], "url": p.get("url"),
                           "sessions": sessions, "passages": []}
        if len(groups[key]["passages"]) < PER_SUBJECT:
            groups[key]["passages"].append(p)
    return list(groups.values())


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", s.lower().replace("visualization", "visualisation"))


# Short forms students type that the Handbook spells out ("Which subject teaches ML?" found no ML subject).
ABBREVIATIONS = {"ML": "machine learning", "AI": "artificial intelligence", "NLP": "natural language processing",
                 "DL": "deep learning", "LLM": "large language models", "LLMs": "large language models",
                 "BI": "business intelligence", "GenAI": "generative AI", "DS": "data science"}


def spell_out(question: str) -> str:
    """The question with ABBREVIATIONS written in full, for retrieval only (case-sensitive, whole words)."""
    return re.sub(r"\b(" + "|".join(sorted(ABBREVIATIONS, key=len, reverse=True)) + r")\b",
                  lambda m: ABBREVIATIONS[m.group(1)], question)


DONE_OR_PLANNED = re.compile(r"\b(took|taken|completed|finished|done|passed|already|planning|plan to|going to take|"
                             r"will take|enrolled)\b", re.I)


def named_in(question: str, sources: list[dict], done_or_planned: bool = True) -> set[str]:
    """Codes of the subjects the question names, by code or by the first two or more words of the name, typos allowed
    (ratio 0.85). done_or_planned: only in a sentence that says the student took or plans to take them ("I already
    took Data Visualization, ..."); "Should I take 36121 or 36123?" names subjects to compare, so they stay."""
    from difflib import SequenceMatcher
    sentences = re.split(r"[.!?;\n]", question)
    q = _words(" ".join(s for s in sentences if not done_or_planned or DONE_OR_PLANNED.search(s)))
    out = set()
    for s in sources:
        code, name = s.get("subject_code"), _words(s.get("subject_name") or "")
        if not code:
            continue
        if code in q:
            out.add(code)
            continue
        for k in range(len(name), 1, -1):
            head = " ".join(name[:k])
            if any(SequenceMatcher(None, head, " ".join(q[i:i + k])).ratio() >= 0.85 for i in range(len(q) - k + 1)):
                out.add(code)
                break
    return out


def cited_only(reply: str, sources: list[dict]) -> tuple[str, list[dict]]:
    """The sources the answer names by code, in the order it names them, and the answer without [n] marks: it names
    each subject by code and name already, and a mark could disagree with the list (a [2] numbered after an earlier
    answer pointed at another subject). An answer that names no code keeps its marks, renumbered, and the sources
    they cite; none if it does neither ("I'm unable to answer that" listed four unrelated subjects)."""
    named = {}
    for i, s in enumerate(sources, 1):
        if s.get("subject_code"):
            hits = [m.start() for m in re.finditer(rf"\b{re.escape(s['subject_code'])}\b", reply)]
            if hits:
                named[i] = min(hits)
    if named:
        return re.sub(r"\s*\[\d+\]", "", reply), [sources[n - 1] for n in sorted(named, key=named.get)]
    first = {i: m.start() for i in range(len(sources), 0, -1) for m in re.finditer(rf"\[{i}\]", reply)}
    if not first:
        return reply, []
    order = sorted(first, key=first.get)
    new = {old: i + 1 for i, old in enumerate(order)}
    reply = re.sub(r"\[(\d+)\]", lambda m: f"[{new[int(m.group(1))]}]" if int(m.group(1)) in new else "", reply)
    return reply, [sources[n - 1] for n in order]


def subject_label(s: dict) -> str:
    """'36118 Applied Natural Language Processing': code and name, as the Handbook lists a subject."""
    return " ".join(x for x in (s.get("subject_code"), s.get("subject_name")) if x) or s["source"]


def source_name(s: dict) -> str:
    """A source line under the answer: code and name only. The layer stays in the model's context; shown here
    it was noise (the skill page and path cards are where a layer tells a student how a subject covers a skill)."""
    return subject_label(s)


def link_subjects(reply: str, sources: list[dict]) -> tuple[str, list[dict]]:
    """The answer with each source's first mention ('36103' or '36103 Statistical Thinking for Data Science') linked to
    its Handbook page, and the sources it does not mention. Linked in the text, the numbered list under every answer
    only repeated the subjects the answer had just named."""
    rest = []
    for s in sources:
        code, url = s.get("subject_code"), s.get("url")
        if not code or not url:
            rest.append(s)
            continue
        name = re.escape(s.get("subject_name") or "")
        pattern = rf"(?<![\[\w/]){re.escape(code)}\b(?:\s+{name})?" if name else rf"(?<![\[\w/]){re.escape(code)}\b"
        reply, n = re.subn(pattern, lambda m: f"[{m.group(0)}]({url})", reply, count=1)
        if not n:
            rest.append(s)
    return reply, rest


HANDBOOK = "https://coursehandbook.uts.edu.au"


def course_page(home_course: str | None) -> tuple[str, str]:
    """(label, url) of the student's course in the Handbook (scrape_handbook.py reads the same URL); the Handbook's
    front page for a student not enrolled yet."""
    if not home_course:
        return "the UTS Handbook", HANDBOOK
    name = dict(backend.courses()).get(home_course, f"UTS course {home_course}")
    return f"{name} ({home_course}) in the UTS Handbook", f"{HANDBOOK}/course/2026/{home_course}"


# A study plan or a course's structure: the chat does not build one (the app checks prerequisites and sessions, not
# credit-point rules); it points to the right course page in the Handbook, so it needs to know the course.
PLAN = re.compile(r"\b(study plan|plan|structure|core subjects?|electives?|credit points?|two[- ]years?|2[- ]years?|"
                  r"semester by semester|roadmap)\b", re.I)


def course_named(text: str) -> str | None:
    """The UTS course the text names: a code (C04372), MDSI, or a course name (the longest that appears)."""
    known = dict(backend.courses())
    code = next((c for c in re.findall(r"\bC\d{5}\b", text) if c in known), None)
    if code:
        return code
    if re.search(r"\bMDSI\b", text):
        return "C04372"
    low = spell_out(text).lower()                    # "Master of AI" -> Master of Artificial Intelligence
    names = sorted(((n, c) for c, n in known.items() if not re.search(r"\(C\d{5}\)$", n)), key=lambda x: -len(x[0]))
    return next((c for n, c in names if n.lower() in low), None)


def link_handbook(reply: str, home_course: str | None) -> str:
    """Link the first mention of the Handbook to the student's course page, unless the answer already links it. A link
    the model wrote to the Handbook's front page is pointed at the course page; text inside a link is left alone (a
    link put inside the model's own link label rendered as broken brackets)."""
    label, url = course_page(home_course)
    known = dict(backend.courses())
    reply = re.sub(rf"\]\({re.escape(HANDBOOK)}/?\)", f"]({url})", reply)
    # a link the model wrote to a course page that does not exist (C04444) goes to the course page
    reply = re.sub(rf"\]\({re.escape(HANDBOOK)}/course/\d{{4}}/(\w*)\)",
                   lambda m: m.group(0) if m.group(1) in known else f"]({url})", reply)
    if url in reply:
        return reply
    parts = re.split(r"(\[[^\]]*\]\([^)]*\))", reply)                   # odd items are existing links
    for i in range(0, len(parts), 2):
        parts[i], n = re.subn(r"(?:the )?(?:course's page in the )?UTS Handbook", lambda m: f"[{label}]({url})",
                              parts[i], count=1)
        if n:
            break
    return "".join(parts)


def fix_codes(reply: str, question: str = "") -> str:
    """Subject codes the model wrote that are not UTS subjects lose the code ("36119 Machine Learning" was invented);
    a real code followed by another subject's name gets its own name back ("36106 Data Analytics for Business"); a
    course code that is not a UTS course is dropped ("Master of Business Analytics (C04444)"). A code the student
    typed stays ("I don't have information on 99999")."""
    names, typed = dict(backend.subjects()), set(re.findall(r"\b[C]?\d{5,6}\b", question))
    courses = dict(backend.courses())
    reply = re.sub(r"\s*\((C\d{5})\)|(?<![/\w])(C\d{5})\b",
                   lambda m: m.group(0) if (m.group(1) or m.group(2)) in courses or (m.group(1) or m.group(2)) in typed
                   else "", reply)

    def fix(m):
        code, title = m.group(1), m.group(2) or ""
        if code in typed:
            return m.group(0)
        if code not in names:
            return title.lstrip()
        if title.strip() and not title.strip().lower().startswith(names[code].lower()[:12]):
            return f"{code} {names[code]}"
        return m.group(0)

    # a code, then the Title Case words that follow it (up to punctuation): the name the model gave it
    return re.sub(r"(?<![\w/\[])(\d{5,6})(?![\w/])((?:\s+[A-Z0-9][\w&'’-]*(?:\s+(?:and|of|for|in|to|the|&))?)*)",
                  fix, reply)


def link_courses(reply: str) -> str:
    """Link the first mention of every UTS course (by code, 'C04372', or by name, 'Master of Data Science and
    Innovation') to its Handbook page; text already inside a link is left alone. All 44 pages answered 200 on 17 Oct."""
    courses = backend.courses()
    by_name = sorted(((n, c) for c, n in courses if not re.search(r"\(C\d{5}\)$", n)), key=lambda x: -len(x[0]))
    parts = re.split(r"(\[[^\]]*\]\([^)]*\))", reply)                   # odd items are existing links
    done: set[str] = set()

    def link(text: str) -> str:
        for code, _ in courses:
            if code not in done and re.search(rf"\b{code}\b", text):
                text = re.sub(rf"\b{code}\b", f"[{code}]({HANDBOOK}/course/2026/{code})", text, count=1)
                done.add(code)
        for name, code in by_name:
            if code not in done and re.search(rf"(?<!\[){re.escape(name)}\b(?!\])", text):
                text = re.sub(rf"(?<!\[){re.escape(name)}\b(?!\])", f"[{name}]({HANDBOOK}/course/2026/{code})", text,
                              count=1)
                done.add(code)
        return text

    for i, part in enumerate(parts):
        if i % 2:
            done.update(re.findall(r"/course/2026/(C\d{5})", part))
        else:
            parts[i] = link(part)
    return "".join(parts)


def has_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def answer(question: str, gap: dict | None, taken: list[str] | tuple = (), home_course: str | None = None,
           history: list[dict] | tuple = ()) -> tuple[str, list[dict] | None]:
    """Answer and its sources, one per subject (see by_subject); sources None = the reply is a follow-up question.

    taken: the subjects the student ticked in the app; home_course: their course, for the subjects closed to them and,
    when they ask what to take, its own subjects; history: the chat so far ({"role", "content", "followup"?}), so a
    vague request can get one follow-up question and the student's reply is read together with the request.
    """
    history = list(history)[-HISTORY:]          # home_course None = not enrolled yet: no course subjects, no course rules
    replying = bool(history) and history[-1].get("followup", False)       # this message answers our follow-up
    query = question
    # a reply to our follow-up, or a short follow-on that points back ("Give me two more", "How about ...?"), is searched
    # with the message before; a short question of its own is not ("Which subject teaches ML?" after a Python question
    # was searched as Python and answered with an invented code)
    if replying or (history and len(question.split()) < 8 and FOLLOW_ON.search(question)):
        asked = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        query = f"{asked} {question}"
    done, advice = set(taken), bool(ADVICE.search(query))
    passages = name_matches(query) + retrieve(spell_out(query), k=POOL)
    # a subject the student asks about stays even when taken ("36106 or 36120 for deep learning?" with both ticked
    # found nothing); only the subjects the question does not name are left out as taken
    asked = named_in(query, passages, done_or_planned=False) - named_in(query, passages)
    done -= asked
    # the course the question names, else the student's; a plan for an unknown course asks which one, once, so the
    # answer can link the right course page
    named_course = course_named(question) or course_named(query)   # this message's course before an earlier one's
    course = named_course or home_course
    if PLAN.search(query) and not course and not replying:
        return ("Which UTS course are you in, or planning to take (for example the Master of Data Science and "
                "Innovation, C04372)? I'll point you to its structure in the Handbook."), None
    if PLAN.search(query) and course:
        # the link only: subjects suggested "for your goal" when no goal was given read as random (17 Oct test)
        label, url = course_page(course)
        return (f"The structure of the {label.replace(' in the UTS Handbook', '')} (core subjects, electives, credit "
                f"points) is on its page in the Handbook: [{label}]({url}). I can't lay out a full study plan here. "
                "Tell me your goal or the skills you want, and I can suggest electives; please confirm your plan "
                "with your course coordinator."), []
    advice = advice or bool(named_course)     # "How about the Master of Business Analytics?": its own subjects too
    if advice:
        lp = (gap or {}).get("learning_path")
        path = lp.get("subjects", []) if isinstance(lp, dict) else []
        # the path and what the question is about first, then the rest of the student's course
        passages = (subject_passages(path, done) + passages
                    + subject_passages(backend.course_subjects(course), done))
        named = named_in(query, passages) - asked     # taken or planned, as the student wrote them
        passages = [p for p in passages if p.get("subject_code") not in named]
    sources = by_subject(passages, done, course, MAX_CHOICES if advice else MAX_SUBJECTS)
    if not sources:
        return ("I couldn't find anything about that in the UTS Handbook text I have. "
                "Try naming a skill or a subject."), []
    if not has_llm():
        lines = [f"- **{source_name(s)}**: {s['passages'][0]['text']}" for s in sources[:3]]
        return "Here's what the Handbook says:\n\n" + "\n".join(lines), sources

    from openai import OpenAI

    gaps = ""
    if gap:
        missing = [s["skill_label"] for s in gap["skills"] if s["status"] != "have"]
        gaps = f"The student's skill gaps for their target role: {', '.join(missing) or 'none'}.\n"
    names = dict(backend.subjects())
    if done:
        gaps += f"Subjects the student has already taken: {', '.join(f'{c} {names.get(c, c)}' for c in sorted(done))}.\n"
    if asked & set(taken):
        gaps += ("The student asks about subjects they have already taken, "
                 f"{', '.join(f'{c} {names.get(c, c)}' for c in sorted(asked & set(taken)))}: still answer the "
                 "question in full (describe or compare them from the Handbook text), then add one short note that "
                 "they have taken them.\n")
    # Code and name, so a student can find the subject in the Handbook and in My Student Admin.
    context = "\n".join(
        f"[{i + 1}] {subject_label(s)}"
        + (f" (runs in {', '.join(s['sessions'])})" if s.get("sessions") else "") + ": "
        + " ".join(f"({LAYER_NAME.get(p.get('layer'), p.get('layer'))}) {p['text']}" for p in s["passages"])
        for i, s in enumerate(sources))
    follow_up = (
        "The student has just answered your follow-up question: answer now and do not ask another."
        if replying else
        "Only if the student asks what to take and names no goal, interest, skill, subject or skill gaps, in this "
        "message or earlier in the chat, reply "
        f"with one short follow-up question that starts with \"{FOLLOW_UP}\" and nothing else. Answer everything "
        "else directly: a question about a skill (abbreviations such as ML, AI, NLP or BI are clear) or about a "
        "named subject never needs one.")
    # an earlier answer without the source list the app adds under it: seen in the history, the model copied the list
    # into its next answer and the app added its own, so a repeated question showed it twice
    turns = [{"role": m["role"], "content": m.get("answer", m["content"])} for m in history]
    resp = OpenAI().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": (
                "You help UTS data science students choose subjects. Answer only from the numbered "
                "Handbook subjects. Name each subject by its code and name exactly as given, for example "
                "\"36118 Applied Natural Language Processing\". Cite them like [1] at the end of a sentence; "
                "do not write the word \"passage\". If they do not answer the question, say so. Mention the "
                "student's skill gaps only when the question is about them. Never suggest a subject the "
                "student has taken or says they have taken or plan to take, nor one whose name or topic is "
                "nearly the same (a second deep learning subject for someone taking Deep Learning). If the "
                "student names a session, suggest only subjects that run in it. Two to five sentences. "
                "Suggestions, not advice. " + follow_up)},
            *turns,
            {"role": "user", "content": f"{gaps}Subjects:\n{context}\n\nQuestion: {question}"},
        ],
    )
    reply = resp.choices[0].message.content.strip()
    reply = re.sub(r"(\n\s*\[\d+\] [^\n]*)+\s*$", "", reply).strip()   # a source list the model wrote itself
    at = reply.upper().find(FOLLOW_UP.upper())        # the marker, even after a sentence the model put before it
    if at != -1:
        return reply[at + len(FOLLOW_UP):].strip(), None
    return cited_only(link_courses(link_handbook(fix_codes(reply, question), course)), sources)
