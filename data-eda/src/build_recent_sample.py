"""Build the recent Australian data-role sample: 2026 job boards plus LinkedIn January 2024.

Team plan task 2 asked for about 150 Australian data roles from 2026. What can be
collected legitimately falls well short of that, so this file is honest about it:

  source            period    full text   how it was collected
  greenhouse/lever/ 2026-09,  yes         public job-board APIs (src/fetch_ats.py), one
  smartrecruiters/  2026-10               snapshot per run (Sept, then daily 14-16 Oct)
  ashby/workable
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

Every source goes through the same title filter and de-duplication. On the 2026
job-board rows (issue #64) three more rules apply before a row counts:

  * age      posted at most --max-age-days (60) before the snapshot was taken;
             job boards keep evergreen roles open for years (one Greenhouse ad
             dates from 2021). Rows with no date are kept.
  * group    `role_group` = "data scientist" for data/applied/ML/AI/research
             scientist titles, the only titles the 2019-22 Seek file has, so this
             group is the like-for-like comparison; "data role" for the rest of
             DATA_TITLE (engineers, analysts, ML engineers)
  * cap      at most --cap (3) rows per company and group, the most recent first,
             so one employer (Canva had 12 of 22 in September) cannot set the shares;
             ads posted on the same day are ordered by ad_id, so reruns keep the same rows

`in_sample` marks the rows that pass all three; recount_recent.py counts those.
The same role seen in several snapshots is kept once, from the latest snapshot; a role
re-posted under a new id is kept once, from the newest posting.

Usage (from data-eda/):
    python src/build_recent_sample.py                       # Sept file + every ats_ads_2026-*.csv
    python src/build_recent_sample.py --ats data/raw/jobs_au_ats_2026.csv data/raw/ats_ads_2026-10-14.csv
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEPT_ATS = RAW / "jobs_au_ats_2026.csv"
DEFAULT_ADZUNA = RAW / "jobs_au_adzuna_2026.csv"
DEFAULT_LINKEDIN = RAW / "linkedin_datascience_2024"
DEFAULT_OUT = ROOT / "data" / "clean" / "jobs_au_recent_2024-2026_clean.csv"

# One filter for every source, so the periods are comparable. No bare "AI": it let
# "Senior Graphic AI Designer" and "AI Video Lead" in (#64).
DATA_TITLE = re.compile(
    r"data scien|data analy|machine learning|\bML engineer|data engineer|analytics|"
    r"\bAI (?:engineer|scientist|researcher|specialist)|applied scien|research scien|"
    r"statistic|quantitative|business intelligence|\bBI\b", re.I)
# Sales and account roles that sell analytics ("Business Development Manager - FMCG Analytics").
NOT_DATA = re.compile(r"\bsales\b|business development|account (?:executive|manager)", re.I)
# The like-for-like group: the 2019-22 Seek file holds Data Scientist titles only.
DS_TITLE = re.compile(r"\b(?:data|applied|decision|research|machine learning|ML|AI) scientists?\b", re.I)

COLUMNS = ["ad_id", "source", "period", "title", "company", "location", "posted",
           "full_text", "description", "url", "snapshot", "age_days", "role_group", "in_sample"]

log = logging.getLogger("recent_sample")


# Recruiters' names sit in their addresses (firstname.lastname@agency) and mobiles are personal,
# so contact details are masked before the file is committed (#53). Skills never sit in them.
# Recruiters' names next to a number ("contact Raj Singh on [PHONE]") stay: ads are published
# for people to contact them, and the team decided on #53 to leave ad text as written.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(
    r"(?<![\d+])(?:"
    r"(?:\+?61[\s-]?|0)4(?:[\s-]?\d){8}"                               # mobile, any grouping: 0404 380 704, 0432 08 5020
    r"|(?:\+?61[\s-]?\(?0?|\(0|0)[2378]\)?[\s-]?\d{4}[\s-]?\d{4}"     # landline: (08) 6551 9419, +61 2 9005 5000
    r"|\+61[\s-]?\d{4}[\s-]?\d{4}"                                     # +61 without the area digit: +61 9236 7780
    r"|1[38]00[\s-]?\d{3}[\s-]?\d{3}"                                  # 1300 / 1800
    r")(?!\d)")


def mask_contacts(text: str) -> str:
    return PHONE.sub("[PHONE]", EMAIL.sub("[EMAIL]", text))


def tidy(text) -> str:
    if not isinstance(text, str):
        return ""
    text = mask_contacts(text)
    text = text.replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def posted_date(value) -> pd.Timestamp:
    """Job-board dates as UTC timestamps: Lever sends epoch milliseconds, the others ISO 8601."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or str(value).strip() == "":
        return pd.NaT
    s = str(value).strip()
    if re.fullmatch(r"\d{12,14}(?:\.0)?", s):
        return pd.to_datetime(int(float(s)), unit="ms", utc=True)
    return pd.to_datetime(s, utc=True, errors="coerce")


def snapshot_date(path: Path, created: pd.Series) -> pd.Timestamp:
    """The day a job-board file was fetched: from its name (ats_ads_2026-10-14.csv), else the
    newest posting date in it (the September file)."""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    if m:
        return pd.Timestamp(m.group(1), tz="UTC")
    return created.max().normalize()


def role_group(title: str) -> str:
    return "data scientist" if DS_TITLE.search(title or "") else "data role"


