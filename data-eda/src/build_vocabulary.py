"""One skill vocabulary: ESCO as the base, plus the skills ESCO lacks (plan D5).

Writes data/1_knowledge/skills/skills_vocabulary.csv, one row per skill. The plan is
docs/notes/data_it_scope_2026-10-14.md, section 3. Three parts, in this order:

  1. The 148 dictionary skills (skills_seed_v2.csv), used to detect skills in ads (used_for = extract).
     Each one's ESCO link was judged by hand in esco_link_review.csv; this script only copies it.
  2. Core skills of the ESCO and O*NET occupations of the 11 roles (used_for = core_skill). Not yet.
  3. IT skills ESCO lacks, each with ad-style aliases and found in at least 3 Australian ads. Not yet.

Columns:
  skill_id      esco:<uri> only when esco_match = exact (the data contract's form); otherwise
                skillabus:<slug>, so two tools under one wide ESCO concept (Tableau, Power BI ->
                "data visualisation software") keep different ids and match.py never confuses them
  label         display name; for part 1 the dictionary's canonical name, unchanged
  category      the dictionary's group
  source        esco (esco_match = exact) or added (ESCO lacks the skill, or has only a wider concept)
  esco_uri, esco_label   the related ESCO concept, also when it is wider (empty for none)
  esco_match    exact / close / broad (the ESCO concept is wider) / none, as in SKOS
                (exactMatch, closeMatch, broadMatch), the mapping relations ESCO itself uses
  reviewed_by   who checked the ESCO link
  aliases_ads   how ads write the skill, "|"-joined. Only rows with aliases are used for detection;
                ESCO labels never are (most ICT labels are 3+ word verb phrases ads do not use)
  strict        1 = aliases match case-sensitively (R, SAS, SAP, React)
  used_for      extract, core_skill, or extract;core_skill
  why_added     for added rows: why the row is ours and not ESCO's

To change a link: edit esco_link_review.csv (one row per dictionary skill, with a note for every
link that is not exact), rerun this script, commit both files. The script checks each link against
the committed ESCO table (the URI exists and carries the label written next to it) and refuses
links known to be wrong. skills_seed_v2.csv and skill_to_esco.csv stay as they are until the
pipeline reads this file (plan C2).

Usage (from the repo root):
    python data-eda/src/build_vocabulary.py
    python data-eda/src/build_vocabulary.py --check                 # exit 1 if the CSV is out of date
    python data-eda/src/build_vocabulary.py --count-ads FILE [FILE ...]
        ads per extract skill in those ad CSVs (column "description"), with the tier-1 matcher
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import extract, paths  # noqa: E402
from skillabus.normalise import BLOCKED_ESCO  # noqa: E402
from skillabus.text import read_csv_skipping_notes, slug  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("build_vocabulary")

SEED = paths.SKILLS_SEED
REVIEW = paths.ESCO_LINK_REVIEW
ESCO = paths.ESCO_SKILLS_CLEAN
OUT = paths.SKILLS_VOCABULARY

COLUMNS = ["skill_id", "label", "category", "source", "esco_uri", "esco_label", "esco_match",
           "reviewed_by", "aliases_ads", "strict", "used_for", "why_added"]
REVIEW_COLUMNS = ["canonical", "old_esco_uri", "old_esco_label", "esco_uri", "esco_label",
                  "esco_match", "note", "reviewed_by"]
MATCHES = ("exact", "close", "broad", "none")
_E = "http://data.europa.eu/esco/skill/"
# Links found wrong on 14 Oct 2026 (ESCO alt labels that share a word with a data skill). The concepts
# themselves are fine for other skills ("computer vision" is the exact link for Computer vision).
KNOWN_WRONG = {
    ("Transformers", _E + "f0ab5d57-4be7-411b-afce-b4a76a142302"),   # electrical machines
    ("TensorFlow", _E + "7b0d5000-00da-4864-b776-6de49a87a669"),     # computer vision
    ("Keras", _E + "7b0d5000-00da-4864-b776-6de49a87a669"),          # computer vision
}


def read_table(path: Path) -> pd.DataFrame:
    """A committed CSV as strings, empty cells as "" (never NaN), leading "# ..." notes skipped."""
    return read_csv_skipping_notes(path, dtype=str, keep_default_na=False)


def read_table_text(text: str) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def vocab_slug(label: str) -> str:
    """skillabus:<slug> part. Keeps + and # apart, so C++ and C# can never share an id."""
    return slug(label.replace("+", " plus ").replace("#", " sharp "))


