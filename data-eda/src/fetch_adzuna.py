"""Pull Australian job advertisements from the Adzuna API.

IMPORTANT - READ BEFORE USING THIS FOR SKILL EXTRACTION
-------------------------------------------------------
Adzuna's search endpoint returns a *snippet* of each job description, not the full
text. Their docs say so explicitly: "we currently only provide a snipped of the job
description in the response." Snippets run a few hundred characters.

That means Adzuna alone CANNOT give you a trustworthy skill-frequency chart: you
only see whatever the ad happened to say in its opening lines, which biases results
towards skills named early and against skills buried in a requirements list.

So use it for what it is genuinely good at:
  - Australian geography, job titles, employers, salaries, categories, volumes
  - block 3 evidence that the product is grounded in the Australian market
  - a cross-check against a full-text corpus

and use a full-text corpus (e.g. the LinkedIn postings dump) for the block 5
skill-frequency chart. This script reports the description-length distribution on
every run so you can see the truncation for yourself rather than taking my word.

Setup:
    Register at developer.adzuna.com, then set credentials:
        setx ADZUNA_APP_ID   your_id       (restart the shell afterwards)
        setx ADZUNA_APP_KEY  your_key
    or pass --app-id / --app-key.

Usage:
    python src/fetch_adzuna.py --what "data scientist" "data analyst" --where Sydney --pages 5
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

ENDPOINT = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
MAX_PER_PAGE = 50  # Adzuna caps a page at 50 results

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("fetch_adzuna")


def fetch_page(session, country, page, what, where, app_id, app_key, per_page, insecure):
    """Return (results, total_count) for one page of the Adzuna search endpoint."""
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "results_per_page": per_page,
        "what": what,
        "content-type": "application/json",
    }
    if where:
        params["where"] = where

    response = session.get(
        ENDPOINT.format(country=country, page=page),
        params=params, timeout=30, verify=not insecure,
    )
    if response.status_code == 401:
        raise SystemExit("HTTP 401 - check ADZUNA_APP_ID and ADZUNA_APP_KEY.")
    if response.status_code == 429:
        log.warning("HTTP 429 rate limited on page %d; stopping this query", page)
        return [], None
    if response.status_code != 200:
        log.warning("HTTP %s on page %d: %s", response.status_code, page, response.text[:200])
        return [], None

    payload = response.json()
    return payload.get("results", []), payload.get("count")


def flatten(result, query):
    """Pick the fields worth keeping out of one Adzuna result object."""
    location = result.get("location") or {}
    areas = location.get("area") or []
    return {
        "ad_id": result.get("id"),
        "query": query,
        "title": result.get("title", ""),
        "company": (result.get("company") or {}).get("display_name", ""),
        "location": location.get("display_name", ""),
        "state": areas[1] if len(areas) > 1 else "",
        "category": (result.get("category") or {}).get("label", ""),
        "contract_time": result.get("contract_time", ""),
        "salary_min": result.get("salary_min"),
        "salary_max": result.get("salary_max"),
        "salary_is_predicted": result.get("salary_is_predicted"),
        "created": result.get("created", ""),
        "description": result.get("description", ""),
        "redirect_url": result.get("redirect_url", ""),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--what", nargs="+", required=True, help="one or more search terms")
    parser.add_argument("--where", default="Sydney", help="location, or '' for all of Australia")
    parser.add_argument("--country", default="au")
    parser.add_argument("--pages", type=int, default=5, help="pages per search term")
    parser.add_argument("--per-page", type=int, default=MAX_PER_PAGE)
    parser.add_argument("--delay", type=float, default=1.2, help="seconds between calls")
    parser.add_argument("--app-id", default=os.environ.get("ADZUNA_APP_ID"))
    parser.add_argument("--app-key", default=os.environ.get("ADZUNA_APP_KEY"))
    parser.add_argument("--out", default=paths.RAW / "adzuna_ads.csv", type=Path)
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args()

    if not args.app_id or not args.app_key:
        raise SystemExit(
            "Missing credentials. Register at developer.adzuna.com, then either set "
            "ADZUNA_APP_ID / ADZUNA_APP_KEY or pass --app-id / --app-key."
        )

    session = requests.Session()
    if args.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    rows = []
    for what in args.what:
        log.info("query %r in %r", what, args.where or "all Australia")
        for page in range(1, args.pages + 1):
            results, total = fetch_page(
                session, args.country, page, what, args.where,
                args.app_id, args.app_key, args.per_page, args.insecure,
            )
            if page == 1 and total is not None:
                log.info("  Adzuna reports %s total matches", f"{total:,}")
            if not results:
                break
            rows.extend(flatten(r, what) for r in results)
            log.info("  page %d: +%d (running total %d)", page, len(results), len(rows))
            time.sleep(args.delay)

    if not rows:
        raise SystemExit("No results returned - check your search terms and credentials.")

    df = pd.DataFrame(rows)
    before = len(df)
    df = df.drop_duplicates(subset="ad_id").reset_index(drop=True)
    log.info("deduplicated %d -> %d ads", before, len(df))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"\nWrote {len(df)} ads to {args.out}")

    # The truncation check. Look at these numbers before trusting any skill counts.
    lengths = df["description"].fillna("").str.len()
    print("\nDescription length (characters):")
    print(lengths.describe().round(0).to_string())
    truncated = df["description"].fillna("").str.rstrip().str.endswith(("…", "...")).mean()
    print(f"\nShare of descriptions ending in an ellipsis: {truncated:.0%}")
    if lengths.median() < 1000:
        print(
            "\n>>> Median description is short, which confirms Adzuna is returning snippets.\n"
            ">>> Do NOT build the block 5 skill-frequency chart from this file alone.\n"
            ">>> Use it for geography, titles, employers and salary; use a full-text\n"
            ">>> corpus for skill counts."
        )

    print("\nTop 10 locations:")
    print(df["location"].value_counts().head(10).to_string())


if __name__ == "__main__":
    main()
