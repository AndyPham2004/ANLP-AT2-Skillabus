"""Count every dictionary skill in 2019-22, January 2024 and 2026, with the same method.

Writes data/processed/skill_counts_2026.csv, the file match.py reads for
`demand_pct_2026` (data contract section 2). One row per skill in
skills_seed_v2.csv:

  skill, category
  pct_2019_22      share of the 3,204 Seek Data Scientist ads (clean text)
  pct_2024_01      share of the 124 Australian LinkedIn data roles, January 2024
  n_2026           how many of the 2026 full-text roles name the skill
  pct_2026         n_2026 as a share; what match.py reads
  pct_2026_low,    95% Wilson interval on pct_2026. With 22 ads the interval is
  pct_2026_high    wide, and the app should show it or show "n of 22" instead
  total_*          the denominators, repeated on every row

All three periods go through the same extractor, the same dictionary and cleaned
text, so differences between columns are about the ads, not the method. Two
things that are NOT controlled, and must be said wherever these numbers appear:

  * the role mix differs - Seek is Data Scientist titles only; January 2024 is
    mostly data engineers and analysts; 2026 is tech employers, AI-titled roles
    included
  * pct_2019_22 here is on the cleaned Seek text, so it can sit up to ~2 points
    above skill_counts_v2.csv, which was counted on the raw text in September

Adzuna rows (description cut at 500 characters) are excluded from every share.

Usage (from data-eda/):
    python src/recount_recent.py
"""

from __future__ import annotations

import argparse
import logging
import math
from pathlib import Path

import pandas as pd

from extract_skills import build_patterns, extract

ROOT = Path(__file__).resolve().parents[1]          # data-eda/
REPO = ROOT.parent
DEFAULT_SEEK = ROOT / "data" / "clean" / "jobs_au_seek_datascientist_2019-2022_clean.csv"
DEFAULT_RECENT = ROOT / "data" / "clean" / "jobs_au_recent_2024-2026_clean.csv"
DEFAULT_SEED = REPO / "data" / "processed" / "skills_seed_v2.csv"
DEFAULT_OUT = REPO / "data" / "processed" / "skill_counts_2026.csv"

LLM_ERA = ["Large language models", "Generative AI", "Prompt engineering", "RAG",
           "LangChain", "Vector databases", "Hugging Face", "Transformers"]

log = logging.getLogger("recount")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n, as percentages."""
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(100 * max(0.0, centre - half), 1), round(100 * min(1.0, centre + half), 1)


def counts(df: pd.DataFrame, id_col: str, patterns) -> pd.Series:
    """Number of ads naming each skill."""
    long = extract(df, "description", id_col, patterns)
    key = [c for c in long.columns if c not in ("skill", "category")][0]
    return long.groupby("skill")[key].nunique()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seek", type=Path, default=DEFAULT_SEEK)
    parser.add_argument("--recent", type=Path, default=DEFAULT_RECENT)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("extract_skills").setLevel(logging.WARNING)

    patterns = build_patterns(args.seed)
    seed = pd.read_csv(args.seed, skiprows=1) if open(args.seed, encoding="utf-8").readline().startswith("#") \
        else pd.read_csv(args.seed)

    seek = pd.read_csv(args.seek)
    recent = pd.read_csv(args.recent)
    recent = recent[recent.full_text]
    jan24 = recent[recent.period == "2024-01"]
    y26 = recent[recent.period == "2026-09"]

    n_seek, n_24, n_26 = len(seek), len(jan24), len(y26)
    c_seek = counts(seek, "ad_id", patterns)
    c_24 = counts(jan24, "ad_id", patterns)
    c_26 = counts(y26, "ad_id", patterns)

    out = seed[["canonical", "category"]].rename(columns={"canonical": "skill"}).copy()
    out["pct_2019_22"] = (100 * out.skill.map(c_seek).fillna(0) / n_seek).round(1)
    out["pct_2024_01"] = (100 * out.skill.map(c_24).fillna(0) / n_24).round(1)
    out["n_2026"] = out.skill.map(c_26).fillna(0).astype(int)
    out["pct_2026"] = (100 * out.n_2026 / n_26).round(1)
    ci = out.n_2026.apply(lambda k: wilson(k, n_26))
    out["pct_2026_low"] = [lo for lo, _ in ci]
    out["pct_2026_high"] = [hi for _, hi in ci]
    out["total_2019_22"], out["total_2024_01"], out["total_2026"] = n_seek, n_24, n_26
    out = out.sort_values(["pct_2019_22", "skill"], ascending=[False, True]).reset_index(drop=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")

    log.info("Wrote %s: %d skills | n = %d (2019-22), %d (Jan 2024), %d (2026)",
             args.out.name, len(out), n_seek, n_24, n_26)
    show = ["skill", "pct_2019_22", "pct_2024_01", "n_2026", "pct_2026", "pct_2026_low", "pct_2026_high"]
    tech = out[out.category != "Professional"]
    log.info("\nTop 12 technical skills, 2019-22:\n%s", tech.head(12)[show].to_string(index=False))
    log.info("\nLLM-era skills:\n%s",
             out[out.skill.isin(LLM_ERA)].sort_values("n_2026", ascending=False)[show].to_string(index=False))

    def any_of(frame, c):
        long = extract(frame, "description", "ad_id", patterns)
        return long[long.skill.isin(LLM_ERA)].ad_id.nunique()
    k26, k24, kseek = any_of(y26, None), any_of(jan24, None), any_of(seek, None)
    lo, hi = wilson(k26, n_26)
    log.info("\nAny LLM-era skill: %.1f%% (2019-22) -> %.1f%% (Jan 2024) -> %d of %d = %.0f%% "
             "(2026; 95%% interval %.0f-%.0f%%)",
             100 * kseek / n_seek, 100 * k24 / n_24, k26, n_26, 100 * k26 / n_26, lo, hi)


if __name__ == "__main__":
    main()
