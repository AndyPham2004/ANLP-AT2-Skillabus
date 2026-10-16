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


def source_name(p: dict) -> str:
    """'Applied Natural Language Processing (topic)': what a student reads, without the subject code."""
    if p.get("subject_name"):
        return f"{p['subject_name']} ({LAYER_NAME.get(p.get('layer'), p.get('layer') or 'Handbook')})"
    return p["source"]


def has_llm() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def answer(question: str, gap: dict | None) -> tuple[str, list[dict]]:
    """Answer and the passages it rests on."""
    passages = retrieve(question)
    if not passages:
        return ("I couldn't find anything about that in the UTS Handbook text I have. "
                "Try naming a skill or a subject."), []
    if not has_llm():
        lines = [f"- **{source_name(p)}**: {p['text']}" for p in passages[:3]]
        return "Here's what the Handbook says:\n\n" + "\n".join(lines), passages

    from openai import OpenAI

    gaps = ""
    if gap:
        missing = [s["skill_label"] for s in gap["skills"] if s["status"] != "have"]
        gaps = f"The student's skill gaps for their target role: {', '.join(missing) or 'none'}.\n"
    # Names, not codes, so the answer names subjects the way the rest of the app does.
    context = "\n".join(f"[{i + 1}] {source_name(p)}: {p['text']}" for i, p in enumerate(passages))
    resp = OpenAI().chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": (
                "You help UTS data science students choose subjects. Answer only from the numbered "
                "Handbook passages. Cite them like [1] at the end of a sentence; do not write the word "
                "\"passage\". If the passages do not answer the question, say so. Two to four sentences. "
                "Suggestions, not advice.")},
            {"role": "user", "content": f"{gaps}Passages:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content, passages
