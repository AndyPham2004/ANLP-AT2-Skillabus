"""Count live Australian ads per certification on Adzuna; fill au_ads_count, count_date and hot.

For every row of data/1_knowledge/learning_resources/certifications.csv this makes ONE call to the
Adzuna AU search endpoint with results_per_page=1 and keeps only the `count` in the reply (how many
ads live on Adzuna Australia contain the row's `adzuna_query`). No ad text is stored.

    - `adzuna_query` is sent as an exact phrase (`what_phrase`); --match words sends it as `what`
      (every word somewhere in the ad) instead.
    - The first call has no query: it gives the number of all live AU ads, printed as the denominator.
      A phrase count equal to that number means Adzuna ignored the phrase, and the run stops.
    - Adzuna's default limit is 25 calls a minute and 250 a day (developer.adzuna.com/docs/terms_of_service),
      so the default gap between calls is 2.5 s (50 calls, about 2 minutes). On HTTP 429 it waits a minute
      and tries once more.
    - A second run on a later day moves the old count to au_ads_count_prev / count_date_prev, which
      gives the trend.
    - Then it applies the hot rule (certifications.md) and writes `hot` and `hot_reason`.

Credentials: ADZUNA_APP_ID and ADZUNA_APP_KEY in .env at the repo root (copy .env.example), in the
environment, or --app-id / --app-key. The auth and the HTTP call are fetch_adzuna.py's.

Usage (from the repo root):
    python data-eda/src/count_cert_adzuna.py --limit 3 --dry-run     # try three rows, write nothing
    python data-eda/src/count_cert_adzuna.py                         # all rows, write the CSV
    python data-eda/src/count_cert_adzuna.py --category it-jobs      # only Adzuna's IT category
    python data-eda/src/count_cert_adzuna.py --hot-only              # recompute hot from the counts in the file
"""
from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))              # data-eda/src, for fetch_adzuna
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
import fetch_adzuna  # noqa: E402
from skillabus import paths  # noqa: E402

ROLES = (
    "Data Scientist", "Data Analyst", "Data Engineer", "Machine Learning Engineer", "Software Engineer", "QA/Test Engineer",
    "Cloud Engineer", "DevOps/SRE", "Network/Systems Administrator", "Cybersecurity Analyst", "Business Analyst",
)
TREND_MIN_CHANGE = 0.20   # a rise of 20% or more between two counts ...
TREND_MIN_COUNT = 10      # ... on at least 10 ads also makes a certificate hot


class PhraseIgnored(RuntimeError):
    pass


def count_ads(session, query, *, match="phrase", where="", category=None, max_days_old=None,
              app_id, app_key, country="au", insecure=False, retry_wait=60.0):
    """Adzuna's `count` for one query (None if the call failed). Empty query = all live ads."""
    what, extra = "", {}
    if query:
        if match == "phrase":
            extra["what_phrase"] = query
        else:
            what = query
    if category:
        extra["category"] = category
    if max_days_old:
        extra["max_days_old"] = int(max_days_old)
    for attempt in (1, 2):
        try:
            _, total = fetch_adzuna.fetch_page(session, country, 1, what, where, app_id, app_key, 1, insecure,
                                               extra_params=extra)
        except requests.RequestException as e:
            fetch_adzuna.log.warning("request failed for %r: %s", query, e)
            total = None
        if total is not None or attempt == 2:
            return total
        time.sleep(retry_wait)            # 429 or a passing error: wait once, then one more try
    return None


def count_all(certs: pd.DataFrame, session, *, delay=2.5, today=None, **kw) -> tuple[pd.DataFrame, int | None]:
    """Fill au_ads_count / count_date (old values move to *_prev). Returns (certs, all-ads count)."""
    today = today or dt.date.today().isoformat()
    certs = certs.copy()
    for col in ("au_ads_count", "count_date", "au_ads_count_prev", "count_date_prev", "hot", "hot_reason"):
        if col not in certs:
            certs[col] = ""
    everything = count_ads(session, "", **kw)
    print(f"All live Adzuna AU ads{' in ' + kw['category'] if kw.get('category') else ''}: {everything}")
    for i, row in certs.iterrows():
        time.sleep(delay)
        n = count_ads(session, row["adzuna_query"], **kw)
        if n is not None and everything and n == everything and kw.get("match", "phrase") == "phrase":
            raise PhraseIgnored(
                f"'{row['adzuna_query']}' returned {n}, the same as all ads: Adzuna ignored what_phrase. "
                "Rerun with --match words.")
        print(f"  {n!s:>7}  {row['adzuna_query']!r:42} {row['cert']}")
        if n is None:
            continue
        if str(row["au_ads_count"]).strip() and str(row["count_date"]).strip() != today:
            certs.at[i, "au_ads_count_prev"] = row["au_ads_count"]
            certs.at[i, "count_date_prev"] = row["count_date"]
        certs.at[i, "au_ads_count"] = str(int(n))
        certs.at[i, "count_date"] = today
    return certs, everything


