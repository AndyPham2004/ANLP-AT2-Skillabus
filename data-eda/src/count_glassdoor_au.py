"""Count skills in Australian Glassdoor data ads (2022): a second-platform check on Seek.

Source: Kaggle nadzmiagthomas/australia-data-science-jobs (CC BY-NC 4.0), two CSVs
of Glassdoor Australia listings. The listing URLs carry the scrape time, which runs
5 Aug - 18 Dec 2022, so this is the same era as the Seek corpus on a different job
board. That makes it a platform check, not a trend point: if Seek's skill ranking
were an artefact of how Seek ads are written, Glassdoor's would differ.

Same title filter as build_recent_sample.py, same 133-skill dictionary as the
September Seek counts (outputs/skill_counts_PRIMARY.csv), so the two are
comparable. Writes outputs/skill_counts_glassdoor_au_2022.csv in the same shape.

Usage (from data-eda/):
    python src/count_glassdoor_au.py
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from build_recent_sample import DATA_TITLE
from extract_skills import build_patterns, extract, summarise

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IN = ROOT / "data" / "raw" / "glassdoor_au_2022"
DEFAULT_SEED = ROOT / "config" / "skills_seed.csv"
DEFAULT_OUT = ROOT / "outputs" / "skill_counts_glassdoor_au_2022.csv"

log = logging.getLogger("glassdoor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_IN,
                        help="folder with AustraliaDataScienceJobs.csv and AustraliaDataScienceJob2.csv")
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("extract_skills").setLevel(logging.WARNING)

    files = sorted(args.input.glob("AustraliaDataScienceJob*.csv"))
    if not files:
        raise SystemExit(f"no Glassdoor CSVs in {args.input}; download the Kaggle dataset there")
    raw = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    ads = raw.drop_duplicates(subset=["Job Descriptions"]).reset_index(drop=True)
    data = ads[ads["Job Title"].fillna("").str.contains(DATA_TITLE)].reset_index(drop=True)
    data["ad_id"] = range(len(data))

    long = extract(data, "Job Descriptions", "ad_id", build_patterns(args.seed))
    counts = summarise(long, len(data))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(args.out, index=False)

    scraped = pd.to_datetime(ads.Url.astype(str).str.extract(r"[?&]cb=(\d{13})")[0]
                             .dropna().astype("int64"), unit="ms")
    log.info("rows %d -> %d unique ads -> %d data roles (scraped %s to %s)",
             len(raw), len(ads), len(data), f"{scraped.min():%d %b %Y}", f"{scraped.max():%d %b %Y}")
    log.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
