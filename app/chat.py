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
PER_SUBJECT = 2        # passages kept per subject


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
                    "url": r.source_url, "subject_name": r.subject_name, "layer": r.layer})
    return out


def by_subject(passages: list[dict]) -> list[dict]:
    """One source per subject, best first: '36118 Applied Natural Language Processing' with up to PER_SUBJECT
    passages and the layers they come from. Five passages of one subject were five identical citations."""
    groups: dict[str, dict] = {}
    for p in passages:
        key = p.get("subject_code") or p.get("subject_name") or p["source"]
        if key not in groups:
            if len(groups) == MAX_SUBJECTS:
                continue
            groups[key] = {"subject_code": p.get("subject_code"), "subject_name": p.get("subject_name"),
                           "source": p["source"], "url": p.get("url"), "passages": []}
        if len(groups[key]["passages"]) < PER_SUBJECT:
            groups[key]["passages"].append(p)
    return list(groups.values())


def subject_label(s: dict) -> str:
    """'36118 Applied Natural Language Processing': code and name, as the Handbook lists a subject."""
    return " ".join(x for x in (s.get("subject_code"), s.get("subject_name")) if x) or s["source"]


def source_name(s: dict) -> str:
    """'36118 Applied Natural Language Processing (topic, learning objective)': a source line under the answer."""
    layers = dict.fromkeys(LAYER_NAME.get(p.get("layer"), p.get("layer") or "Handbook")
                           for p in s.get("passages", [s]))
    return f"{subject_label(s)} ({', '.join(layers)})"


def has_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def answer(question: str, gap: dict | None) -> tuple[str, list[dict]]:
    """Answer and its sources, one per subject (see by_subject)."""
    sources = by_subject(retrieve(question, k=POOL))
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
    # Code and name, so a student can find the subject in the Handbook and in My Student Admin.
    context = "\n".join(
        f"[{i + 1}] {subject_label(s)}: "
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
                "student's skill gaps only when the question is about them. Two to four sentences. "
                "Suggestions, not advice.")},
            {"role": "user", "content": f"{gaps}Subjects:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content, sources
