"""Pull FULL-TEXT job advertisements from public ATS job-board APIs.

Why this exists
---------------
Adzuna caps every description at exactly 500 characters, so it cannot support a
skill-frequency chart. LinkedIn's User Agreement bans automated access. But many
employers publish their vacancies through applicant tracking systems whose job
boards expose a public, unauthenticated JSON API intended to be consumed - that is
how the "careers" page on their own website is rendered.

Three platforms are covered:
    Greenhouse       https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
    Lever            https://api.lever.co/v0/postings/{slug}?mode=json
    SmartRecruiters  https://api.smartrecruiters.com/v1/companies/{slug}/postings

SmartRecruiters needs two calls per job: the listing carries location but no body,
so we filter to Australia FIRST and only then fetch each detail. That keeps the
call count proportional to what we actually keep.

Both return the complete advertisement text. No key, no login, no ToS breach.

Known limitation - state this on the poster
-------------------------------------------
Coverage is per-employer, and the employers reachable this way skew towards tech
companies that use a modern ATS. This is NOT a representative sample of the
Australian labour market. Use it as a full-text Australian supplement that
cross-checks the LinkedIn corpus, not as a replacement for it.

Usage:
    python src/fetch_ats.py --australia-only
    python src/fetch_ats.py --companies config/ats_companies.csv
"""

