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


def named_in(question: str, sources: list[dict]) -> set[str]:
    """Codes of the subjects the question names ("I already took Data Visualization, ..."): a code, or the first two or
    more words of the subject's name, typos allowed (ratio 0.85). Used only to leave them out of a suggestion."""
    from difflib import SequenceMatcher
    q = _words(question)
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
    """Keep the sources the answer cites or names by code, in the order it first does, with the citations renumbered;
    all of them if it does neither."""
    first = {}
    for i, s in enumerate(sources, 1):
        hits = [m.start() for m in re.finditer(rf"\[{i}\]", reply)]
        if s.get("subject_code"):
            hits += [m.start() for m in re.finditer(rf"\b{re.escape(s['subject_code'])}\b", reply)]
        if hits:
            first[i] = min(hits)
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


def answer(question: str, gap: dict | None, taken: list[str] | tuple = (),
           home_course: str | None = None) -> tuple[str, list[dict]]:
    """Answer and its sources, one per subject (see by_subject). taken: the subjects the student ticked in the app;
    home_course: their course, for the subjects closed to them and, when they ask what to take, its own subjects."""
    home_course = home_course or backend.HOME_COURSE
    done, advice = set(taken), bool(ADVICE.search(question))
    passages = retrieve(question, k=POOL)
    if advice:
        lp = (gap or {}).get("learning_path")
        path = lp.get("subjects", []) if isinstance(lp, dict) else []
        passages = (subject_passages(path, done) + subject_passages(backend.course_subjects(home_course), done)
                    + passages)
        named = named_in(question, passages)          # taken or planned, as the student wrote them
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
    if done:
        names = dict(backend.subjects())
        gaps += f"Subjects the student has already taken: {', '.join(f'{c} {names.get(c, c)}' for c in sorted(done))}.\n"
    # Code and name, so a student can find the subject in the Handbook and in My Student Admin.
    context = "\n".join(
        f"[{i + 1}] {subject_label(s)}"
        + (f" (runs in {', '.join(s['sessions'])})" if s.get("sessions") else "") + ": "
        + " ".join(f"({LAYER_NAME.get(p.get('layer'), p.get('layer'))}) {p['text']}" for p in s["passages"])
        for i, s in enumerate(sources))
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
                "Suggestions, not advice.")},
            {"role": "user", "content": f"{gaps}Subjects:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return cited_only(resp.choices[0].message.content, sources)
