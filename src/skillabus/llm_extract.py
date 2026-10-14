"""Skill extraction, tier 3: GPT-4o-mini. Owner: Quan.

Same output as the dictionary and NER tiers (docs/data_contract.md section 1, before
normalisation): {"text", "method": "llm", "sentence", "kind"}.

Guards:
- personal details are masked before the call (mask_pii);
- every skill the model returns must appear verbatim in the text, so it cannot invent skills;
- the evidence sentence is taken from the text, not from the model;
- responses are cached on disk by a hash of model + prompt + text, so re-running the
  evaluation over 200 ads costs nothing the second time.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .text import mask_pii, sentence_with, text_units

MODEL = os.getenv("SKILLABUS_LLM_MODEL", "gpt-4o-mini")
PROMPT_VERSION = "v3"
MAX_CHARS = 12_000
CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache" / "llm_extract"

# v1 (4 Oct) split resumes into fragments ("joins", "charts", "writing queries") and kept vague
# phrases ("AI solutions"). v2 (10 Oct) merged too much: listed techniques ("supervised learning,
# classification, forecasting") vanished into "machine learning". v3 keeps every named technique,
# tool and library and drops only tasks and vague phrases. Checked on the Robert Walters ad, the
# sample resume and a CBA Sept 2026 ad; tune further on the labelled ads.
SYSTEM = """You extract skills from job ads and resumes for a skills-gap tool that compares the two.
Return JSON: {"skills": [{"text": "...", "kind": "hard" | "soft"}]}.

A skill is something a course could teach and an employer could ask for: a programming language,
tool, platform, library, method, technique, area of knowledge (statistics, deep learning,
generative AI, LLMs) or a soft skill (communication, stakeholder management, problem solving).

Rules:
- Return every named language, tool, library, platform, method and technique, including those
  listed under a broader skill. "Experience with supervised learning, classification or
  forecasting" gives supervised learning, classification and forecasting. "Python: pandas and
  matplotlib for data cleaning" gives Python, pandas, matplotlib and data cleaning.
  "Data visualisation: dashboards in Power BI" gives data visualisation and Power BI.
- Leave out tasks and activities that are not skills in themselves ("writing queries", "joins",
  "building dashboards", "presenting findings"), vague phrases ("AI solutions", "charts",
  "methodologies", "insights"), job titles, company names, degrees, years of experience,
  benefits and locations.
- "text" must be copied exactly from the document, character for character, so it can be found
  again ("PySpark", "predictive models", "LLM", "hypothesis testing"). Copy the shortest span that
  names the skill, without words like "skills", "experience", "knowledge of" or "strong".
- Every distinct skill once; if an abbreviation and its full form both appear, return one.
  No explanations."""


def _cache_path(text: str) -> Path:
    key = hashlib.sha256(f"{MODEL}|{PROMPT_VERSION}|{text}".encode()).hexdigest()[:24]
    return CACHE_DIR / f"{key}.json"


def _call(text: str, client) -> list[dict]:
    if client is None:
        if not os.getenv("OPENAI_API_KEY"):   # RuntimeError: the evaluation reports the tier as "not run"
            raise RuntimeError("OPENAI_API_KEY is not set and this text is not in the cache")
        from openai import OpenAI
        client = OpenAI(max_retries=3, timeout=60)
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
    )
    try:
        data = json.loads(resp.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        return []
    items = data.get("skills", []) if isinstance(data, dict) else []
    return [i for i in items if isinstance(i, dict) and isinstance(i.get("text"), str)]


def extract_llm(text: str, client=None, use_cache: bool = True) -> list[dict]:
    """Skill mentions found by the LLM. `client` is injectable for tests."""
    clean = mask_pii(text or "")[:MAX_CHARS]
    if not clean.strip():
        return []
    path = _cache_path(clean)
    if use_cache and path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
    else:
        raw = _call(clean, client)
        if use_cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    units = text_units(clean)
    out, seen = [], set()
    for item in raw:
        span = item["text"].strip()
        sentence = sentence_with(span, units)
        if not span or sentence is None or span.lower() in seen:
            continue  # not in the text: the model made it up, or rephrased it
        seen.add(span.lower())
        out.append({"text": span, "method": "llm", "sentence": sentence,
                    "kind": item.get("kind", "hard") if item.get("kind") in ("hard", "soft") else "hard"})
    return out


def main() -> None:
    """python -m skillabus.llm_extract app/mock/sample_ad.txt  (from the repo root, with src on PYTHONPATH)."""
    import sys

    from dotenv import load_dotenv

    from .normalise import normalise

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    text = Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else sys.stdin.read()
    for m in normalise(extract_llm(text)):
        print(f"{m['text']:30} {m['kind']:5} {m['how']:11} {m['vocab']:9} {m['skill_label']}")


def extract_llm_many(texts: list[str], client=None, progress: bool = True) -> list[list[dict]]:
    """Run over many documents (the 200 labelled ads), cached, one call per uncached document."""
    out = []
    for i, t in enumerate(texts, 1):
        out.append(extract_llm(t, client=client))
        if progress and i % 20 == 0:
            print(f"  llm extract: {i}/{len(texts)}")
    return out


if __name__ == "__main__":
    main()