def from_ats(path: Path) -> pd.DataFrame:
    a = pd.read_csv(path, dtype=str, keep_default_na=False)
    created = a.created.map(posted_date)
    snap = snapshot_date(path, created)
    return pd.DataFrame({
        "ad_id": "ats-" + a.ad_id.astype(str),
        "source": a.source,                      # greenhouse / lever / smartrecruiters / ashby / workable
        "period": snap.strftime("%Y-%m"),
        "title": a.title, "company": a.company, "location": a.location,
        "posted": created.dt.strftime("%Y-%m-%d"), "full_text": True,
        "description": a.description.map(tidy), "url": a.redirect_url,
        "snapshot": snap.strftime("%Y-%m-%d"),
        "age_days": (snap - created).dt.days,
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


def mark_sample(df: pd.DataFrame, max_age: int, cap: int) -> pd.DataFrame:
    """`in_sample` for the 2026 job-board rows: recent enough, at most `cap` per company and group."""
    df = df.copy()
    df["role_group"] = df.title.fillna("").map(role_group)
    boards = df.period.str.startswith("2026") & df.full_text
    fresh = df.age_days.isna() | (df.age_days <= max_age)
    df["in_sample"] = False
    # ad_id breaks ties on the same posting day, so the rows kept never depend on input order.
    pool = df[boards & fresh].sort_values(["snapshot", "posted", "ad_id"], ascending=False, kind="stable")
    keep = pool.groupby(["company", "role_group"]).head(cap).index
    df.loc[keep, "in_sample"] = True
    df.loc[~boards, "in_sample"] = df.loc[~boards, "full_text"]   # LinkedIn 2024 as before; Adzuna never
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ats", type=Path, nargs="+", default=None,
                        help="job-board snapshots; default: the September file and every data/raw/ats_ads_2026-*.csv")
    parser.add_argument("--adzuna", type=Path, default=DEFAULT_ADZUNA)
    parser.add_argument("--linkedin", type=Path, default=DEFAULT_LINKEDIN,
                        help="folder with job_postings.csv and job_summary.csv")
    parser.add_argument("--max-age-days", type=int, default=60)
    parser.add_argument("--cap", type=int, default=3, help="rows per company and role group")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    ats_files = args.ats or [SEPT_ATS] + sorted(RAW.glob("ats_ads_2026-*.csv"))
    for path in (*ats_files, args.adzuna, args.linkedin):
        if not path.exists():
            raise SystemExit(f"{path} not found - see data/README.md for where each source comes from")

    # Latest snapshot first, so a role seen on several days keeps its newest text and date;
    # then the newest posting, so a role re-posted under a new id keeps the fresh copy; ad_id
    # settles the rest. Files are read in reverse name order so a second run on one day (_pm)
    # wins over the first.
    boards = (pd.concat([from_ats(p) for p in sorted(ats_files, key=lambda p: p.name, reverse=True)],
                        ignore_index=True)
                .sort_values(["snapshot", "posted", "ad_id"], ascending=False, kind="stable"))
    frames = {"job boards": boards, "adzuna": from_adzuna(args.adzuna), "linkedin": from_linkedin(args.linkedin)}
    log.info("job-board snapshots: %s", ", ".join(f"{p.name} ({len(from_ats(p))})" for p in ats_files))
    log.info("%-12s %6s %6s %8s", "source", "rows", "data", "deduped")
    kept = []
    for name, f in frames.items():
        t = f.title.fillna("")
        data = f[t.str.contains(DATA_TITLE) & ~t.str.contains(NOT_DATA)]
        year = f.period.str[:4] if name == "job boards" else f.period
        dedup = (data.assign(_y=year).drop_duplicates(subset=["description"])
                     .drop_duplicates(subset=["title", "company", "_y"]).drop(columns="_y"))
        log.info("%-12s %6d %6d %8d", name, len(f), len(data), len(dedup))
        kept.append(dedup)

    # Full text wins when the same 2026 role appears on a job board and on Adzuna.
    out = (pd.concat(kept, ignore_index=True)
             .assign(_y=lambda d: d.period.str[:4])
             .sort_values("full_text", ascending=False, kind="stable")
             .drop_duplicates(subset=["title", "company", "_y"])
             .drop(columns="_y"))
    out = mark_sample(out, args.max_age_days, args.cap)
    out = out.sort_values(["period", "source", "company", "title"]).reset_index(drop=True)[COLUMNS]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")

    log.info("")
    log.info("Wrote %s: %d Australian data roles", args.out.name, len(out))
    summary = out.groupby(["period", "full_text"]).size().unstack(fill_value=0)
    log.info("%s", summary.rename(columns={True: "full text", False: "500-char only"}).to_string())
    b = out[out.period.str.startswith("2026") & out.full_text]
    old = b.age_days > args.max_age_days
    log.info("")
    log.info("2026 job-board roles: %d full text; %d older than %d days dropped", len(b), int(old.sum()), args.max_age_days)
    for g in ("data scientist", "data role"):
        s = b[(b.role_group == g) & b.in_sample]
        log.info("  %-15s %3d in the sample from %d companies (cap %d); before the cap %d",
                 g, len(s), s.company.nunique(), args.cap, int(((b.role_group == g) & ~old).sum()))


if __name__ == "__main__":
    main()
