"""Scrape UTS subject descriptions and learning outcomes from the course handbook.

The handbook moved from handbook.uts.edu.au to coursehandbook.uts.edu.au, which is
a Next.js front end over the CourseLoop platform. The CourseLoop REST API itself
returns 403 without credentials, but every subject page is server-rendered with
its full payload embedded in a <script id="__NEXT_DATA__"> tag. We parse that
rather than scraping rendered HTML, so the fields come out already structured and
the parser does not break when the page styling changes.

Two modes:

    # 1. discover the subject codes in a course (MDSI is C04372)
    python src/scrape_handbook.py --course C04372 --list-only

    # 2. fetch those subjects into the CSV that C needs
    python src/scrape_handbook.py --course C04372 --year 2026

    # or fetch an explicit list
    python src/scrape_handbook.py --codes 36118 36103 36106 --year 2026

Output: data/raw/uts_subjects.csv
"""

import argparse
import html as html_lib
import json
import logging
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://coursehandbook.uts.edu.au"
NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)
SUBJECT_CODE = re.compile(r"Subject:\s*(\w+)")
HEADERS = {"User-Agent": "Mozilla/5.0 (UTS 36118 student project; contact via UTS)"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("scrape_handbook")


def clean(raw):
    """Strip HTML tags and unescape entities, collapsing whitespace."""
    if not raw:
        return ""
    text = re.sub(r"<li>", " | ", str(raw))
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip(" |").strip()


def fetch_payload(session, url, insecure=False):
    """Return the pageContent dict embedded in a handbook page, or None."""
    response = session.get(url, headers=HEADERS, timeout=30, verify=not insecure)
    if response.status_code != 200:
        log.warning("%s -> HTTP %s", url, response.status_code)
        return None
    match = NEXT_DATA.search(response.text)
    if not match:
        log.warning("%s -> no __NEXT_DATA__ block (page structure may have changed)", url)
        return None
    try:
        data = json.loads(match.group(1))
        return data["props"]["pageProps"]["pageContent"]
    except (json.JSONDecodeError, KeyError) as exc:
        log.warning("%s -> could not read payload: %s", url, exc)
        return None


def discover_codes(session, course, year, insecure=False):
    """Return {subject_code: curriculum group} from a course's curriculumStructure.

    The structure is a tree of containers (Core, Electives, Innovation Labs), each
    holding relationship entries whose child_record.value reads "Subject: 36118".
    Walking it properly also tells us which group a subject sits in, which is what
    lets the app distinguish "you must do this" from "you could choose this".
    """
    url = f"{BASE}/course/{year}/{course}"
    payload = fetch_payload(session, url, insecure)
    if payload is None:
        return {}
    log.info("course %s: %s (%s cp, %s)", course, payload.get("title"),
             payload.get("credit_points"), payload.get("implementation_year"))

    found = {}

    def walk(node, path):
        if not isinstance(node, dict):
            return
        title = node.get("title") or node.get("name") or ""
        here = path + [title] if title else path
        for rel in (node.get("relationship") or []):
            value = str((rel.get("child_record") or {}).get("value", ""))
            match = SUBJECT_CODE.match(value)
            if match:
                found.setdefault(match.group(1), here[-1] if here else "")
        for child in (node.get("container") or []):
            walk(child, here)

    walk(payload.get("curriculumStructure") or {}, [])
    log.info("discovered %d subjects: %s", len(found),
             ", ".join(f"{g}={sum(1 for v in found.values() if v == g)}"
                       for g in dict.fromkeys(found.values())))
    return found


def parse_subject(payload, year):
    """Flatten a subject payload into one row, outcomes joined into one field."""
    outcomes = payload.get("unit_learning_outcomes") or []
    ordered = sorted(outcomes, key=lambda o: int(o.get("number") or 0))
    outcome_text = " ".join(
        f"{o.get('code', '')}: {clean(o.get('description'))}".strip(": ")
        for o in ordered
        if clean(o.get("description"))
    )

    return {
        "subject_code": payload.get("code", ""),
        "subject_name": payload.get("title", ""),
        "credit_points": payload.get("credit_points", ""),
        "faculty": payload.get("academic_org", ""),
        "study_level": payload.get("study_level_ref", ""),
        "year": payload.get("implementation_year", year),
        "n_outcomes": len(ordered),
        "learning_outcomes": outcome_text,
        "description": clean(payload.get("description")),
        "topics": clean(payload.get("learning_approach")),
        "teaching_strategies": clean(payload.get("teaching_strategies")),
        "requisites": clean(payload.get("requisite_detail")),
        "handbook_url": f"{BASE}/subject/{year}/{payload.get('code', '')}",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", nargs="*", default=None,
                        help="one or more course codes, e.g. C04372 C04380 C04295")
    parser.add_argument("--codes", nargs="*", default=None, help="explicit subject codes")
    parser.add_argument("--year", default="2026", help="handbook year (or 'current')")
    parser.add_argument("--out", default=ROOT / "data" / "raw" / "uts_subjects.csv", type=Path)
    parser.add_argument("--delay", type=float, default=0.7, help="seconds between requests")
    parser.add_argument("--list-only", action="store_true", help="print codes and stop")
    parser.add_argument("--insecure", action="store_true",
                        help="skip TLS verification (only if behind an intercepting proxy)")
    args = parser.parse_args()

    if not args.course and not args.codes:
        raise SystemExit("Give me --course C04372 or --codes 36118 36103 ...")

    session = requests.Session()
    if args.insecure:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # A subject can sit in several courses, so remember every course that claims it.
    groups, courses = {}, {}
    for course in (args.course or []):
        for code, group in discover_codes(session, course, args.year, args.insecure).items():
            groups.setdefault(code, group)
            courses.setdefault(code, []).append(course)
        time.sleep(args.delay)
    codes = sorted(set(args.codes or []) | set(groups))

    if not codes:
        raise SystemExit(
            "No subject codes found. The course page structure may have changed - "
            "pass codes explicitly with --codes instead."
        )

    if args.list_only:
        print(" ".join(codes))
        return

    rows, failed = [], []
    for i, code in enumerate(codes, 1):
        url = f"{BASE}/subject/{args.year}/{code}"
        payload = fetch_payload(session, url, args.insecure)
        if payload is None or not payload.get("code"):
            failed.append(code)
        else:
            row = parse_subject(payload, args.year)
            row["curriculum_group"] = groups.get(code, "")
            row["courses"] = "|".join(courses.get(code, []))
            rows.append(row)
            log.info("[%d/%d] %s %s (%d outcomes)",
                     i, len(codes), row["subject_code"], row["subject_name"], row["n_outcomes"])
        time.sleep(args.delay)

    if not rows:
        raise SystemExit("Nothing scraped successfully - check --year and the codes.")

    df = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")

    print(f"\nWrote {len(df)} subjects to {args.out}")
    print(f"Subjects with zero learning outcomes: {(df['n_outcomes'] == 0).sum()}")
    if failed:
        print(f"FAILED ({len(failed)}): {', '.join(failed)}")
        print("Retry these, or paste them by hand into config/subjects_template.csv.")
    print("\n" + df[["subject_code", "subject_name", "credit_points", "n_outcomes"]].to_string(index=False))


if __name__ == "__main__":
    main()
