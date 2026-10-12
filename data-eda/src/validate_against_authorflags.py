"""Compare our dictionary extraction against the dataset author's own tool flags.

The Kaggle Seek dataset ships a second file with 25 binary tool columns the
author extracted independently - someone else's labels, on the same ads, at no
labelling cost. All 3,204 ads in our primary corpus join to it on
`ad_id == jobId`.

This is **not** an accuracy test: the author's flags are not ground truth, and
the headline result is that they are far more permissive than ours (their R
fires on 64% of ads, ours on 12%). Treating them as truth would score our
extractor badly for being correct. So what this script reports is:

  * agreement, and Cohen's kappa, per tool
  * which direction each disagreement runs
  * sampled ad sentences from the disagreeing ads, so the cause is visible

The output is the error analysis for the report: it shows what a boundary-less
substring matcher does to a skill count, which is the argument for our
`(?<![A-Za-z0-9+#_])` boundaries.

Usage:
    python src/validate_against_authorflags.py
    python src/validate_against_authorflags.py --examples 5
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADS = ROOT / "data" / "raw" / "jobs_au_seek_datascientist_2019-2022.csv"
DEFAULT_FLAGS = ROOT / "data" / "raw" / "jobs_au_seek_datascience_2019-2022_authorflags.csv"
DEFAULT_LONG = ROOT / "outputs" / "ad_skill_long.csv"
DEFAULT_OUT = ROOT / "outputs" / "extractor_agreement.csv"

# Their flag column -> our canonical skill. Only tools both extractors cover.
PAIRS = {
    "Python": "Python",
    "SQL": "SQL",
    "R": "R",
    "SAS": "SAS",
    "Tableau": "Tableau",
    "Spark": "Spark",
    "Hadoop": "Hadoop",
    "Scala": "Scala",
    "Java": "Java",
    "Julia": "Julia",
    "Matlab": "MATLAB",
    "Javascript": "JavaScript",
    "Golang": "Go",
    "D3": "D3.js",
}

log = logging.getLogger("agreement")


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    """Cohen's kappa for two binary labellings of the same items."""
    n = len(a)
    observed = (a == b).mean()
    pa, pb = a.mean(), b.mean()
    expected = pa * pb + (1 - pa) * (1 - pb)
    if expected == 1.0:
        return float("nan")
    return (observed - expected) / (1 - expected)


def load(ads_path: Path, flags_path: Path, long_path: Path):
    ads = pd.read_csv(ads_path, usecols=["ad_id", "description"])
    flags = pd.read_csv(flags_path)
    long = pd.read_csv(long_path)

    missing = [c for c in PAIRS if c not in flags.columns]
    if missing:
        raise SystemExit(f"{flags_path.name} has no columns {missing}")

    flags = flags.rename(columns={"jobId": "ad_id"})
    joined = ads.merge(flags[["ad_id", *PAIRS]], on="ad_id", how="inner")
    log.info("joined %d of %d ads to the author's flags", len(joined), len(ads))
    if len(joined) < len(ads):
        log.warning("%d ads had no flag row and are excluded", len(ads) - len(joined))

    ours = {
        skill: set(g.ad_id)
        for skill, g in long[long.skill.isin(PAIRS.values())].groupby("skill")
    }
    return joined, ours


def compare(joined: pd.DataFrame, ours: dict[str, set]) -> pd.DataFrame:
    rows = []
    for their_col, our_skill in PAIRS.items():
        theirs = joined[their_col].to_numpy().astype(bool)
        mine = joined.ad_id.isin(ours.get(our_skill, set())).to_numpy()
        both = int((theirs & mine).sum())
        rows.append({
            "skill": our_skill,
            "their_col": their_col,
            "ours_pct": round(100 * mine.mean(), 1),
            "theirs_pct": round(100 * theirs.mean(), 1),
            "both": both,
            "ours_only": int((mine & ~theirs).sum()),
            "theirs_only": int((theirs & ~mine).sum()),
            "neither": int((~mine & ~theirs).sum()),
            "agreement_pct": round(100 * (mine == theirs).mean(), 1),
            "kappa": round(kappa(mine.astype(int), theirs.astype(int)), 3),
            "jaccard": round(both / max(1, int((theirs | mine).sum())), 3),
        })
    return pd.DataFrame(rows).sort_values("kappa", ascending=False).reset_index(drop=True)


# Single letters and very short acronyms cannot be decomposed: a regex for "R"
# followed by a letter also matches "Role", "Reporting" and every other
# capitalised R-word, so the glue test is meaningless for them.
UNDECOMPOSABLE = {"R", "C", "Go", "D3.js"}


