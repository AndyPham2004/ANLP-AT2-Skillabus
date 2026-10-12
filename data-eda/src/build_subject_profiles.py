"""Build the four-layer subject profiles the pipeline matches against.

One row per piece of subject text, so a recommendation can cite the exact
sentence it came from and name which layer it sat in. Layers, strongest first:

    learning_objective  an SLO from the handbook
    assessment          an assessment item (collected by hand, see --assessments)
    weekly_topic        one entry from the subject's topic list
    description         one sentence of the subject description

Shapes are fixed by docs/data_contract.md section 3. Two notes on that contract:

  * `course` carries every course the subject belongs to, pipe-separated
    ("C04380|C04379"), because the contract's other rule - one row per piece of
    text - forbids repeating the same sentence once per course. Filter with
    `df.course.str.contains("C04372")`, not `==`.
  * The output has NO leading comment line. `data/processed/skills_seed_v2.csv`
    has one, and because the file also contains a literal `C#`, reading it with
    `pandas.read_csv(..., comment="#")` silently truncates that row to `C` with
    no aliases. Provenance for this file lives in the companion .md instead.

Usage (from data-eda/):
    python src/build_subject_profiles.py
    python src/build_subject_profiles.py --courses C04372 --out mdsi_only.csv
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]          # data-eda/
REPO = ROOT.parent                                  # the Skillabus repo
DEFAULT_SUBJECTS = ROOT / "data" / "raw" / "uts_subjects_2026.csv"
DEFAULT_ASSESSMENTS = REPO / "data" / "labels" / "subject_content.csv"
DEFAULT_SCRAPED_ASSESSMENTS = REPO / "data" / "processed" / "assessments_scraped.csv"
DEFAULT_OUT = REPO / "data" / "processed" / "subject_profiles.csv"

COLUMNS = ["subject_code", "subject_name", "course", "layer", "text", "source_url", "collected_by"]

# The handbook pages were served as UTF-8 and read as a single-byte codec, so a
# handful of punctuation marks arrived as two or three stray characters. The
# whole-string round-trip (encode latin-1, decode utf-8) does not work here
# because some of the damage is no longer valid UTF-8 - a stray 'Â' sits before
# a plain space. These are every damaged sequence in the file, counted.
MOJIBAKE = {
    "â\u0080\u0099": "'",    # right single quote
    "â\u0080\u0098": "'",    # left single quote
    "â\u0080\u009c": '"',    # left double quote
    "â\u0080\u009d": '"',    # right double quote
    "â\u0080\u0094": " - ",  # em dash
    "â\u0080\u0093": " - ",  # en dash
    "â\u0080¦": "...",  # ellipsis
    "â\u0080¢": "•",  # bullet: kept, it is a topic delimiter
    "â\u0080¯": " ",    # narrow no-break space
    "Â ": " ",          # no-break space
    "Â": "",                 # stray, left over from the above
}

SLO_SPLIT = re.compile(r"\s*SLO\s*\d+\s*:\s*")
CILO_TAIL = re.compile(r"\s*\(\s*CILOs?[^)]*\)\s*$", re.I)
TOPIC_SPLIT = re.compile(r"\s*(?:\||•|;|\n)\s*")
# `\s*` not `\s+`: some handbook text runs sentences together without a space
# ("...proposing solutions.This simulates a 'virtual' work environment...").
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s*(?=[A-Z(])")

MIN_TOPIC_CHARS = 4
MIN_SENTENCE_CHARS = 30
# A delimited topic longer than this is a prose paragraph that leaked into the
# topics field, not a topic. Sentence-split it so the evidence panel has
# something quotable; sentence boundaries are punctuation, not a guess.
LONG_TOPIC_CHARS = 200

log = logging.getLogger("subject_profiles")


def clean(raw) -> str:
    """Repair the handbook's encoding damage and collapse whitespace."""
    if not isinstance(raw, str):
        return ""
    text = raw
    for broken, fixed in MOJIBAKE.items():
        text = text.replace(broken, fixed)
    return re.sub(r"\s+", " ", text).strip()


def split_outcomes(raw: str) -> list[str]:
    """One string of 'SLO1: ... SLO2: ...' into one entry per outcome."""
    parts = [p.strip() for p in SLO_SPLIT.split(clean(raw)) if p.strip()]
    return [CILO_TAIL.sub("", p).strip() for p in parts]


def split_topics(raw: str) -> tuple[list[str], bool]:
    """Split a topic list. Returns the entries and whether boundaries were found.

    Some handbook pages lost their list markup during collection, leaving the
    topics run together. Two kinds of damage, and only one is recoverable:

      * Prose with sentence punctuation ("... the data analytics professional.
        Introduction to use generative AI in the data pipeline, understanding
        ...") splits cleanly on sentence boundaries. Worth doing: an unsplit row
        of 391 characters is a useless evidence snippet in the app.
      * No punctuation at all ("Case study background Advanced report writing
        Presentation techniques") has nothing to split on. Guessing at the
        capital letters would shred "Natural Language Processing", so the whole
        string is kept and the caller is told via the second return value.
    """
    text = clean(raw)
    if not text:
        return [], True
    def sentences(chunk: str) -> list[str]:
        out = [p.strip(" .-") for p in SENTENCE_SPLIT.split(chunk)]
        return [p for p in out if len(p) >= MIN_TOPIC_CHARS]

    parts = [p.strip(" .-") for p in TOPIC_SPLIT.split(text)]
    parts = [p for p in parts if len(p) >= MIN_TOPIC_CHARS]
    if len(parts) > 1:
        out: list[str] = []
        for part in parts:
            out += sentences(part) if len(part) > LONG_TOPIC_CHARS else [part]
        return out, True
    recovered = sentences(text)
    if len(recovered) > 1:
        return recovered, True
    return ([text] if text else []), False


