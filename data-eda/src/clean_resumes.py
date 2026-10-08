"""Clean the resume set: mask personal details, drop the HTML copy, flag data profiles.

The Kaggle Resume Dataset (snehaanbhawal) already replaces employer names with
"Company Name". It does not remove everything personal, so this script masks:

  * email addresses                 -> [EMAIL]   regex
  * phone numbers, US and international -> [PHONE]  regex
  * URLs, including LinkedIn        -> [URL]     regex
  * person names                    -> [NAME]    spaCy NER, then filters (below),
                                                 plus a regex for "Summary <Name> is a ..."

Why the name step needs filters. Resumes are written in capitalised fragments, and
en_core_web_sm tags 16,447 PERSON spans across this set - mostly "Developed",
"Maintained", "Dean", and skills such as "Java", "C++", "Oracle", "MS Word".
Masking those would destroy the resumes as a skill-extraction test set. A span is
masked only if all of these hold:

  1. two or more words, each capitalised like a name ("Judy Marshall", "Frank W. Spencer")
  2. the first word is a known first name (gender-guesser's ~40k international list)
  3. the exact span occurs in at most two resumes - a person's name is rare,
     "Active Directory" is not
  4. no word is a skill in our dictionary, and the span is not part of an O*NET
     tool name ("Spring Boot", "Allen Bradley", "Jack Henry")

Measured on a random 50 of the spans this masks, about half are real names (some
are public figures - "Walt Disney", "John F. Kennedy" - which costs nothing to
mask) and the rest are harmless phrases ("Dean List", "Boy Scouting"). Recall is
not guaranteed: a name in capitals, a single first name, or a first name outside
the list survives. Treat the output as de-identified, not anonymous.

There is no data-science category among the 24, so `n_data_skills` counts how
many of six core data skills a resume mentions. Filter on it to find the profiles
that are plausible inputs for a Data Scientist target role.

Usage:
    python src/clean_resumes.py              # ~5 minutes, most of it spaCy
    python src/clean_resumes.py --no-ner     # regex masking only, seconds
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
SKILL_SEED = ROOT / "config" / "skills_seed.csv"
ONET_TOOLS = ROOT / "data" / "raw" / "taxonomy_onet_v31" / "software_skills.csv"

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# Tight on purpose: a looser pattern matched date ranges like "2012 - 12".
PHONE = re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}(?!\d)"
                   r"|\+\d{1,3}[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,6}(?!\d)")  # international
URL = re.compile(r"https?://\s*\S+|www\.\S+|\b(?:linkedin|github)\.com/\S+", re.I)
# Belt and braces for the one phrasing spaCy misses: "Summary Jane Citizen is a ...".
SUMMARY_NAME = re.compile(
    r"(\bSummary\s+)[A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+(?=\s+(?:is|has|brings|was)\b)")

NAME_SHAPE = re.compile(
    r"^[A-Z][a-z]+(?:[-'][A-Z]?[a-z]+)?"            # first name, maybe hyphenated
    r"(?:\s+[A-Z]\.?)?"                             # optional middle initial
    r"(?:\s+[A-Z][a-z]+(?:[-'][A-Z]?[a-z]+)?){1,2}$")  # one or two surnames
MAX_DOC_FREQ = 2

DATA_SKILLS = {
    "python": r"\bpython\b",
    "sql": r"\bsql\b",
    "machine learning": r"machine learning",
    "statistics": r"\bstatistic",
    "data analysis": r"data analy",
    "tableau / power bi": r"tableau|power ?bi",
}

log = logging.getLogger("clean_resumes")


def mask_contacts(text: str) -> tuple[str, dict]:
    counts = {}
    for label, pattern, repl in [("email", EMAIL, "[EMAIL]"), ("phone", PHONE, "[PHONE]"),
                                 ("url", URL, "[URL]")]:
        text, n = pattern.subn(repl, text)
        counts[label] = n
    return text, counts


def protected_terms() -> tuple[set[str], str]:
    """Skill words from our dictionary, and O*NET tool names as one searchable blob."""
    seed = pd.read_csv(SKILL_SEED)
    words = set(seed.canonical.str.lower())
    words |= {a.strip().lower() for cell in seed.aliases.dropna() for a in cell.split("|")}
    tools = ""
    if ONET_TOOLS.exists():
        onet = pd.read_csv(ONET_TOOLS)
        col = next(c for c in onet.columns if "example" in c.lower())
        tools = "\n".join(onet[col].dropna().str.lower().unique())
    else:
        log.warning("%s not found - O*NET tool names are not protected", ONET_TOOLS)
    return words, tools


def mask_names(texts: list[str]) -> tuple[list[str], int, int]:
    """Mask person names with spaCy NER plus the four filters in the module docstring."""
    import gender_guesser.detector as gg
    import spacy

    nlp = spacy.load("en_core_web_sm",
                     disable=["parser", "lemmatizer", "tagger", "attribute_ruler"])
    first_names = gg.Detector(case_sensitive=False)
    skill_words, onet_tools = protected_terms()

    spans = []  # (doc index, start, end, text)
    for i, doc in enumerate(nlp.pipe(texts, batch_size=32)):
        spans += [(i, e.start_char, e.end_char, e.text) for e in doc.ents if e.label_ == "PERSON"]
    log.info("spaCy tagged %d PERSON spans; filtering", len(spans))

    doc_freq = pd.DataFrame(spans, columns=["doc", "s", "e", "text"]).groupby("text").doc.nunique()

    def is_name(span: str) -> bool:
        words = span.split()
        low = span.lower()
        return (len(words) >= 2
                and bool(NAME_SHAPE.match(span))
                and doc_freq.get(span, 0) <= MAX_DOC_FREQ
                and first_names.get_gender(words[0]) != "unknown"
                and not any(w in skill_words for w in low.split())
                and low not in onet_tools)

    keep = [s for s in spans if is_name(s[3])]
    by_doc: dict[int, list] = {}
    for i, start, end, _ in keep:
        by_doc.setdefault(i, []).append((start, end))

    out = list(texts)
    for i, ranges in by_doc.items():
        t = out[i]
        for start, end in sorted(ranges, reverse=True):   # right to left keeps offsets valid
            t = t[:start] + "[NAME]" + t[end:]
        out[i] = t
    return out, len(keep), len(by_doc)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-ner", action="store_true", help="skip spaCy name masking")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    raw = pd.read_csv(args.input, usecols=["ID", "Resume_str", "Category"])
    before = len(raw)
    raw = raw[raw.Resume_str.fillna("").str.strip().str.len() > 0]
    raw = raw.drop_duplicates(subset=["Resume_str"]).reset_index(drop=True)

    texts, totals, touched = [], dict(email=0, phone=0, url=0), dict(email=0, phone=0, url=0)
    for t in raw.Resume_str.fillna("").astype(str):
        t = re.sub(r"[ \t ]+", " ", t).strip()
        t, counts = mask_contacts(t)
        texts.append(t)
        for k, v in counts.items():
            totals[k] += v
            touched[k] += bool(v)

    names = docs_with_names = 0
    if not args.no_ner:
        texts, names, docs_with_names = mask_names(texts)
    summary_hits = 0
    for i, t in enumerate(texts):
        texts[i], n = SUMMARY_NAME.subn(r"\1[NAME]", t)
        summary_hits += n

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
    if args.no_ner:
        log.info("  names NOT masked (--no-ner)")
    else:
        log.info("  masked name  %4d times in %4d resumes (de-identified, not anonymous)",
                 names, docs_with_names)
    log.info("  masked name  %4d more by the 'Summary <Name> is' rule", summary_hits)
    log.info("")
    log.info("Data-relevant profiles (n_data_skills = how many of %d core data skills):",
             len(DATA_SKILLS))
    for k in (2, 3, 4):
        log.info("  >= %d: %4d resumes", k, int((out.n_data_skills >= k).sum()))


if __name__ == "__main__":
    main()
