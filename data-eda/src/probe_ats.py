"""Which Australian employers can we reach through a public ATS job-board API, and how many
data-scientist ads do they have open right now?

Reads config/ats_candidates.csv (one row per company, a slug guess per platform; blank = not
tried), hits each platform's public listing endpoint, and writes data/clean/ats_probe_<date>.csv
with one row per (company, platform): status, total ads, Australian ads, Australian data roles,
Australian data-scientist roles. No key, no login; these endpoints exist to render the
companies' own careers pages (see fetch_ats.py).

Usage (from data-eda/):
    python src/probe_ats.py
    python src/probe_ats.py --only canva atlassian
"""

from __future__ import annotations

import argparse
import logging
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from build_recent_sample import DATA_TITLE
from fetch_ats import AU_PATTERN, HEADERS, fetch_greenhouse, fetch_lever, fetch_smartrecruiters, to_text

ROOT = Path(__file__).resolve().parents[1]
ASHBY = "https://api.ashbyhq.com/posting-api/job-board/{slug}"
WORKABLE = "https://apply.workable.com/api/v1/widget/accounts/{slug}"
DS_TITLE = re.compile(r"data scien|applied scien|research scien|machine learning|\bML\b|AI scientist", re.I)
BARE_AI = re.compile(r"\bAI\b", re.I)
PLATFORMS = ("greenhouse", "lever", "smartrecruiters", "ashby", "workable")

log = logging.getLogger("probe_ats")


def classify(status_code: int, rows: list | None) -> str:
    if status_code == 404:
        return "missing"
    if status_code != 200:
        return "error"
    return "ok" if rows else "empty"


def is_data_title(title: str) -> bool:
    """DATA_TITLE without the bare 'AI' match that lets 'Graphic AI Designer' through."""
    t = title or ""
    if DS_TITLE.search(t):
        return True
    return bool(DATA_TITLE.search(t)) and not (BARE_AI.search(t) and not re.search(r"data|analy|engineer|scien|learning|intelligence", t, re.I))


def count_roles(rows: list[dict]) -> dict:
    au = [r for r in rows if AU_PATTERN.search(r.get("location") or "")]
    return {"total": len(rows), "au": len(au),
            "data_au": sum(is_data_title(r.get("title")) for r in au),
            "ds_au": sum(bool(DS_TITLE.search(r.get("title") or "")) for r in au)}


def fetch_ashby(session, slug):
    r = session.get(ASHBY.format(slug=slug), headers=HEADERS, timeout=30)
    rows = [] if r.status_code != 200 else [
        {"ad_id": f"as-{j.get('id')}", "source": "ashby", "title": j.get("title", ""), "company": slug,
         "location": j.get("location", ""), "created": j.get("publishedAt", ""),
         "description": to_text(j.get("descriptionHtml") or j.get("descriptionPlain")), "redirect_url": j.get("jobUrl", "")}
        for j in r.json().get("jobs", [])]
    return r.status_code, rows


def fetch_workable(session, slug):
    r = session.get(WORKABLE.format(slug=slug), params={"details": "true"}, headers=HEADERS, timeout=30)
    rows = [] if r.status_code != 200 else [
        {"ad_id": f"wk-{j.get('shortcode')}", "source": "workable", "title": j.get("title", ""), "company": slug,
         "location": ", ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")])),
         "created": j.get("published_on", ""), "description": to_text(j.get("description")), "redirect_url": j.get("url", "")}
        for j in r.json().get("jobs", [])]
    return r.status_code, rows


def probe(session, platform: str, slug: str) -> dict:
    try:
        if platform == "greenhouse":
            r = session.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", headers=HEADERS, timeout=30)
            rows = fetch_greenhouse(session, slug, slug, False) if r.status_code == 200 else []
            code = r.status_code
        elif platform == "lever":
            r = session.get(f"https://api.lever.co/v0/postings/{slug}", params={"mode": "json"}, headers=HEADERS, timeout=30)
            rows = fetch_lever(session, slug, slug, False) if r.status_code == 200 else []
            code = r.status_code
        elif platform == "smartrecruiters":
            r = session.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params={"limit": 1}, headers=HEADERS, timeout=30)
            code = r.status_code
            rows = []
            if code == 200 and (r.json().get("totalFound") or 0) > 0:
                rows = fetch_smartrecruiters(session, slug, slug, False, au_only=True, delay=0.25)
        elif platform == "ashby":
            code, rows = fetch_ashby(session, slug)
        else:
            code, rows = fetch_workable(session, slug)
    except (requests.RequestException, ValueError) as exc:
        log.warning("%s/%s -> %s", platform, slug, exc)
        return {"status": "error", "rows": []}
    return {"status": classify(code, rows), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidates", type=Path, default=ROOT / "config" / "ats_candidates.csv")
    parser.add_argument("--only", nargs="*", default=None, help="company names to probe")
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "clean" / f"ats_probe_{date.today().isoformat()}.csv")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cands = pd.read_csv(args.candidates, dtype=str).fillna("")
    if args.only:
        cands = cands[cands.company.str.lower().isin([o.lower() for o in args.only])]
    session = requests.Session()
    out = []
    for c in cands.itertuples(index=False):
        for platform in PLATFORMS:
            slug = getattr(c, platform, "")
            if not slug:
                continue
            res = probe(session, platform, slug)
            counts = count_roles(res["rows"])
            out.append({"company": c.company, "platform": platform, "slug": slug, "status": res["status"], **counts})
            log.info("%-28s %-15s %-8s total=%3d au=%3d data_au=%2d ds_au=%2d", c.company, platform, res["status"],
                     counts["total"], counts["au"], counts["data_au"], counts["ds_au"])
            time.sleep(args.delay)
    df = pd.DataFrame(out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    hit = df[df.status == "ok"]
    print(f"\nWrote {args.out}: {len(df)} probes, {len(hit)} reachable boards, "
          f"{int(hit.au.sum())} AU ads, {int(hit.data_au.sum())} AU data roles, {int(hit.ds_au.sum())} AU data-scientist roles")
    print(hit.sort_values('ds_au', ascending=False)[['company', 'platform', 'au', 'data_au', 'ds_au']].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