import argparse
import html as html_lib
import logging
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
GREENHOUSE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
LEVER = "https://api.lever.co/v0/postings/{slug}"
SMARTRECRUITERS = "https://api.smartrecruiters.com/v1/companies/{slug}/postings"
SMARTRECRUITERS_DETAIL = "https://api.smartrecruiters.com/v1/companies/{slug}/postings/{pid}"
HEADERS = {"User-Agent": "Mozilla/5.0 (UTS 36118 student project)"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("fetch_ats")


def to_text(raw):
    """Convert an ATS content field to plain text.

    Order matters: these fields arrive HTML-escaped, so unescape FIRST and strip
    tags SECOND. Doing it the other way round leaves real tags in the output once
    the entities decode.
    """
    if not raw:
        return ""
    text = html_lib.unescape(str(raw))
    text = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()


def fetch_greenhouse(session, slug, company, insecure):
    url = GREENHOUSE.format(slug=slug)
    r = session.get(url, params={"content": "true"}, headers=HEADERS,
                    timeout=30, verify=not insecure)
    if r.status_code != 200:
        log.warning("greenhouse/%s -> HTTP %s", slug, r.status_code)
        return []
    rows = []
    for j in r.json().get("jobs", []):
        rows.append({
            "ad_id": f"gh-{j.get('id')}",
            "source": "greenhouse",
            "title": j.get("title", ""),
            "company": company or j.get("company_name", slug),
            "location": (j.get("location") or {}).get("name", ""),
            "created": j.get("first_published", "") or j.get("updated_at", ""),
            "description": to_text(j.get("content")),
            "redirect_url": j.get("absolute_url", ""),
        })
    return rows


def fetch_lever(session, slug, company, insecure):
    url = LEVER.format(slug=slug)
    r = session.get(url, params={"mode": "json"}, headers=HEADERS,
                    timeout=30, verify=not insecure)
    if r.status_code != 200:
        log.warning("lever/%s -> HTTP %s", slug, r.status_code)
        return []
    payload = r.json()
    if not isinstance(payload, list):
        return []
    rows = []
    for j in payload:
        categories = j.get("categories") or {}
        body = " ".join(filter(None, [
            j.get("descriptionPlain") or j.get("description") or "",
            *(to_text(s.get("text")) + " " + to_text(s.get("content"))
              for s in (j.get("lists") or [])),
            j.get("additionalPlain") or j.get("additional") or "",
        ]))
        rows.append({
            "ad_id": f"lv-{j.get('id')}",
            "source": "lever",
            "title": j.get("text", ""),
            "company": company or slug,
            "location": categories.get("location", ""),
            "created": j.get("createdAt", ""),
            "description": to_text(body),
            "redirect_url": j.get("hostedUrl", ""),
        })
    return rows


def fetch_smartrecruiters(session, slug, company, insecure, au_only=True, delay=0.25):
    """List postings (paginated), keep Australian ones, then fetch each full ad."""
    keep, offset = [], 0
    while True:
        r = session.get(SMARTRECRUITERS.format(slug=slug),
                        params={"limit": 100, "offset": offset},
                        headers=HEADERS, timeout=30, verify=not insecure)
        if r.status_code != 200:
            log.warning("smartrecruiters/%s -> HTTP %s", slug, r.status_code)
            break
        payload = r.json()
        batch = payload.get("content", [])
        if not batch:
            break
        for j in batch:
            loc = j.get("location") or {}
            if not au_only or str(loc.get("country", "")).lower() == "au":
                keep.append((j, loc))
        offset += len(batch)
        if offset >= (payload.get("totalFound") or 0):
            break
        time.sleep(delay)

    rows = []
    for j, loc in keep:
        d = session.get(SMARTRECRUITERS_DETAIL.format(slug=slug, pid=j.get("id")),
                        headers=HEADERS, timeout=30, verify=not insecure)
        sections = d.json().get("jobAd", {}).get("sections", {}) if d.status_code == 200 else {}
        body = " ".join(str((sections.get(k) or {}).get("text", ""))
                        for k in ("companyDescription", "jobDescription",
                                  "qualifications", "additionalInformation"))
        rows.append({
            "ad_id": f"sr-{j.get('id')}",
            "source": "smartrecruiters",
            "title": j.get("name", ""),
            "company": company or slug,
            "location": ", ".join(filter(None, [loc.get("city"), loc.get("region"),
                                                (loc.get("country") or "").upper()])),
            "created": j.get("releasedDate", ""),
            "description": to_text(body),
            "redirect_url": j.get("ref", ""),
        })
        time.sleep(delay)
    return rows


AU_PATTERN = re.compile(
    r"austral|sydney|melbourne|brisbane|perth|adelaide|canberra|hobart|darwin"
    r"|nsw|vic|qld|\bwa\b|\bsa\b|\bact\b|\bnt\b|\btas\b", re.I
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companies", default=ROOT / "config" / "ats_companies.csv", type=Path)
    parser.add_argument("--australia-only", action="store_true",
                        help="keep only roles whose location looks Australian")
    parser.add_argument("--out", default=ROOT / "data" / "raw" / "ats_ads.csv", type=Path)
    parser.add_argument("--delay", type=float, default=0.8)
    parser.add_argument("--insecure", action="store_true")
    args = parser.parse_args()

    companies = pd.read_csv(args.companies)
    session = requests.Session()
    if args.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    rows = []
    for c in companies.itertuples(index=False):
        name = getattr(c, "company", c.slug)
        if c.platform == "smartrecruiters":
            got = fetch_smartrecruiters(session, c.slug, name, args.insecure,
                                        au_only=args.australia_only, delay=args.delay / 3)
        elif c.platform == "greenhouse":
            got = fetch_greenhouse(session, c.slug, name, args.insecure)
        else:
            got = fetch_lever(session, c.slug, name, args.insecure)
        log.info("%-11s %-16s %3d jobs", c.platform, c.slug, len(got))
        rows.extend(got)
        time.sleep(args.delay)

    if not rows:
        raise SystemExit("Nothing fetched - check the slugs in the companies file.")

    df = pd.DataFrame(rows).drop_duplicates(subset="ad_id").reset_index(drop=True)
    total = len(df)

    if args.australia_only:
        df = df[df["location"].fillna("").str.contains(AU_PATTERN)].reset_index(drop=True)
        log.info("Australian filter: %d -> %d roles", total, len(df))

    if df.empty:
        raise SystemExit("No rows left after the Australian filter.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")

    lengths = df["description"].fillna("").str.len()
    print(f"\nWrote {len(df)} ads to {args.out}")
    print("\nDescription length (characters) - compare with Adzuna's flat 500:")
    print(lengths.describe().round(0).to_string())
    print(f"\nEmployers: {df['company'].nunique()}   Empty descriptions: {(lengths == 0).sum()}")
    print("\nBy company:")
    print(df["company"].value_counts().to_string())


if __name__ == "__main__":
    main()
