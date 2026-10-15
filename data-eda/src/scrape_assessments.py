"""Assessment tasks for every subject, from the handbook's per-offering data route.

The subject page shows no assessment until an availability is chosen. Choosing one makes the
browser fetch the Next.js data route

    /_next/data/<buildId>/subject/<year>/<code>.json?offering=<display_name>

which returns the page payload with `selected_assessment` filled: one item per task with
name ("Assessment 2: End-to-end NLP project"), assessment_type ("Report"), weight ("50") and
individual ("Group, group and individually assessed"). The route answers without cookies
(checked 13 Oct 2026), and the task list is the same for every offering of a subject
(`applies_to_all_offerings`), so one offering per subject is enough; we still union them.

Usage (from the repo root):
    python data-eda/src/scrape_assessments.py                 # all subjects in uts_subjects_2026.csv
    python data-eda/src/scrape_assessments.py --codes 36118   # a few

Writes data/1_knowledge/uts/assessments_scraped.csv in the subject_profiles.csv shape
(layer = assessment, collected_by = "script (handbook)"); build_subject_profiles.py merges it.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))  # repo src/, for skillabus.paths
from skillabus import paths  # noqa: E402

SUBJECTS = paths.UTS_SUBJECTS_RAW
OUT = paths.ASSESSMENTS_SCRAPED
BASE = "https://coursehandbook.uts.edu.au"
HEADERS = {"User-Agent": "Mozilla/5.0 (UTS 36118 student project)"}
NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)
COLUMNS = ["subject_code", "subject_name", "course", "layer", "text", "source_url", "collected_by"]

log = logging.getLogger("scrape_assessments")


def task_text(item: dict) -> str:
    """One quotable line per task: name, then type, weight and group/individual in brackets."""
    name = (item.get("name") or "").strip()
    bits = [b for b in [(item.get("assessment_type") or "").strip(),
                        f"{item['weight']}%" if item.get("weight") else "",
                        (item.get("individual") or "").strip()] if b]
    desc = html.unescape(re.sub(r"<[^>]+>", " ", item.get("description") or "")).strip()
    desc = re.sub(r"\s+", " ", desc)
    text = f"{name} ({', '.join(bits)})" if bits else name
    return f"{text}. {desc}" if desc else text


def rows_from_items(items: list[dict], subject: dict, url: str) -> list[dict]:
    """Rows in the profile shape, ordered by task number, de-duplicated by text."""
    seen, rows = set(), []
    for item in sorted(items or [], key=lambda i: int(i.get("number") or 0)):
        text = task_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append({"subject_code": subject["subject_code"], "subject_name": subject["subject_name"],
                     "course": subject.get("course", ""), "layer": "assessment", "text": text,
                     "source_url": url, "collected_by": "script (handbook)"})
    return rows


def build_id(session: requests.Session, year: str, code: str) -> str:
    html = session.get(f"{BASE}/subject/{year}/{code}", headers=HEADERS, timeout=30).text
    return json.loads(NEXT_DATA.search(html).group(1))["buildId"]


def fetch_json(session: requests.Session, build: str, year: str, code: str, offering: str | None) -> dict | None:
    params = {"catchAll": ["subject", year, code]}
    if offering:
        params["offering"] = offering
    r = session.get(f"{BASE}/_next/data/{build}/subject/{year}/{code}.json", params=params, headers=HEADERS, timeout=30)
    if r.status_code != 200:
        log.warning("%s offering=%s -> HTTP %s", code, offering, r.status_code)
        return None
    try:
        return r.json()["pageProps"]["pageContent"]
    except (ValueError, KeyError):
        log.warning("%s offering=%s -> no pageContent", code, offering)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--subjects", type=Path, default=SUBJECTS)
    parser.add_argument("--codes", nargs="*", default=None)
    parser.add_argument("--year", default="2026")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    subjects = pd.read_csv(args.subjects, dtype=str).fillna("")
    if args.codes:
        subjects = subjects[subjects.subject_code.isin(args.codes)]
    session = requests.Session()
    build = build_id(session, args.year, subjects.subject_code.iloc[0])
    log.info("buildId %s", build)

    rows, no_tasks, failed = [], [], []
    for i, s in enumerate(subjects.itertuples(index=False), 1):
        code = s.subject_code
        subject = {"subject_code": code, "subject_name": s.subject_name, "course": getattr(s, "courses", "")}
        url = f"{BASE}/subject/{args.year}/{code}"
        base = fetch_json(session, build, args.year, code, None)
        time.sleep(args.delay)
        if base is None:
            failed.append(code)
            continue
        offerings = [o.get("display_name") for o in (base.get("offering") or []) if o.get("display_name")]
        items: list[dict] = []
        for off in offerings[:2] or [None]:
            pc = fetch_json(session, build, args.year, code, off)
            time.sleep(args.delay)
            if pc and pc.get("selected_assessment"):
                items += pc["selected_assessment"]
        got = rows_from_items(items, subject, url)
        if not got:
            no_tasks.append(code)
        rows += got
        log.info("[%d/%d] %s %d tasks", i, len(subjects), code, len(got))

    df = pd.DataFrame(rows, columns=COLUMNS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")
    print(f"\nWrote {args.out}: {len(df)} rows, {df.subject_code.nunique()} subjects with tasks")
    if no_tasks:
        print(f"No tasks ({len(no_tasks)}): {', '.join(no_tasks)}")
    if failed:
        print(f"FAILED ({len(failed)}): {', '.join(failed)}")


if __name__ == "__main__":
    main()