def split_description(raw: str) -> list[str]:
    """Description into sentences, with fragments folded into the sentence before."""
    text = clean(raw)
    if not text:
        return []
    out: list[str] = []
    for part in SENTENCE_SPLIT.split(text):
        part = part.strip()
        if not part:
            continue
        if out and len(part) < MIN_SENTENCE_CHARS:
            out[-1] = f"{out[-1]} {part}"
        else:
            out.append(part)
    return out


def load_assessments(paths: list[Path] | Path) -> pd.DataFrame:
    """Read assessment rows from one or more files (hand-collected and scraped), concatenated."""
    frames = []
    for path in ([paths] if isinstance(paths, Path) else paths):
        if not path.exists():
            log.warning("no assessment file at %s", path)
            continue
        df = pd.read_csv(path, dtype=str).fillna("")
        missing = [c for c in ("subject_code", "layer", "text") if c not in df.columns]
        if missing:
            raise SystemExit(f"{path} is missing columns {missing}; see data/labels/README.md")
        df = df[df["layer"].astype(str).str.strip().str.lower() == "assessment"].copy()
        df["text"] = df["text"].map(clean)          # the handbook's encoding damage reaches these rows too
        log.info("read %d assessment rows from %s", len(df), path.name)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        frames.append(df[COLUMNS])
    if not frames:
        log.warning("the assessment layer will be empty")
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)


def build(subjects: pd.DataFrame, assessments: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows: list[dict] = []
    stats = {"subjects": len(subjects), "no_outcomes": [], "no_topics": [], "topics_unsplit": []}

    for _, s in subjects.iterrows():
        base = {
            "subject_code": s["subject_code"],
            "subject_name": clean(s["subject_name"]),
            "course": s.get("courses") if isinstance(s.get("courses"), str) else "",
            "source_url": s.get("handbook_url", ""),
            "collected_by": "Van Thong",
        }

        outcomes = split_outcomes(s.get("learning_outcomes"))
        if not outcomes:
            stats["no_outcomes"].append(s["subject_code"])
        rows += [{**base, "layer": "learning_objective", "text": t} for t in outcomes]

        topics, was_split = split_topics(s.get("topics"))
        if not topics:
            stats["no_topics"].append(s["subject_code"])
        elif not was_split:
            stats["topics_unsplit"].append(s["subject_code"])
        rows += [{**base, "layer": "weekly_topic", "text": t} for t in topics]

        rows += [
            {**base, "layer": "description", "text": t}
            for t in split_description(s.get("description"))
        ]

    df = pd.DataFrame(rows, columns=COLUMNS)
    if len(assessments):
        df = pd.concat([df, assessments], ignore_index=True)

    before = len(df)
    df = df[df["text"].str.len() > 0].drop_duplicates(subset=["subject_code", "layer", "text"])
    stats["dropped_duplicates"] = before - len(df)

    order = {"learning_objective": 0, "assessment": 1, "weekly_topic": 2, "description": 3}
    df = df.sort_values(
        ["subject_code", "layer", "text"], key=lambda c: c.map(order) if c.name == "layer" else c
    ).reset_index(drop=True)
    return df, stats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--subjects", type=Path, default=DEFAULT_SUBJECTS,
                        help="uts_subjects_2026.csv from the handbook collection")
    parser.add_argument("--assessments", type=Path, nargs="+",
                        default=[DEFAULT_ASSESSMENTS, DEFAULT_SCRAPED_ASSESSMENTS],
                        help="files whose assessment rows are merged in (hand-collected, then scraped)")
    parser.add_argument("--courses", nargs="*", default=None,
                        help="keep only subjects in these course codes, e.g. C04372")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.subjects.exists():
        raise SystemExit(
            f"{args.subjects} not found. The raw handbook file is not committed; "
            "re-run src/scrape_handbook.py or ask Van Thong for it, or pass --subjects."
        )

    subjects = pd.read_csv(args.subjects, dtype=str)   # keep leading zeros: 090043 is not 90043
    if args.courses:
        pattern = "|".join(re.escape(c) for c in args.courses)
        subjects = subjects[subjects["courses"].fillna("").str.contains(pattern)]
        log.info("filtered to %d subjects in %s", len(subjects), ", ".join(args.courses))

    df, stats = build(subjects, load_assessments(args.assessments))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")

    log.info("")
    log.info("Wrote %s: %d rows from %d subjects", args.out, len(df), stats["subjects"])
    for layer, n in df["layer"].value_counts().items():
        log.info("  %-18s %4d rows, %2d subjects", layer, n,
                 df[df.layer == layer].subject_code.nunique())
    if stats["dropped_duplicates"]:
        log.info("  dropped %d duplicate rows", stats["dropped_duplicates"])
    log.info("")
    for key, label in [("no_outcomes", "no learning objectives"),
                       ("no_topics", "no topic list"),
                       ("topics_unsplit", "topic list arrived without delimiters")]:
        codes = stats[key]
        if codes:
            log.info("%2d subjects with %s: %s", len(codes), label,
                     ", ".join(str(c) for c in codes))
    if not len(df[df.layer == "assessment"]):
        log.info("")
        log.info("No assessment layer: run data-eda/src/scrape_assessments.py, or drop hand-collected")
        log.info("rows into data/labels/subject_content.csv, and re-run.")


if __name__ == "__main__":
    main()
