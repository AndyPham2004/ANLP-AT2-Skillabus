"""Fetch recent Australian ads per role from the JobsPipe API and keep only what we may commit (plan D2 follow-up).

JobsPipe (jobspipe.dev) aggregates Indeed, LinkedIn, Workday and 11 ATS platforms into one schema with the
full description, the posting date, the country and its own ESCO skill tags. The free key has 1,000 credits
once (1 credit per ad returned, 25 ads per call, 2 calls a second), so this script is run once, by role,
weakest-covered roles first, and writes:

    data/raw/jobspipe/jobspipe_ads_<date>.csv           every ad with its description (gitignored: JobsPipe's
                                                        terms forbid redistributing the data in bulk, and the
                                                        text belongs to the employers)
    data/2_demand/ads/jobspipe_2026_skills.csv          one row per ad: id, role, title, company, location,
                                                        date, employer type, seniority, providers, url (the
                                                        terms ask to keep the link), the vocabulary skills the
                                                        ad names (tier-1 matcher, as every other count) and
                                                        JobsPipe's own ESCO tags. No ad text. This is what
                                                        build_role_skill_demand.py counts (source jobspipe_2026).
    data/2_demand/collection/jobspipe_totals_<date>.csv  per role: the title query, JobsPipe's total number of
                                                        live Australian ads for it in the window, how many were
                                                        fetched and kept.

Filters: country AU, posted in the last MAX_AGE_DAYS (60, as the other 2026 sources), status active, title
contains one of the role's phrases (JobsPipe matches substrings, so "engineer" also finds "Engineering
Manager": management words are excluded in the query and the title is then checked with the same rules as
the job-board ads, classify_ats_roles.role_of).

Usage (from the repo root; needs JOBSPIPE_API_KEY in .env):
    python data-eda/src/fetch_jobspipe.py --dry-run            # show the plan and the credits left, no fetch
    python data-eda/src/fetch_jobspipe.py                      # fetch TARGET ads per role, write the three files
    python data-eda/src/fetch_jobspipe.py --rehit              # recompute the skills column from the raw file
                                                                 (no API calls), after a vocabulary change
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

from build_vocabulary import read_table, skill_hits
from classify_ats_roles import role_of

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

log = logging.getLogger("fetch_jobspipe")

API = "https://api.jobspipe.dev/v1/jobs/search"
COUNTRY, MAX_AGE_DAYS, PAGE = "AU", 60, 25
TARGET = 85                                   # ads per role: 11 x 85 = 935 of the 1,000 one-off credits
NOT_TITLE = ["manager", "director", "head of", "chief", "vice president"]
# Title phrases per role (substring match, case-insensitive; words of 4 letters or fewer match whole words).
# Weakest-covered roles first, so the budget goes where no full-text 2026 source exists yet.
QUERIES: dict[str, list[str]] = {
    "QA/Test Engineer": ["test analyst", "test engineer", "qa engineer", "software tester", "test automation"],
    "Network/Systems Administrator": ["systems administrator", "system administrator", "network administrator",
                                      "network engineer"],
    "Cybersecurity Analyst": ["security analyst", "cyber security analyst", "cybersecurity analyst", "soc analyst",
                              "security operations"],
    "DevOps/SRE": ["devops", "site reliability"],
    "Cloud Engineer": ["cloud engineer"],
    "Business Analyst": ["business analyst"],
    "Data Engineer": ["data engineer"],
    "Data Analyst": ["data analyst"],
    "Machine Learning Engineer": ["machine learning engineer", "ml engineer", "ai engineer"],
    "Data Scientist": ["data scientist"],
    "Software Engineer": ["software engineer", "software developer"],
}
RAW_DIR = paths.RAW / "jobspipe"
OUT = paths.JOBSPIPE_SKILLS
TOTALS_DIR = paths.DEMAND / "collection"
SKILL_COLUMNS = ["ad_id", "role", "title", "company", "location", "date_posted", "employer_type", "seniority",
                 "providers", "url", "n_chars", "skills", "esco_tags"]


def api_key() -> str:
    key = os.environ.get("JOBSPIPE_API_KEY", "")
    if not key:
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.startswith("JOBSPIPE_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit("JOBSPIPE_API_KEY is not set (put it in .env at the repo root)")
    return key


def search(key: str, body: dict, retries: int = 3) -> dict:
    for attempt in range(retries):
        r = requests.post(API, json=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                          timeout=90)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 502, 504) and attempt < retries - 1:
            log.warning("HTTP %s, retrying in 5 s", r.status_code)
            time.sleep(5)
            continue
        sys.exit(f"JobsPipe HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("unreachable")


def fetch_role(key: str, role: str, target: int, dry_run: bool) -> tuple[list[dict], int, int]:
    """Up to `target` ads for the role, newest first; returns (ads, total_results, credits_remaining)."""
    base = {"job_title_or": QUERIES[role], "job_title_not": NOT_TITLE, "job_country_code_or": [COUNTRY],
            "posted_at_max_age_days": MAX_AGE_DAYS, "status": "active", "include_total_results": True}
    if dry_run:
        return [], -1, -1
    ads, cursor, total, remaining = [], None, -1, -1
    while len(ads) < target:
        body = dict(base, limit=min(PAGE, target - len(ads)))
        if cursor:
            body["cursor"] = cursor
        out = search(key, body)
        meta = out.get("metadata", {})
        total, remaining = meta.get("total_results", total), meta.get("credits_remaining", remaining)
        data = out.get("data", [])
        ads += data
        cursor = meta.get("next_cursor")
        log.info("  %s: +%d ads (total live %s, credits charged %s, remaining %s)", role, len(data),
                 meta.get("total_results"), meta.get("credits_charged"), remaining)
        if not data or not cursor:
            break
        time.sleep(0.6)                                   # 2 calls a second allowed
    return ads, total, remaining


def flatten(role: str, ad: dict) -> dict:
    return {
        "ad_id": f"jp-{ad.get('id')}", "role_query": role, "title": (ad.get("job_title") or "").strip(),
        "company": ad.get("company") or "", "location": ad.get("location") or "",
        "date_posted": str(ad.get("date_posted") or "")[:10], "employer_type": ad.get("employer_type") or "",
        "seniority": ad.get("seniority") or "", "providers": "|".join(sorted({s.get("provider", "") for s in ad.get("sources", [])})),
        "url": ad.get("url") or ad.get("source_url") or "", "description": ad.get("description") or "",
        "esco_tags": "|".join(e.get("label", "") for e in (ad.get("esco_skills") or []) if e.get("label")),
        "country_code": ad.get("country_code") or "",
    }


def derive(raw: pd.DataFrame) -> pd.DataFrame:
    """The committed table: role from the title (same rules as the job-board ads), vocabulary skills from the text."""
    raw = raw.copy()
    raw["role"] = raw.title.map(role_of)
    keep = raw.role == raw.role_query                     # the title really is that role (no managers, no pre-sales)
    log.info("%d ads fetched, %d whose title is the queried role", len(raw), int(keep.sum()))
    kept = raw[keep].drop_duplicates("ad_id").drop_duplicates(["company", "title"]).reset_index(drop=True)
    vocab = read_table(paths.SKILLS_VOCABULARY)
    detection = vocab[vocab.used_for.str.contains("extract")].reset_index(drop=True)
    hits = skill_hits(detection, kept.description.fillna(""))
    kept["skills"] = ["|".join(sorted(h)) for h in hits]
    kept["n_chars"] = kept.description.str.len()
    return kept[SKILL_COLUMNS].sort_values(["role", "company", "title", "ad_id"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=int, default=TARGET, help="ads per role")
    parser.add_argument("--roles", nargs="*", default=list(QUERIES), help="roles to fetch (default: all 11)")
    parser.add_argument("--date", default=dt.date.today().isoformat())
    parser.add_argument("--dry-run", action="store_true", help="show the plan and the credits left, fetch nothing")
    parser.add_argument("--rehit", action="store_true", help="recompute skills from the raw file, no API calls")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    raw_csv = RAW_DIR / f"jobspipe_ads_{args.date}.csv"

    if args.rehit:
        raw = pd.read_csv(raw_csv, dtype=str, keep_default_na=False)
        table = derive(raw)
        table.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n")
        log.info("rewrote %s: %d ads", OUT, len(table))
        return

    key = api_key()
    probe = search(key, {"job_country_code_or": [COUNTRY], "limit": 1, "include_total_results": True})
    meta = probe.get("metadata", {})
    log.info("credits remaining %s of %s; %s live AU ads in all", meta.get("credits_remaining"),
             meta.get("credits_allowance"), meta.get("total_results"))
    need = args.target * len(args.roles)
    log.info("plan: %d roles x %d ads = %d credits, %d days, country %s", len(args.roles), args.target, need, MAX_AGE_DAYS, COUNTRY)
    if args.dry_run:
        return
    if meta.get("credits_remaining", 0) < need:
        sys.exit(f"not enough credits: {meta.get('credits_remaining')} left, {need} needed; lower --target or --roles")

    rows, totals = [], []
    for role in args.roles:
        ads, total, remaining = fetch_role(key, role, args.target, dry_run=False)
        rows += [flatten(role, ad) for ad in ads]
        totals.append({"role": role, "title_query": "|".join(QUERIES[role]), "title_not": "|".join(NOT_TITLE),
                       "country": COUNTRY, "max_age_days": MAX_AGE_DAYS, "total_results": total, "fetched": len(ads),
                       "date": args.date})
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        (RAW_DIR / f"{args.date}_{role.replace('/', '-').replace(' ', '_')}.json").write_text(json.dumps(ads), encoding="utf-8")
        if remaining >= 0 and remaining < PAGE:
            log.warning("stopping: %d credits left", remaining)
            break
    raw = pd.DataFrame(rows)
    raw.to_csv(raw_csv, index=False, encoding="utf-8", lineterminator="\n")
    log.info("raw: %s (%d ads, gitignored)", raw_csv, len(raw))

    table = derive(raw)
    kept_by_role = table.role.value_counts()
    for t in totals:
        t["kept"] = int(kept_by_role.get(t["role"], 0))
    tot = pd.DataFrame(totals)
    TOTALS_DIR.mkdir(parents=True, exist_ok=True)
    tot.to_csv(TOTALS_DIR / f"jobspipe_totals_{args.date}.csv", index=False, lineterminator="\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n")
    log.info("kept per role:\n%s", kept_by_role.to_string())
    log.info("wrote %s (%d ads) and %s", OUT, len(table), TOTALS_DIR / f"jobspipe_totals_{args.date}.csv")


if __name__ == "__main__":
    main()
