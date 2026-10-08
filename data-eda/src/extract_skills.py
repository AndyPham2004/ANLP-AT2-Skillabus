"""Dictionary-based skill extraction from job advertisement text.

Reads a CSV of job ads, matches every alias in config/skills_seed.csv against the
ad text, and writes two outputs:

  outputs/skill_counts.csv   one row per skill: how many ads mention it (feeds poster block 5)
  outputs/ad_skill_long.csv  one row per (ad, skill) pair (feeds C's matching step)

This is the "traditional" arm of the traditional-vs-neural comparison the brief
rewards. It is deliberately simple and fully inspectable: every match traces back
to a literal string in the seed dictionary.

Usage:
    python src/extract_skills.py --input data/raw/postings.csv --text-col description
"""

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED = ROOT / "config" / "skills_seed.csv"
DEFAULT_OUT = ROOT / "outputs"

# Characters that may not sit directly beside a match. Unlike \b this tolerates
# aliases ending in punctuation, so "c++" and "c#" match but "c++x" does not.
BOUNDARY_CHARS = r"A-Za-z0-9+#_"
LEFT = rf"(?<![{BOUNDARY_CHARS}])"
RIGHT = rf"(?![{BOUNDARY_CHARS}])"

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("extract_skills")


def build_patterns(seed_path):
    """Compile one regex per skill from its pipe-separated literal aliases."""
    seed = pd.read_csv(seed_path)
    required = {"canonical", "category", "strict", "aliases"}
    missing = required - set(seed.columns)
    if missing:
        raise ValueError(f"{seed_path} is missing columns: {sorted(missing)}")

    patterns = []
    for row in seed.itertuples(index=False):
        aliases = [a.strip() for a in str(row.aliases).split("|") if a.strip()]
        if not aliases:
            log.warning("skill %r has no aliases, skipping", row.canonical)
            continue
        # Longest first so "sql server" wins over "sql" inside the same alternation.
        aliases.sort(key=len, reverse=True)
        body = "|".join(re.escape(a) for a in aliases)
        flags = 0 if int(row.strict) == 1 else re.IGNORECASE
        patterns.append(
            (row.canonical, row.category, re.compile(LEFT + f"(?:{body})" + RIGHT, flags))
        )
    log.info("compiled %d skill patterns from %s", len(patterns), seed_path.name)
    return patterns


def extract(df, text_col, id_col, patterns):
    """Return a long (ad_id, skill, category) frame of every skill found per ad."""
    texts = df[text_col].fillna("").astype(str)
    ids = df[id_col]

    rows = []
    for ad_id, text in zip(ids, texts):
        if not text:
            continue
        for canonical, category, pattern in patterns:
            if pattern.search(text):
                rows.append((ad_id, canonical, category))

    long = pd.DataFrame(rows, columns=["ad_id", "skill", "category"])
    log.info("found %d (ad, skill) pairs across %d ads", len(long), len(df))
    return long


def summarise(long, n_ads):
    """Collapse the long frame to per-skill counts and share of ads."""
    counts = (
        long.groupby(["skill", "category"], as_index=False)
        .agg(n_ads=("ad_id", "nunique"))
        .sort_values("n_ads", ascending=False)
        .reset_index(drop=True)
    )
    counts["pct_ads"] = (counts["n_ads"] / n_ads * 100).round(1)
    counts["total_ads_in_sample"] = n_ads
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="CSV of job ads")
    parser.add_argument("--text-col", default="description", help="column holding the ad text")
    parser.add_argument("--id-col", default=None, help="unique ad id column (default: row number)")
    parser.add_argument("--seed", default=DEFAULT_SEED, type=Path)
    parser.add_argument("--out-dir", default=DEFAULT_OUT, type=Path)
    parser.add_argument("--sample", type=int, default=None, help="use only the first N ads")
    parser.add_argument(
        "--filter-col", default=None, help="optional column to filter on, e.g. location"
    )
    parser.add_argument(
        "--filter-contains", default=None, help="keep rows where filter-col contains this string"
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, low_memory=False)
    log.info("loaded %s rows from %s", f"{len(df):,}", args.input)

    if args.filter_col and args.filter_contains:
        before = len(df)
        mask = df[args.filter_col].fillna("").astype(str).str.contains(
            args.filter_contains, case=False, regex=False
        )
        df = df[mask]
        log.info(
            "filtered %s -> %s rows where %s contains %r",
            f"{before:,}", f"{len(df):,}", args.filter_col, args.filter_contains,
        )

    if args.sample:
        df = df.head(args.sample)
        log.info("sampled first %s rows", f"{len(df):,}")

    if df.empty:
        raise SystemExit("No rows left after filtering - check --filter-contains.")
    if args.text_col not in df.columns:
        raise SystemExit(
            f"--text-col {args.text_col!r} not found. Columns are: {list(df.columns)[:25]}"
        )

    id_col = args.id_col
    if id_col is None:
        df = df.reset_index(drop=True)
        df["_row_id"] = df.index
        id_col = "_row_id"

    patterns = build_patterns(args.seed)
    long = extract(df, args.text_col, id_col, patterns)
    counts = summarise(long, n_ads=len(df))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    long.to_csv(args.out_dir / "ad_skill_long.csv", index=False)
    counts.to_csv(args.out_dir / "skill_counts.csv", index=False)
    log.info("wrote %s and %s", "ad_skill_long.csv", "skill_counts.csv")

    print(f"\nSample size: {len(df):,} ads\nTop 15 skills by share of ads:\n")
    print(counts.head(15).to_string(index=False))
    print(
        "\nSanity-check these before they go on the poster. Any skill above ~85% or "
        "a 'Professional' skill in the top 3 usually means an alias is over-matching."
    )


if __name__ == "__main__":
    main()