def _int(value):
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def apply_hot_rule(certs: pd.DataFrame) -> pd.DataFrame:
    """hot = yes when, among the certificates of at least one of its roles, its au_ads_count is in the top
    third (and at least 1); or a recent industry report names it (report_signal) and au_ads_count >= 1; or it
    rose 20% or more since the previous count and has at least 10 ads. Rows without a count stay blank."""
    certs = certs.copy()
    counts = certs["au_ads_count"].map(_int)
    roles = certs["roles"].map(lambda s: [r.strip() for r in str(s).split(";") if r.strip()])
    top = {i: [] for i in certs.index}
    for role in ROLES:
        idx = [i for i in certs.index if role in roles[i] and counts[i] is not None]
        if not idx:
            continue
        ranked = sorted(idx, key=lambda i: counts[i], reverse=True)
        for i in ranked[: math.ceil(len(ranked) / 3)]:
            if counts[i] >= 1:
                top[i].append(role)
    for i in certs.index:
        n = counts[i]
        if n is None:
            certs.at[i, "hot"], certs.at[i, "hot_reason"] = "", ""
            continue
        reasons = []
        if top[i]:
            reasons.append(f"top third of certificates for {', '.join(top[i])} ({n} AU ads on {certs.at[i, 'count_date']})")
        if str(certs.at[i, "report_signal"]).strip() and n >= 1:
            reasons.append(str(certs.at[i, "report_signal"]).split(":")[0])
        prev = _int(certs.at[i, "au_ads_count_prev"]) if "au_ads_count_prev" in certs else None
        if prev:
            change = (n - prev) / prev
            if change >= TREND_MIN_CHANGE and n >= TREND_MIN_COUNT:
                reasons.append(f"rising {change:+.0%} since {certs.at[i, 'count_date_prev']}")
        certs.at[i, "hot"] = "yes" if reasons else "no"
        certs.at[i, "hot_reason"] = "; ".join(reasons)
    return certs


def main(argv=None):
    from dotenv import load_dotenv

    load_dotenv(paths.ENV_FILE)
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--certs", type=Path, default=paths.CERTIFICATIONS)
    parser.add_argument("--match", choices=("phrase", "words"), default="phrase")
    parser.add_argument("--where", default="", help="location; default all of Australia")
    parser.add_argument("--category", help="Adzuna category tag, e.g. it-jobs; default all categories")
    parser.add_argument("--max-days-old", type=int, help="only ads posted in the last N days")
    parser.add_argument("--delay", type=float, default=2.5, help="seconds between calls (Adzuna: 25 a minute)")
    parser.add_argument("--limit", type=int, help="only the first N rows (a test run)")
    parser.add_argument("--date", help="count_date to write, YYYY-MM-DD; default today")
    parser.add_argument("--app-id", default=os.environ.get("ADZUNA_APP_ID"))
    parser.add_argument("--app-key", default=os.environ.get("ADZUNA_APP_KEY"))
    parser.add_argument("--insecure", action="store_true")
    parser.add_argument("--hot-only", action="store_true", help="no calls: recompute hot from the file's counts")
    parser.add_argument("--dry-run", action="store_true", help="print the counts, do not write the CSV")
    args = parser.parse_args(argv)

    certs = pd.read_csv(args.certs, dtype=str, keep_default_na=False)
    if not args.hot_only:
        if not args.app_id or not args.app_key:
            raise SystemExit("Missing credentials: put ADZUNA_APP_ID and ADZUNA_APP_KEY in .env (see .env.example), "
                             "or pass --app-id / --app-key.")
        todo = certs.head(args.limit) if args.limit else certs
        session = requests.Session()
        counted, _ = count_all(todo, session, delay=args.delay, today=args.date, match=args.match, where=args.where,
                               category=args.category, max_days_old=args.max_days_old, app_id=args.app_id,
                               app_key=args.app_key, insecure=args.insecure)
        for col in counted.columns:
            if col not in certs:
                certs[col] = ""
        certs.loc[counted.index, counted.columns] = counted
    certs = apply_hot_rule(certs)
    print(f"hot = yes for {(certs['hot'] == 'yes').sum()} of {len(certs)} certificates")
    if not args.dry_run:
        certs.to_csv(args.certs, index=False, encoding="utf-8", lineterminator="\n")
        print(f"Wrote {args.certs}")
    return certs


if __name__ == "__main__":
    main()