def skill_id(label: str, esco_match: str, esco_uri: str) -> str:
    return f"esco:{esco_uri}" if esco_match == "exact" else f"skillabus:{vocab_slug(label)}"


def check_review(seed: pd.DataFrame, review: pd.DataFrame, esco: pd.DataFrame) -> list[str]:
    """Every problem in the review file, as readable lines (empty list = fine)."""
    errors = []
    if list(review.columns) != REVIEW_COLUMNS:
        return [f"columns must be {REVIEW_COLUMNS}, got {list(review.columns)}"]
    dupes = review.canonical[review.canonical.duplicated()].tolist()
    missing = sorted(set(seed.canonical) - set(review.canonical))
    extra = sorted(set(review.canonical) - set(seed.canonical))
    errors += [f"listed twice: {d}" for d in dupes]
    errors += [f"dictionary skill with no review row: {m}" for m in missing]
    errors += [f"review row for a skill not in the dictionary: {x}" for x in extra]
    label_of = dict(zip(esco.concept_uri, esco.preferred_label))
    for r in review.itertuples():
        where = f"{r.canonical}:"
        if r.esco_match not in MATCHES:
            errors.append(f"{where} esco_match {r.esco_match!r} is not one of {MATCHES}")
            continue
        if r.esco_match == "none":
            if r.esco_uri or r.esco_label:
                errors.append(f"{where} esco_match none but an ESCO link is filled in")
        elif not r.esco_uri:
            errors.append(f"{where} esco_match {r.esco_match} needs an esco_uri")
        elif r.esco_uri not in label_of:
            errors.append(f"{where} {r.esco_uri} is not in {ESCO.name}")
        elif label_of[r.esco_uri] != r.esco_label:
            errors.append(f"{where} esco_label {r.esco_label!r} but ESCO calls {r.esco_uri} "
                          f"{label_of[r.esco_uri]!r}")
        if r.esco_uri in BLOCKED_ESCO or (r.canonical, r.esco_uri) in KNOWN_WRONG:
            errors.append(f"{where} {r.esco_uri} ({r.esco_label}) is a known wrong link")
        if r.esco_match != "exact" and not r.note.strip():
            errors.append(f"{where} a {r.esco_match} link needs a note saying why it is not exact")
        if not r.reviewed_by.strip():
            errors.append(f"{where} reviewed_by is empty")
    return errors


def why_added(esco_match: str, esco_label: str, origin: str) -> str:
    if esco_match == "exact":
        return ""
    if esco_match == "none":
        return f"{origin}; not in ESCO"
    if esco_match == "broad":
        return f"{origin}; ESCO has only the wider '{esco_label}'"
    return f"{origin}; ESCO's nearest concept '{esco_label}' is not the same skill"


def part1(seed: pd.DataFrame, review: pd.DataFrame) -> list[dict]:
    """The dictionary skills, in dictionary order, with their reviewed ESCO links."""
    links = review.set_index("canonical")
    rows = []
    for s in seed.itertuples():
        r = links.loc[s.canonical]
        rows.append({
            "skill_id": skill_id(s.canonical, r.esco_match, r.esco_uri),
            "label": s.canonical,
            "category": s.category,
            "source": "esco" if r.esco_match == "exact" else "added",
            "esco_uri": r.esco_uri,
            "esco_label": r.esco_label,
            "esco_match": r.esco_match,
            "reviewed_by": r.reviewed_by,
            "aliases_ads": s.aliases,
            "strict": s.strict,
            "used_for": "extract",
            "why_added": why_added(r.esco_match, r.esco_label, "Dictionary skill"),
        })
    return rows


