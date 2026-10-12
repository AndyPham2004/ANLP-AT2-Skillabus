"""Build the recent Australian data-role sample: 2026 job boards plus LinkedIn January 2024.

Team plan task 2 asked for about 150 Australian data roles from 2026. What can be
collected legitimately falls well short of that, so this file is honest about it:

  source            period    full text   how it was collected
  greenhouse/lever/ 2026-09   yes         public job-board APIs (src/fetch_ats.py)
  smartrecruiters
  adzuna            2026-09   NO          Adzuna API; every description is cut at
                                          500 characters, so these count as roles
                                          but must not be used for skill shares
  linkedin          2024-01   yes         Kaggle asaniczka/data-science-job-postings-
                                          and-skills (ODC-By), Australian rows only

Indeed was in the plan and is not here: its terms forbid scraping, as Seek's and
LinkedIn's do, and it has no public job-search API.

The LinkedIn 2024 rows are a separate period, not padding for 2026. They give the
2019-22 -> 2026 trend an Australian middle point, so the step to 2026 no longer
changes country and year at the same time.

Every source goes through the same title filter and de-duplication. Skill shares
for the report come from task 5 (skill_counts_2026.csv), computed on
`full_text == True` rows only, per period.

Usage (from data-eda/):
    python src/build_recent_sample.py
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DEFAULT_ATS = RAW / "jobs_au_ats_2026.csv"
DEFAULT_ADZUNA = RAW / "jobs_au_adzuna_2026.csv"
DEFAULT_LINKEDIN = RAW / "linkedin_datascience_2024"
DEFAULT_OUT = ROOT / "data" / "clean" / "jobs_au_recent_2024-2026_clean.csv"

# One filter for every source, so the periods are comparable.
DATA_TITLE = re.compile(
    r"data scien|data analy|machine learning|\bML engineer|data engineer|analytics|\bAI\b|"
    r"research scien|statistic|quantitative|business intelligence|\bBI\b", re.I)

COLUMNS = ["ad_id", "source", "period", "title", "company", "location", "posted",
           "full_text", "description", "url"]

log = logging.getLogger("recent_sample")


def tidy(text) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def from_ats(path: Path) -> pd.DataFrame:
    a = pd.read_csv(path)
    return pd.DataFrame({
        "ad_id": "ats-" + a.ad_id.astype(str),
        "source": a.source,                      # greenhouse / lever / smartrecruiters
        "period": "2026-09",
        "title": a.title, "company": a.company, "location": a.location,
        "posted": a.created, "full_text": True,
        "description": a.description.map(tidy), "url": a.redirect_url,
    })


def from_adzuna(path: Path) -> pd.DataFrame:
    z = pd.read_csv(path)
    return pd.DataFrame({
        "ad_id": "adzuna-" + z.ad_id.astype(str),
        "source": "adzuna", "period": "2026-09",
        "title": z.title, "company": z.company, "location": z.location,
        "posted": z.created, "full_text": False,   # API caps text at 500 characters
        "description": z.description.map(tidy), "url": z.redirect_url,
    })


def from_linkedin(folder: Path) -> pd.DataFrame:
    p = pd.read_csv(folder / "job_postings.csv")
    s = pd.read_csv(folder / "job_summary.csv")
    au = p[p.search_country == "Australia"].merge(s, on="job_link", how="inner")
    job_id = au.job_link.str.extract(r"(\d{6,})/?$")[0].fillna(au.index.to_series().astype(str))
    return pd.DataFrame({
        "ad_id": "li24-" + job_id,
        "source": "linkedin", "period": "2024-01",
        "title": au.job_title, "company": au.company, "location": au.job_location,
        "posted": au.first_seen, "full_text": True,
        "description": au.job_summary.map(tidy), "url": au.job_link,
    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ats", type=Path, default=DEFAULT_ATS)
    parser.add_argument("--adzuna", type=Path, default=DEFAULT_ADZUNA)
    parser.add_argument("--linkedin", type=Path, default=DEFAULT_LINKEDIN,
                        help="folder with job_postings.csv and job_summary.csv")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    for path in (args.ats, args.adzuna, args.linkedin):
        if not path.exists():
            raise SystemExit(f"{path} not found - see data/README.md for where each source comes from")

    frames = {"job boards": from_ats(args.ats), "adzuna": from_adzuna(args.adzuna),
              "linkedin": from_linkedin(args.linkedin)}
    log.info("%-12s %6s %6s %8s", "source", "rows", "data", "deduped")
    kept = []
    for name, f in frames.items():
        data = f[f.title.fillna("").str.contains(DATA_TITLE)]
        dedup = (data.drop_duplicates(subset=["description"])
                     .drop_duplicates(subset=["title", "company", "period"]))
        log.info("%-12s %6d %6d %8d", name, len(f), len(data), len(dedup))
        kept.append(dedup)

    # Full text wins when the same 2026 role appears on a job board and on Adzuna.
    out = (pd.concat(kept, ignore_index=True)
             .sort_values("full_text", ascending=False)
             .drop_duplicates(subset=["title", "company", "period"])
             .sort_values(["period", "source", "company", "title"])
             .reset_index(drop=True))[COLUMNS]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")

    log.info("")
    log.info("Wrote %s: %d Australian data roles", args.out.name, len(out))
    summary = out.groupby(["period", "full_text"]).size().unstack(fill_value=0)
    log.info("%s", summary.rename(columns={True: "full text", False: "500-char only"}).to_string())
    n26 = int(((out.period == "2026-09") & out.full_text).sum())
    log.info("")
    log.info("2026 roles with full text: %d (team plan target was ~150).", n26)


if __name__ == "__main__":
    main()
