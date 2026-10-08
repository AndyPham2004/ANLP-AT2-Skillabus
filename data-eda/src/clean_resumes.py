"""Clean the resume set: mask contact details, drop the HTML copy, flag data profiles.

The Kaggle Resume Dataset (snehaanbhawal) already replaces employer names with
"Company Name". It does not remove everything personal, so this script masks:

  * email addresses                 -> [EMAIL]
  * US phone numbers                -> [PHONE]
  * URLs, including LinkedIn        -> [URL]
  * a third-person summary opening  -> [NAME]   ("Summary Jane Citizen is a ...")

**Name masking is partial.** A regex cannot find names in general; it only catches
the one phrasing above. The rest is the app's job: per the ethics section, names,
emails and phones are masked with spaCy NER before any LLM call. This file is for
the team drive only and must never be committed (CONTRIBUTING section 3).

There is no data-science category among the 24, so `n_data_skills` counts how
many of six core data skills a resume mentions. Filter on it to find the profiles
that are plausible inputs for a Data Scientist target role.

Usage:
    python src/clean_resumes.py
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "raw" / "resumes_us_2021.csv"
DEFAULT_OUT = ROOT / "data" / "clean" / "resumes_us_2021_clean.csv"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Tight on purpose: a looser pattern matched date ranges like "2012 - 12".
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?!\d)"
                   r"|\+\d{1,3}[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,6}(?!\d)")  # international
URL = re.compile(r"https?://\s*\S+|www\.\S+|\b(?:linkedin|github)\.com/\S+", re.I)
SUMMARY_NAME = re.compile(
    r"(\bSummary\s+)([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)(?=\s+(?:is|has|brings|was)\b)")

DATA_SKILLS = {
    "python": r"\bpython\b",
    "sql": r"\bsql\b",
    "machine learning": r"machine learning",
    "statistics": r"\bstatistic",
    "data analysis": r"data analy",
    "tableau / power bi": r"tableau|power ?bi",
}

log = logging.getLogger("clean_resumes")


def mask(text: str) -> tuple[str, dict]:
    counts = {}
    for label, pattern, repl in [("email", EMAIL, "[EMAIL]"), ("phone", PHONE, "[PHONE]"),
                                 ("url", URL, "[URL]")]:
        text, n = pattern.subn(repl, text)
        counts[label] = n
    text, n = SUMMARY_NAME.subn(r"\1[NAME]", text)
    counts["name"] = n
    return text, counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    raw = pd.read_csv(args.input, usecols=["ID", "Resume_str", "Category"])
    before = len(raw)
    raw = raw[raw.Resume_str.fillna("").str.strip().str.len() > 0]
    raw = raw.drop_duplicates(subset=["Resume_str"]).reset_index(drop=True)

    texts, totals, touched = [], dict(email=0, phone=0, url=0, name=0), dict(email=0, phone=0, url=0, name=0)
    for t in raw.Resume_str.fillna("").astype(str):
        t = re.sub(r"[ \t ]+", " ", t).strip()
        t, counts = mask(t)
        texts.append(t)
        for k, v in counts.items():
            totals[k] += v
            touched[k] += bool(v)

    out = pd.DataFrame({"resume_id": raw.ID, "category": raw.Category, "resume_text": texts})
    hits = pd.DataFrame({k: out.resume_text.str.contains(v, case=False, regex=True)
                         for k, v in DATA_SKILLS.items()})
    out["n_data_skills"] = hits.sum(axis=1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")

    log.info("Wrote %s: %d resumes (%d empty or duplicate dropped, HTML copy dropped)",
             args.out, len(out), before - len(out))
    for k in totals:
        log.info("  masked %-5s %4d times in %4d resumes", k, totals[k], touched[k])
    log.info("  name masking is partial - see the docstring")
    log.info("")
    log.info("Data-relevant profiles (n_data_skills = how many of %d core data skills):",
             len(DATA_SKILLS))
    for k in (2, 3, 4):
        log.info("  >= %d: %4d resumes", k, int((out.n_data_skills >= k).sum()))


if __name__ == "__main__":
    main()
