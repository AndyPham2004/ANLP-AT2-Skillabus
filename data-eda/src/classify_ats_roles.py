"""Give each 2026 job-board ad one of the 11 roles, or "other", from its title (plan D2 / D15, issue #116).

Input: the raw fetches of fetch_ats.py in data/raw/ (ats_ads_2026-10-13.csv, ats_ads_2026-10-16.csv, ...):
every Australian posting of the 65 public job boards, all professions. Output: the committed
data/2_demand/ads/ats_2026_clean.csv: the ads posted at most MAX_AGE_DAYS before their fetch (job boards keep
evergreen ads open for years; the same 60-day rule as build_recent_sample.py), one row per company and title
(the latest fetch wins, so a re-listing in a second city counts once), contact details masked as in
build_recent_sample.py, and a `role` column that build_role_skill_demand.py counts skills by (source = ats_2026,
period 2026-10).

The role comes from the title alone, so the rule is reviewable: RULES below is tried in order and the
first match wins. Management titles ("Engineering Manager - Data", "Head of Engineering") and pre-sales,
consulting or support engineers are "other". A title must name an individual-contributor noun (engineer,
developer, scientist, analyst, administrator, architect, tester); "engineering" alone never counts.
When the title says "Software Engineer" that wins over a qualifier ("Senior Software Engineer, AI Tooling"
is Software Engineer; "Senior Engineer - ML Systems" is Machine Learning Engineer).

Usage (from the repo root):
    python data-eda/src/classify_ats_roles.py                         # write data/2_demand/ads/ats_2026_clean.csv
    python data-eda/src/classify_ats_roles.py --titles                # every distinct title with its role, by role
    python data-eda/src/classify_ats_roles.py --sample 30 --seed 1    # random ads with the text head, for the hand check
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import pandas as pd

from build_recent_sample import posted_date, snapshot_date, tidy

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("classify_ats_roles")

RAW_GLOB = "ats_ads_2026-10-*.csv"           # the October fetches (the September file holds data roles only)
OUT = paths.ATS_2026_ADS
MIN_TEXT = 200                               # an ad with less text than this is a stub, not an ad
MAX_AGE_DAYS = 60                            # posted at most this long before the fetch (build_recent_sample's rule)
COLUMNS = ["ad_id", "source", "company", "title", "role", "location", "posted", "snapshot", "description", "url"]
from skillabus.roles import ENG, OTHER, RULES, role_of  # noqa: E402,F401  the title rules (moved 17 Oct)


def read_raw(files: list[Path]) -> pd.DataFrame:
    """The fetches as one table: ads posted within MAX_AGE_DAYS of their fetch (an unknown date is kept, as in
    build_recent_sample.py), one row per ad_id and then per company + title, the latest fetch first."""
    parts = []
    for path in sorted(files):
        a = pd.read_csv(path, dtype=str, keep_default_na=False)
        created = a.created.map(posted_date)
        snap = snapshot_date(path, created)
        parts.append(pd.DataFrame({
            "ad_id": "ats-" + a.ad_id.astype(str), "source": a.source, "company": a.company.str.strip(),
            "title": a.title.map(lambda s: re.sub(r"\s+", " ", s or "").strip()), "location": a.location,
            "posted": created.dt.strftime("%Y-%m-%d").fillna(""), "snapshot": snap.strftime("%Y-%m-%d"),
            "description": a.description.map(tidy), "url": a.redirect_url,
        }))
        log.info("%s: %d ads, fetched %s", path.name, len(a), snap.date())
    ads = pd.concat(parts, ignore_index=True)
    before = len(ads)
    age = (pd.to_datetime(ads.snapshot) - pd.to_datetime(ads.posted.replace("", pd.NA))).dt.days
    fresh = age.isna() | (age <= MAX_AGE_DAYS)
    stale = int((~fresh).sum())
    ads = ads[fresh & (ads.description.str.len() >= MIN_TEXT)]
    # The latest fetch first, ad_id breaking ties, so the row kept never depends on input order.
    ads = ads.sort_values(["snapshot", "posted", "ad_id"], ascending=False, kind="stable")
    ads = ads.drop_duplicates("ad_id").drop_duplicates(["company", "title"]).reset_index(drop=True)
    log.info("%d rows -> %d ads: %d posted more than %d days before their fetch dropped, the rest duplicates or stubs",
             before, len(ads), stale, MAX_AGE_DAYS)
    return ads


def classify(ads: pd.DataFrame) -> pd.DataFrame:
    out = ads.copy()
    out["role"] = out.title.map(role_of)
    return out[COLUMNS].sort_values(["role", "company", "title", "ad_id"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw", type=Path, default=paths.RAW, help="folder with the ats_ads_2026-10-*.csv fetches")
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--titles", action="store_true", help="print every distinct title with its role and stop")
    parser.add_argument("--sample", type=int, default=0, help="print this many random ads for the hand check and stop")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)

    files = sorted(args.raw.glob(RAW_GLOB))
    if not files:
        sys.exit(f"no {RAW_GLOB} in {args.raw}; run data-eda/src/fetch_ats.py --australia-only first")
    table = classify(read_raw(files))
    counts = table.role.value_counts()
    log.info("ads per role:\n%s", counts.to_string())

    if args.titles:
        for role, group in table.groupby("role"):
            print(f"\n## {role} ({len(group)} ads)")
            for title, n in group.title.value_counts().sort_index().items():
                print(f"  {n:2d}  {title}")
        return
    if args.sample:
        for row in table.sample(args.sample, random_state=args.seed).itertuples():
            head = re.sub(r"\s+", " ", row.description)[:300]
            print(f"\n[{row.ad_id}] {row.role} | {row.title} | {row.company}\n    {head}")
        return
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False, encoding="utf-8", lineterminator="\n")
    log.info("wrote %s: %d ads, %d with one of the 11 roles", args.out, len(table), int((table.role != OTHER).sum()))


if __name__ == "__main__":
    main()