def decompose(joined: pd.DataFrame, ours: dict[str, set]) -> pd.DataFrame:
    """Split each 'they flagged it, we did not' set into two causes.

    glued   the term is in the ad but welded to the next word, because the
            source dataset stripped HTML tags without putting whitespace back
            ("...Power BI and TableauSuperior analytical skills..."). Our word
            boundaries correctly refuse this, so it is a real miss on our side.
    absent  the term does not appear in the ad text at all, so their flag
            cannot be justified from the description we have.
    """
    rows = []
    for their_col, our_skill in PAIRS.items():
        if our_skill in UNDECOMPOSABLE:
            continue
        mine = joined.ad_id.isin(ours.get(our_skill, set()))
        sub = joined[(joined[their_col] == 1) & ~mine]
        if sub.empty:
            continue
        text = sub.description.fillna("")
        term = re.escape(their_col)
        cased = their_col.isupper()  # SAS, SQL: case-sensitive or they match any 'sas'
        glued = text.str.contains(
            rf"(?<![A-Za-z]){term}(?=[A-Z])|(?<=[a-z]){term}(?![A-Za-z])",
            regex=True, case=cased)
        present = text.str.contains(term, regex=True, case=cased)
        rows.append({
            "skill": our_skill,
            "theirs_only": len(sub),
            "glued_our_miss": int(glued.sum()),
            "absent_their_fp": int((~present).sum()),
            "other": int((present & ~glued).sum()),
        })
    return pd.DataFrame(rows).sort_values("glued_our_miss", ascending=False).reset_index(drop=True)


def show_disagreements(joined: pd.DataFrame, ours: dict[str, set], n: int) -> None:
    """Print ad snippets where only the author's extractor fired.

    These are where the cause of a disagreement shows up: a bare "R" inside
    "R&D", a "SAS" inside "SaaS". Each snippet is the first window around the
    tool's own letters, so the surrounding word is visible.
    """
    for their_col, our_skill in PAIRS.items():
        mine = joined.ad_id.isin(ours.get(our_skill, set()))
        theirs = joined[their_col].astype(bool)
        only_theirs = joined[theirs & ~mine]
        if only_theirs.empty:
            continue
        log.info("")
        log.info("--- %s: %d ads flagged by them, not by us", our_skill, len(only_theirs))
        needle = re.compile(re.escape(their_col.rstrip(".")), re.I)
        shown = 0
        for text in only_theirs.description.dropna():
            m = needle.search(str(text))
            if not m:
                continue
            start, end = max(0, m.start() - 45), m.end() + 35
            snippet = re.sub(r"\s+", " ", str(text)[start:end]).strip()
            log.info('    "...%s..."', snippet)
            shown += 1
            if shown >= n:
                break
        if not shown:
            log.info("    (their flag fired on ads whose text never contains the term)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ads", type=Path, default=DEFAULT_ADS)
    parser.add_argument("--flags", type=Path, default=DEFAULT_FLAGS)
    parser.add_argument("--long", type=Path, default=DEFAULT_LONG,
                        help="our extraction, from extract_skills.py")
    parser.add_argument("--examples", type=int, default=3,
                        help="disagreement snippets to print per tool")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    for path in (args.ads, args.flags, args.long):
        if not path.exists():
            raise SystemExit(f"{path} not found. Run src/extract_skills.py first for --long.")

    joined, ours = load(args.ads, args.flags, args.long)
    table = compare(joined, ours)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    log.info("")
    log.info("%s", table[["skill", "ours_pct", "theirs_pct", "agreement_pct",
                          "kappa", "ours_only", "theirs_only"]].to_string(index=False))
    log.info("")
    log.info("median kappa %.3f over %d tools, n = %d ads",
             table.kappa.median(), len(table), len(joined))
    strong = table[table.kappa >= 0.6]
    log.info("%d of %d tools at kappa >= 0.60 (substantial agreement)", len(strong), len(table))
    log.info("Wrote %s", args.out)

    glue = joined.description.fillna("").str.contains(r"[a-z][A-Z]", regex=True)
    log.info("")
    log.info("Source-text damage: %d of %d ads (%.1f%%) contain at least one",
             int(glue.sum()), len(joined), 100 * glue.mean())
    log.info("lower->Upper join, i.e. HTML stripped without replacing the tag.")
    log.info("")
    parts = decompose(joined, ours)
    log.info("%s", parts.to_string(index=False))
    log.info("")
    log.info("Our under-count from glued text: %d ad-skill mentions across %d tools.",
             int(parts.glued_our_miss.sum()), len(parts))
    log.info("Their flags are unusable as a reference: %d of %d of their extra",
             int(parts.absent_their_fp.sum()), int(parts.theirs_only.sum()))
    log.info("positives have no occurrence of the term in the ad text at all.")
    parts_out = args.out.with_name(args.out.stem + "_decomposed.csv")
    parts.to_csv(parts_out, index=False)
    log.info("Wrote %s", parts_out)

    if args.examples:
        show_disagreements(joined, ours, args.examples)


if __name__ == "__main__":
    main()
