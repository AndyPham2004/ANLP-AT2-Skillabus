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
    they cite; all sources if it does neither."""
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
        return reply, sources
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


def has_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def answer(question: str, gap: dict | None, taken: list[str] | tuple = (), home_course: str | None = None,
           history: list[dict] | tuple = ()) -> tuple[str, list[dict] | None]:
    """Answer and its sources, one per subject (see by_subject); sources None = the reply is a follow-up question.

    taken: the subjects the student ticked in the app; home_course: their course, for the subjects closed to them and,
    when they ask what to take, its own subjects; history: the chat so far ({"role", "content", "followup"?}), so a
    vague request can get one follow-up question and the student's reply is read together with the request.
    """
    home_course = home_course or backend.HOME_COURSE
    history = list(history)[-HISTORY:]
    replying = bool(history) and history[-1].get("followup", False)       # this message answers our follow-up
    query = question
    if replying:
        asked = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
        query = f"{asked} {question}"
    done, advice = set(taken), bool(ADVICE.search(query))
    passages = retrieve(spell_out(query), k=POOL)
    # a subject the student asks about stays even when taken ("36106 or 36120 for deep learning?" with both ticked
    # found nothing); only the subjects the question does not name are left out as taken
    asked = named_in(query, passages, done_or_planned=False) - named_in(query, passages)
    done -= asked
    if advice:
        lp = (gap or {}).get("learning_path")
        path = lp.get("subjects", []) if isinstance(lp, dict) else []
        # the path and what the question is about first, then the rest of the student's course
        passages = (subject_passages(path, done) + passages
                    + subject_passages(backend.course_subjects(home_course), done))
        named = named_in(query, passages) - asked     # taken or planned, as the student wrote them
        passages = [p for p in passages if p.get("subject_code") not in named]
    sources = by_subject(passages, done, home_course, MAX_CHOICES if advice else MAX_SUBJECTS)
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
        "Only if the student asks what to take and names no goal, interest, skill, subject or skill gaps, reply "
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
                "student names a session, suggest only subjects that run in it. Two to four sentences. "
                "Suggestions, not advice. " + follow_up)},
            *turns,
            {"role": "user", "content": f"{gaps}Subjects:\n{context}\n\nQuestion: {question}"},
        ],
    )
    reply = resp.choices[0].message.content.strip()
    reply = re.sub(r"(\n\s*\[\d+\] [^\n]*)+\s*$", "", reply).strip()   # a source list the model wrote itself
    if reply.upper().startswith(FOLLOW_UP.upper()):
        return reply[len(FOLLOW_UP):].strip(), None
    return cited_only(reply, sources)