def build(seed_path: Path = SEED, review_path: Path = REVIEW, esco_path: Path = ESCO) -> pd.DataFrame:
    seed, review = read_table(seed_path), read_table(review_path)
    esco = pd.read_csv(esco_path, usecols=["concept_uri", "preferred_label"], dtype=str)
    errors = check_review(seed, review, esco)
    if errors:
        raise ValueError(f"{review_path.name} has {len(errors)} problem(s):\n  " + "\n  ".join(errors))
    vocab = pd.DataFrame(part1(seed, review), columns=COLUMNS)
    for col in ("skill_id", "label"):
        clash = vocab[col][vocab[col].duplicated()].tolist()
        if clash:
            raise ValueError(f"two rows share a {col}: {clash}")
    return vocab


def to_csv_text(vocab: pd.DataFrame) -> str:
    buf = io.StringIO()
    vocab.to_csv(buf, index=False, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    return buf.getvalue()


def summary(vocab: pd.DataFrame) -> str:
    counts = vocab.esco_match.value_counts()
    return (f"{len(vocab)} skills; esco_match " + ", ".join(f"{m} {counts.get(m, 0)}" for m in MATCHES)
            + f"; source esco {int((vocab.source == 'esco').sum())}, added {int((vocab.source == 'added').sum())}")


# ---------------------------------------------------------------- ad counts (for part 3)
def load_ads(files: list[Path], text_col: str = "description") -> pd.Series:
    """Ad texts from several CSVs, one per ad: de-duplicated on ad_id, then on the text itself."""
    frames = []
    for f in files:
        df = pd.read_csv(f, dtype=str, keep_default_na=False)
        ids = df["ad_id"] if "ad_id" in df else pd.Series(range(len(df))).astype(str).radd(f"{f.stem}:")
        frames.append(pd.DataFrame({"ad_id": ids, "text": df[text_col]}))
    ads = pd.concat(frames, ignore_index=True)
    ads = ads[ads.text.str.strip() != ""].drop_duplicates("ad_id").drop_duplicates("text")
    return ads.set_index("ad_id").text


def count_ads(skills: pd.DataFrame, texts) -> Counter:
    """Ads naming each skill (label -> n), with the tier-1 dictionary matcher of extract.py.

    `skills` needs label, category, aliases_ads, strict, like the vocabulary. The rows are written to
    a temporary file in the dictionary's format, so the counting uses exactly the matching rules of
    extract(): longest alias first, case-sensitive strict aliases, URLs and e-mails blanked out.
    """
    with tempfile.TemporaryDirectory() as tmp:
        seed = Path(tmp) / "candidates.csv"
        pd.DataFrame({"canonical": skills.label, "category": skills.category, "strict": skills.strict,
                      "aliases": skills.aliases_ads}).to_csv(seed, index=False, lineterminator="\n")
        counts = Counter()
        for text in texts:
            found = {c for sentence in extract.split_sentences(text)
                     for _, _, c in extract._dictionary_hits(sentence, str(seed))}
            counts.update(found)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=Path, default=SEED)
    parser.add_argument("--review", type=Path, default=REVIEW)
    parser.add_argument("--esco", type=Path, default=ESCO)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true", help="do not write; exit 1 if --out differs")
    parser.add_argument("--count-ads", type=Path, nargs="+", metavar="FILE",
                        help="print ads per extract skill in these ad CSVs, then stop")
    args = parser.parse_args()

    vocab = build(args.seed, args.review, args.esco)
    log.info(summary(vocab))

    if args.count_ads:
        texts = load_ads(args.count_ads)
        counts = count_ads(vocab[vocab.used_for.str.contains("extract")], texts)
        log.info("%d distinct ads in %d file(s)", len(texts), len(args.count_ads))
        for label in vocab.label:
            print(f"{counts.get(label, 0):6d}  {label}")
        return

    text = to_csv_text(vocab)
    if args.check:
        on_disk = read_table(args.out) if args.out.exists() else None
        if on_disk is None or not on_disk.equals(read_table_text(text)):
            log.error("%s is out of date: run python data-eda/src/build_vocabulary.py", args.out)
            sys.exit(1)
        log.info("%s is up to date", args.out)
        return
    args.out.write_text(text, encoding="utf-8", newline="")
    log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
